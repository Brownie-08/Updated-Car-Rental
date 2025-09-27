"""
Payment Services for Car Rental System
Handles Stripe, PayPal, and other payment integrations
"""

import stripe
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .payment_models import PaymentTransaction, PaymentMethod, PaymentReceipt
from .models import Order

logger = logging.getLogger(__name__)
User = get_user_model()

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

# Configure Paystack
try:
    from paystackapi.transaction import Transaction
    from paystackapi.verification import Verification
    import os
    # Set the Paystack secret key globally
    paystack_secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    if paystack_secret_key:
        os.environ['PAYSTACK_SECRET_KEY'] = paystack_secret_key
    paystack_available = True
except ImportError:
    paystack_available = False
    logger.warning("Paystack library not installed. Paystack payments will not be available.")


class StripePaymentService:
    """Stripe payment processing service"""
    
    @staticmethod
    def create_payment_intent(order, payment_method='stripe'):
        """Create a Stripe payment intent for an order"""
        try:
            # Get or create payment method record
            stripe_method, _ = PaymentMethod.objects.get_or_create(
                name='stripe',
                defaults={
                    'display_name': 'Credit/Debit Card',
                    'description': 'Secure payment via Stripe',
                    'processing_fee_percentage': Decimal('2.9')
                }
            )
            
            # Create payment transaction record
            payment_transaction = PaymentTransaction.objects.create(
                order=order,
                user=order.customer,
                payment_method=stripe_method,
                amount=order.total_amount,
                currency='USD',
                status='pending',
                transaction_type='payment',
                description=f'Car rental payment for {order.car_name}'
            )
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'order_id': str(order.id),
                    'transaction_id': str(payment_transaction.transaction_id),
                    'customer_email': order.customer.email if order.customer else 'guest@example.com',
                    'car_name': order.car_name,
                    'order_number': order.order_number
                },
                description=f'Car Rental - {order.car_name}'
            )
            
            # Update transaction with Stripe data
            payment_transaction.external_transaction_id = intent.id
            payment_transaction.provider_response = {
                'intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status
            }
            payment_transaction.save()
            
            return {
                'success': True,
                'payment_intent': intent,
                'transaction': payment_transaction,
                'client_secret': intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred'
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id):
        """Confirm payment and update transaction status"""
        try:
            # Retrieve payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find corresponding transaction
            transaction = PaymentTransaction.objects.get(
                external_transaction_id=payment_intent_id
            )
            
            if intent.status == 'succeeded':
                # Mark transaction as completed
                transaction.mark_as_completed()
                
                # Update order status
                order = transaction.order
                order.status = 'confirmed'
                order.save()
                
                # Generate receipt
                receipt = PaymentReceipt.objects.create(
                    transaction=transaction,
                    receipt_data={
                        'payment_method': 'Credit/Debit Card',
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'order_details': {
                            'order_number': order.order_number,
                            'car_name': order.car_name,
                            'rental_period': f"{order.date_from} to {order.date_to}",
                            'customer': order.dealer_name,
                            'total_amount': str(order.total_amount)
                        }
                    }
                )
                
                return {
                    'success': True,
                    'transaction': transaction,
                    'order': order,
                    'receipt': receipt
                }
            else:
                transaction.mark_as_failed(f"Payment failed with status: {intent.status}")
                return {
                    'success': False,
                    'error': f"Payment failed with status: {intent.status}"
                }
                
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Transaction not found for payment intent: {payment_intent_id}")
            return {
                'success': False,
                'error': 'Transaction not found'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred'
            }
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                result = StripePaymentService.confirm_payment(payment_intent['id'])
                
                if result['success']:
                    logger.info(f"Payment confirmed via webhook: {payment_intent['id']}")
                    # Send confirmation email here if needed
                else:
                    logger.error(f"Failed to confirm payment via webhook: {result['error']}")
                    
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                try:
                    transaction = PaymentTransaction.objects.get(
                        external_transaction_id=payment_intent['id']
                    )
                    transaction.mark_as_failed('Payment failed via webhook')
                    logger.info(f"Payment marked as failed via webhook: {payment_intent['id']}")
                except PaymentTransaction.DoesNotExist:
                    logger.error(f"Transaction not found for failed payment: {payment_intent['id']}")
            
            return {'success': True}
            
        except ValueError as e:
            logger.error(f"Invalid payload in webhook: {str(e)}")
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in webhook: {str(e)}")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Unexpected error handling webhook: {str(e)}")
            return {'success': False, 'error': 'Unexpected error'}


class PayLaterService:
    """Service for handling pay-later orders"""
    
    @staticmethod
    def create_pay_later_order(order):
        """Create a pay-later payment record"""
        try:
            # Get or create pay-later payment method
            pay_later_method, _ = PaymentMethod.objects.get_or_create(
                name='pay_later',
                defaults={
                    'display_name': 'Pay at Pickup/Delivery',
                    'description': 'Cash or card payment at vehicle pickup',
                    'processing_fee_percentage': Decimal('0.0')
                }
            )
            
            # Create payment transaction record
            payment_transaction = PaymentTransaction.objects.create(
                order=order,
                user=order.customer,
                payment_method=pay_later_method,
                amount=order.total_amount,
                currency='USD',
                status='pending',
                transaction_type='payment',
                description=f'Pay-later booking for {order.car_name}',
                notes='Payment to be collected at pickup/delivery'
            )
            
            # Update order status
            order.status = 'pending'
            order.save()
            
            return {
                'success': True,
                'transaction': payment_transaction,
                'order': order
            }
            
        except Exception as e:
            logger.error(f"Error creating pay-later order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class PaystackPaymentService:
    """Paystack payment processing service with currency conversion"""
    
    @staticmethod
    def initialize_transaction(order, callback_url):
        """Initialize a Paystack transaction for an order with proper currency conversion and unique references"""
        from django.db import transaction as db_transaction
        import uuid
        import time
        
        try:
            if not paystack_available:
                logger.error("Paystack library not available. Install paystackapi package.")
                return {
                    'success': False,
                    'error': 'Paystack payment service is not available. Please contact support.'
                }
            
            # Check if Paystack keys are configured
            paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
            paystack_public = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
            
            if not paystack_secret or not paystack_public:
                logger.error("Paystack API keys not configured")
                return {
                    'success': False,
                    'error': 'Payment service configuration error. Please contact support.'
                }
            
            # Validate API keys format
            if not paystack_secret.startswith(('sk_test_', 'sk_live_')):
                logger.error(f"Invalid Paystack secret key format: {paystack_secret[:10]}...")
                return {
                    'success': False,
                    'error': 'Invalid payment configuration. Please contact support.'
                }
            
            if not paystack_public.startswith(('pk_test_', 'pk_live_')):
                logger.error(f"Invalid Paystack public key format: {paystack_public[:10]}...")
                return {
                    'success': False,
                    'error': 'Invalid payment configuration. Please contact support.'
                }
            
            # Check for existing pending payment for this order
            existing_transaction = PaymentTransaction.objects.filter(
                order=order,
                payment_method__name='paystack',
                status='pending'
            ).first()
            
            if existing_transaction:
                # Check if the existing transaction has valid Paystack data
                if (existing_transaction.external_transaction_id and 
                    existing_transaction.provider_response and 
                    'authorization_url' in existing_transaction.provider_response):
                    
                    logger.info(f"Reusing existing transaction {existing_transaction.transaction_id}")
                    return {
                        'success': True,
                        'transaction': existing_transaction,
                        'authorization_url': existing_transaction.provider_response['authorization_url'],
                        'access_code': existing_transaction.provider_response.get('access_code', ''),
                        'reference': existing_transaction.external_transaction_id,
                        'currency_info': existing_transaction.notes  # Contains conversion info
                    }
            
            # Import currency conversion utilities
            from .currency_utils import convert_usd_to_kobo, format_currency_display
            
            # Convert USD amount to NGN and then to kobo server-side
            usd_amount = order.total_amount
            currency_info = format_currency_display(usd_amount)
            amount_in_kobo = convert_usd_to_kobo(usd_amount)
            
            logger.info(f"Payment conversion: {currency_info['usd_amount']} → {currency_info['ngn_amount']} → {amount_in_kobo} kobo")
            
            # Use database transaction to ensure atomicity
            with db_transaction.atomic():
                # Get or create payment method record
                paystack_method, _ = PaymentMethod.objects.get_or_create(
                    name='paystack',
                    defaults={
                        'display_name': 'Card Payment (Paystack)',
                        'description': 'Secure payment via Paystack',
                        'processing_fee_percentage': Decimal('1.5')
                    }
                )
                
                # Generate unique transaction reference
                unique_reference = f"PAY-{order.id}-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}"
                
                # Create payment transaction record with NGN amount
                payment_transaction = PaymentTransaction.objects.create(
                    order=order,
                    user=order.customer,
                    payment_method=paystack_method,
                    amount=Decimal(str(currency_info['ngn_numeric'])),  # Store NGN amount
                    currency='NGN',  # Paystack uses NGN
                    status='pending',
                    transaction_type='payment',
                    description=f'Car rental payment for {order.car_name}',
                    notes=f"Original: {currency_info['usd_amount']}, Rate: {currency_info['exchange_rate']}, NGN: {currency_info['ngn_amount']}",
                    external_transaction_id=unique_reference  # Pre-set the reference
                )
                
                # Initialize transaction with Paystack using the unique reference
                max_retries = 3
                response = None
                
                for attempt in range(max_retries):
                    try:
                        response = Transaction.initialize(
                            email=order.customer.email if order.customer else 'guest@example.com',
                            amount=amount_in_kobo,  # Amount in kobo
                            callback_url=callback_url,
                            reference=unique_reference,  # Use our unique reference
                            currency='NGN',  # Explicitly set currency
                            metadata={
                                'order_id': str(order.id),
                                'transaction_id': str(payment_transaction.transaction_id),
                                'customer_name': order.dealer_name or 'Guest Customer',
                                'car_name': order.car_name,
                                'order_number': order.order_number,
                                'original_usd_amount': str(usd_amount),
                                'ngn_amount': str(currency_info['ngn_numeric']),
                                'exchange_rate': currency_info['exchange_rate'],
                                'kobo_amount': str(amount_in_kobo)
                            }
                        )
                        
                        # If successful, break out of retry loop
                        if response and response.get('status'):
                            break
                            
                        # Check for duplicate reference error
                        if (response and not response.get('status') and 
                            'duplicate' in response.get('message', '').lower()):
                            
                            # Generate new reference and update transaction
                            unique_reference = f"PAY-{order.id}-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}"
                            payment_transaction.external_transaction_id = unique_reference
                            payment_transaction.save()
                            
                            logger.warning(f"Duplicate reference detected, retrying with new reference: {unique_reference}")
                            continue
                            
                    except Exception as api_error:
                        logger.error(f"Paystack API error (attempt {attempt + 1}): {str(api_error)}")
                        if attempt == max_retries - 1:
                            raise api_error
                        
                        # Generate new reference for retry
                        unique_reference = f"PAY-{order.id}-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}"
                        payment_transaction.external_transaction_id = unique_reference
                        payment_transaction.save()
                        continue
                
                if response['status']:
                    # Update transaction with Paystack response data
                    payment_transaction.provider_response = response['data']
                    payment_transaction.save()
                    
                    return {
                        'success': True,
                        'transaction': payment_transaction,
                        'authorization_url': response['data']['authorization_url'],
                        'access_code': response['data']['access_code'],
                        'reference': unique_reference,
                        'currency_info': currency_info,  # Pass currency info to template
                        'amount_in_kobo': amount_in_kobo
                    }
                else:
                    # Paystack initialization failed, clean up transaction
                    payment_transaction.mark_as_failed(f"Paystack initialization failed: {response.get('message', 'Unknown error')}")
                    logger.error(f"Paystack initialization failed: {response}")
                    return {
                        'success': False,
                        'error': response.get('message', 'Transaction initialization failed')
                    }
                
        except Exception as e:
            logger.error(f"Error initializing Paystack transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def verify_transaction(reference):
        """Verify Paystack transaction and update status"""
        try:
            if not paystack_available:
                raise Exception("Paystack library not available")
            
            # Verify transaction with Paystack
            response = Transaction.verify(reference=reference)
            
            if not response['status']:
                return {
                    'success': False,
                    'error': response.get('message', 'Transaction verification failed')
                }
            
            # Find corresponding transaction
            try:
                transaction = PaymentTransaction.objects.get(
                    external_transaction_id=reference
                )
            except PaymentTransaction.DoesNotExist:
                logger.error(f"Transaction not found for reference: {reference}")
                return {
                    'success': False,
                    'error': 'Transaction not found'
                }
            
            transaction_data = response['data']
            
            if transaction_data['status'] == 'success':
                # Mark transaction as completed
                transaction.mark_as_completed()
                transaction.provider_response = transaction_data
                transaction.save()
                
                # Update order status and confirm booking
                order = transaction.order
                order.status = 'confirmed'
                order.save()
                
                # Send booking confirmation emails after successful payment
                try:
                    from .email_utils import send_booking_confirmation_email, send_admin_notification_email
                    
                    # Try to find associated car for email template
                    selected_car = None
                    if order.car_name:
                        from .models import Car
                        try:
                            selected_car = Car.objects.get(car_name=order.car_name)
                        except Car.DoesNotExist:
                            pass
                    
                    # Send customer confirmation email
                    send_booking_confirmation_email(order, selected_car)
                    
                    # Send admin notification email
                    send_admin_notification_email(order, selected_car)
                    
                    logger.info(f"Booking confirmation emails sent for order {order.order_number}")
                except Exception as email_error:
                    logger.error(f"Failed to send booking confirmation emails for order {order.order_number}: {str(email_error)}")
                
                # Generate receipt
                from .payment_models import PaymentReceipt
                receipt = PaymentReceipt.objects.create(
                    transaction=transaction,
                    receipt_data={
                        'payment_method': 'Card Payment (Paystack)',
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'reference': reference,
                        'order_details': {
                            'order_number': order.order_number,
                            'car_name': order.car_name,
                            'rental_period': f"{order.date_from} to {order.date_to}",
                            'customer': order.dealer_name,
                            'total_amount': str(order.total_amount)
                        }
                    }
                )
                
                return {
                    'success': True,
                    'transaction': transaction,
                    'order': order,
                    'receipt': receipt,
                    'transaction_data': transaction_data
                }
            else:
                transaction.mark_as_failed(f"Payment failed with status: {transaction_data['status']}")
                return {
                    'success': False,
                    'error': f"Payment failed with status: {transaction_data['status']}"
                }
                
        except Exception as e:
            logger.error(f"Error verifying Paystack transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def handle_webhook(payload, signature):
        """Handle Paystack webhook events"""
        try:
            import hashlib
            import hmac
            
            # Verify webhook signature
            secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
            computed_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            if computed_signature != signature:
                logger.error("Invalid Paystack webhook signature")
                return {'success': False, 'error': 'Invalid signature'}
            
            import json
            event = json.loads(payload)
            
            if event['event'] == 'charge.success':
                reference = event['data']['reference']
                result = PaystackPaymentService.verify_transaction(reference)
                
                if result['success']:
                    logger.info(f"Payment confirmed via webhook: {reference}")
                else:
                    logger.error(f"Failed to confirm payment via webhook: {result['error']}")
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error handling Paystack webhook: {str(e)}")
            return {'success': False, 'error': str(e)}


class PaymentServiceFactory:
    """Factory class to get appropriate payment service"""
    
    @staticmethod
    def get_service(payment_method):
        """Get payment service based on method"""
        if payment_method == 'stripe':
            return StripePaymentService()
        elif payment_method == 'paystack':
            return PaystackPaymentService()
        elif payment_method == 'pay_later':
            return PayLaterService()
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")
