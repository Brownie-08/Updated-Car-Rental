"""
API Views for Car Rental System
Provides REST API endpoints for frontend JavaScript
"""

import json
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from .models import Order
from .currency_utils import convert_usd_to_kobo, format_currency_display
from .payment_services import PaystackPaymentService

logger = logging.getLogger(__name__)


@login_required
@require_GET
def get_currency_conversion(request, order_id):
    """
    Get currency conversion for an order
    Returns USD to NGN conversion with exact amounts
    """
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        
        # Get currency conversion info
        usd_amount = order.total_amount
        currency_info = format_currency_display(usd_amount)
        kobo_amount = convert_usd_to_kobo(usd_amount)
        
        logger.info(f"Currency conversion for order {order_id}: {currency_info['usd_amount']} → {currency_info['ngn_amount']}")
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'usd_amount': str(usd_amount),
            'usd_amount_formatted': currency_info['usd_amount'],
            'ngn_amount': currency_info['ngn_numeric'],
            'ngn_amount_formatted': currency_info['ngn_amount'],
            'kobo_amount': kobo_amount,
            'exchange_rate': currency_info['exchange_rate'],
            'conversion_note': f"Converted at rate: {currency_info['exchange_rate']}"
        })
        
    except Exception as e:
        logger.error(f"Error getting currency conversion for order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get currency conversion'
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def initialize_paystack_payment(request, order_id):
    """
    Initialize Paystack payment with proper currency conversion
    Returns payment initialization data for frontend
    """
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        
        # Build callback URL
        callback_url = request.build_absolute_uri(
            f'/car/payment/paystack/callback/{order_id}/'
        )
        
        # Initialize payment
        result = PaystackPaymentService.initialize_transaction(order, callback_url)
        
        if result['success']:
            logger.info(f"Paystack payment initialized for order {order_id}: {result['reference']}")
            
            return JsonResponse({
                'success': True,
                'order_id': order_id,
                'reference': result['reference'],
                'authorization_url': result['authorization_url'],
                'access_code': result['access_code'],
                'currency_info': result.get('currency_info', {}),
                'amount_in_kobo': result.get('amount_in_kobo', 0),
                'transaction_id': str(result['transaction'].transaction_id)
            })
        else:
            logger.error(f"Paystack payment initialization failed for order {order_id}: {result['error']}")
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error initializing Paystack payment for order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to initialize payment'
        }, status=500)


@login_required
@require_GET
def verify_paystack_payment(request, reference):
    """
    Verify Paystack payment and return status
    """
    try:
        # Verify transaction with Paystack
        result = PaystackPaymentService.verify_transaction(reference)
        
        if result['success']:
            logger.info(f"Paystack payment verified successfully: {reference}")
            
            return JsonResponse({
                'success': True,
                'reference': reference,
                'order_id': result['order'].id,
                'order_number': result['order'].order_number,
                'transaction_id': str(result['transaction'].transaction_id),
                'amount': str(result['transaction'].amount),
                'currency': result['transaction'].currency,
                'status': 'completed'
            })
        else:
            logger.error(f"Paystack payment verification failed: {reference} - {result['error']}")
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error verifying Paystack payment {reference}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Payment verification failed'
        }, status=500)


@login_required
@require_GET  
def get_order_status(request, order_id):
    """
    Get current order status
    """
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'order_number': order.order_number,
            'status': order.status,
            'car_name': order.car_name,
            'total_amount': str(order.total_amount),
            'date_from': order.date_from.isoformat() if order.date_from else None,
            'date_to': order.date_to.isoformat() if order.date_to else None
        })
        
    except Exception as e:
        logger.error(f"Error getting order status {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get order status'
        }, status=500)