"""
Payment Services for Car Rental System
Handles Stripe, PayPal, and other payment integrations
"""

import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .payment_models import PaymentTransaction, PaymentMethod, PaymentReceipt
from .models import Order

logger = logging.getLogger(__name__)
User = get_user_model()

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


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


class PaymentServiceFactory:
    """Factory class to get appropriate payment service"""
    
    @staticmethod
    def get_service(payment_method):
        """Get payment service based on method"""
        if payment_method == 'stripe':
            return StripePaymentService()
        elif payment_method == 'pay_later':
            return PayLaterService()
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")
