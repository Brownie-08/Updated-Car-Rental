"""
Payment URLs for Car Rental System
"""
from django.urls import path
from . import payment_views, api_views

urlpatterns = [
    # Payment initiation
    path('initiate/<int:order_id>/', payment_views.initiate_payment, name='initiate_payment'),
    
    # Stripe payment endpoints
    path('stripe/confirm/', payment_views.confirm_stripe_payment, name='confirm_stripe_payment'),
    path('stripe/webhook/', payment_views.stripe_webhook, name='stripe_webhook'),
    
    # Paystack payment endpoints
    path('paystack/callback/<int:order_id>/', payment_views.paystack_callback, name='paystack_callback'),
    path('paystack/webhook/', payment_views.paystack_webhook, name='paystack_webhook'),
    
    # Payment result pages
    path('success/<int:order_id>/', payment_views.payment_success, name='payment_success'),
    path('cancelled/<int:order_id>/', payment_views.payment_cancelled, name='payment_cancelled'),
    
    # Payment management
    path('history/', payment_views.payment_history, name='payment_history'),
    path('receipt/<str:transaction_id>/download/', payment_views.download_receipt, name='download_receipt'),
    
    # API endpoints for AJAX requests
    path('api/currency/<int:order_id>/', api_views.get_currency_conversion, name='api_currency_conversion'),
    path('api/paystack/initialize/<int:order_id>/', api_views.initialize_paystack_payment, name='api_paystack_initialize'),
    path('api/paystack/verify/<str:reference>/', api_views.verify_paystack_payment, name='api_paystack_verify'),
    path('api/order/status/<int:order_id>/', api_views.get_order_status, name='api_order_status'),
]
