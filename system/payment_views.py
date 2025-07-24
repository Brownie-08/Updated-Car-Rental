"""
Payment Views for Car Rental System
Handles payment processing, confirmations, and webhooks
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View

from .models import Order
from .payment_models import PaymentTransaction, PaymentReceipt
from .payment_services import StripePaymentService, PayLaterService
from .email_utils import send_payment_confirmation_email

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, order_id):
    """Initiate payment process based on selected method"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    payment_method = request.POST.get('payment_method', 'stripe')
    
    try:
        if payment_method == 'stripe':
            # Process Stripe payment
            result = StripePaymentService.create_payment_intent(order)
            
            if result['success']:
                # Redirect to Stripe payment page
                return render(request, 'system/payment/stripe_checkout.html', {
                    'order': order,
                    'client_secret': result['client_secret'],
                    'transaction': result['transaction'],
                    'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
                })
            else:
                messages.error(request, f"Payment initialization failed: {result['error']}")
                return redirect('system:order_detail', id=order_id)
        
        elif payment_method == 'pay_later':
            # Process pay-later option
            result = PayLaterService.create_pay_later_order(order)
            
            if result['success']:
                messages.success(request, 
                    f'🎉 Booking confirmed! Order #{order.order_number} has been created. '
                    f'You can pay at pickup/delivery. A confirmation email has been sent.')
                
                # Send confirmation email
                try:
                    send_payment_confirmation_email(order, result['transaction'])
                except Exception as e:
                    logger.error(f"Failed to send confirmation email: {str(e)}")
                
                return redirect('system:order_detail', id=order_id)
            else:
                messages.error(request, f"Booking failed: {result['error']}")
                return redirect('system:order_detail', id=order_id)
        
        else:
            messages.error(request, f"Payment method '{payment_method}' is not yet supported.")
            return redirect('system:order_detail', id=order_id)
    
    except Exception as e:
        logger.error(f"Error initiating payment for order {order_id}: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('system:order_detail', id=order_id)


@login_required
@require_POST
def confirm_stripe_payment(request):
    """Confirm Stripe payment after successful client-side processing"""
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({'success': False, 'error': 'Missing payment intent ID'})
        
        result = StripePaymentService.confirm_payment(payment_intent_id)
        
        if result['success']:
            # Send confirmation email
            try:
                send_payment_confirmation_email(result['order'], result['transaction'])
            except Exception as e:
                logger.error(f"Failed to send payment confirmation email: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'order_id': result['order'].id,
                'order_number': result['order'].order_number,
                'redirect_url': reverse('system:payment_success', args=[result['order'].id])
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Error confirming Stripe payment: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred'})


@login_required
@require_GET
def payment_success(request, order_id):
    """Payment success page"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    # Get the most recent successful payment transaction for this order
    transaction = PaymentTransaction.objects.filter(
        order=order,
        status='completed'
    ).first()
    
    # Get receipt if available
    receipt = None
    if transaction:
        receipt = getattr(transaction, 'receipt', None)
    
    context = {
        'order': order,
        'transaction': transaction,
        'receipt': receipt,
        'title': 'Payment Successful'
    }
    
    return render(request, 'system/payment/payment_success.html', context)


@login_required
@require_GET
def payment_cancelled(request, order_id):
    """Payment cancelled page"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    # Mark any pending transactions as cancelled
    PaymentTransaction.objects.filter(
        order=order,
        status='pending'
    ).update(status='cancelled')
    
    context = {
        'order': order,
        'title': 'Payment Cancelled'
    }
    
    return render(request, 'system/payment/payment_cancelled.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    result = StripePaymentService.handle_webhook(payload, sig_header)
    
    if result['success']:
        return HttpResponse(status=200)
    else:
        logger.error(f"Webhook processing failed: {result.get('error', 'Unknown error')}")
        return HttpResponse(status=400)


@login_required
def payment_history(request):
    """User's payment history"""
    transactions = PaymentTransaction.objects.filter(
        user=request.user
    ).select_related('order', 'payment_method').order_by('-created_at')
    
    context = {
        'transactions': transactions,
        'title': 'Payment History'
    }
    
    return render(request, 'system/payment/payment_history.html', context)


@login_required
def download_receipt(request, transaction_id):
    """Download payment receipt as PDF"""
    transaction = get_object_or_404(
        PaymentTransaction,
        transaction_id=transaction_id,
        user=request.user,
        status='completed'
    )
    
    try:
        receipt = transaction.receipt
        
        # Generate PDF receipt
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Receipt header
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width/2, height - 50, "Brownie Car Rental - Payment Receipt")
        
        # Receipt details
        y = height - 100
        p.setFont("Helvetica", 12)
        
        details = [
            f"Receipt Number: {receipt.receipt_number}",
            f"Order Number: {transaction.order.order_number}",
            f"Car: {transaction.order.car_name}",
            f"Customer: {transaction.order.dealer_name}",
            f"Amount: ${transaction.amount} {transaction.currency}",
            f"Payment Method: {transaction.payment_method.display_name}",
            f"Transaction Date: {transaction.processed_at.strftime('%B %d, %Y at %I:%M %p')}",
            f"Status: {transaction.get_status_display()}"
        ]
        
        for detail in details:
            p.drawString(50, y, detail)
            y -= 25
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{receipt.receipt_number}.pdf"'
        return response
        
    except Exception as e:
        logger.error(f"Error generating receipt PDF: {str(e)}")
        messages.error(request, "Error generating receipt. Please try again.")
        return redirect('system:payment_history')


class PaymentDashboardView(View):
    """Payment management dashboard for admin users"""
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Access denied.")
            return redirect('system:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        # Payment statistics
        today = datetime.now().date()
        this_month = today.replace(day=1)
        
        stats = {
            'total_transactions': PaymentTransaction.objects.count(),
            'completed_transactions': PaymentTransaction.objects.filter(status='completed').count(),
            'pending_transactions': PaymentTransaction.objects.filter(status='pending').count(),
            'failed_transactions': PaymentTransaction.objects.filter(status='failed').count(),
            'total_revenue': PaymentTransaction.objects.filter(
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'monthly_revenue': PaymentTransaction.objects.filter(
                status='completed',
                processed_at__gte=this_month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        }
        
        # Recent transactions
        recent_transactions = PaymentTransaction.objects.select_related(
            'order', 'user', 'payment_method'
        ).order_by('-created_at')[:10]
        
        context = {
            'stats': stats,
            'recent_transactions': recent_transactions,
            'title': 'Payment Dashboard'
        }
        
        return render(request, 'system/payment/admin_dashboard.html', context)
