"""
Payment Models for Car Rental System
Handles all payment-related data structures
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """Payment methods available in the system"""
    PAYMENT_TYPES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('pay_later', 'Pay Later'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    name = models.CharField(max_length=50, choices=PAYMENT_TYPES, unique=True)
    is_active = models.BooleanField(default=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
    
    def __str__(self):
        return self.display_name


class PaymentTransaction(models.Model):
    """Individual payment transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('chargeback', 'Chargeback'),
        ('fee', 'Processing Fee'),
        ('deposit', 'Security Deposit'),
        ('deposit_return', 'Deposit Return'),
    ]
    
    # Primary fields
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payment_transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='payment')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # External payment provider data
    external_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Security and tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['external_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type.title()} - {self.amount} {self.currency} ({self.status})"
    
    def mark_as_completed(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, error_message=None):
        """Mark transaction as failed"""
        self.status = 'failed'
        if error_message:
            self.notes = f"{self.notes}\nError: {error_message}" if self.notes else f"Error: {error_message}"
        self.save(update_fields=['status', 'notes'])
    
    def get_refundable_amount(self):
        """Calculate refundable amount"""
        if self.status != 'completed' or self.transaction_type != 'payment':
            return Decimal('0.00')
        
        refunded_amount = PaymentTransaction.objects.filter(
            order=self.order,
            transaction_type='refund',
            status='completed'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return max(Decimal('0.00'), self.amount - refunded_amount)


class PaymentReceipt(models.Model):
    """Payment receipts and invoices"""
    receipt_number = models.CharField(max_length=50, unique=True)
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='receipt')
    
    # Receipt data
    receipt_data = models.JSONField(default=dict)
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    
    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Receipt"
        verbose_name_plural = "Payment Receipts"
    
    def __str__(self):
        return f"Receipt {self.receipt_number}"
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        if not self.receipt_number:
            today = timezone.now().strftime('%Y%m%d')
            count = PaymentReceipt.objects.filter(
                created_at__date=timezone.now().date()
            ).count() + 1
            self.receipt_number = f"RCP-{today}-{count:04d}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.generate_receipt_number()
        super().save(*args, **kwargs)


class RefundRequest(models.Model):
    """Refund request management"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    REFUND_REASONS = [
        ('cancellation', 'Booking Cancellation'),
        ('no_show', 'Customer No-Show'),
        ('vehicle_issue', 'Vehicle Issue'),
        ('service_issue', 'Service Issue'),
        ('overpayment', 'Overpayment'),
        ('duplicate', 'Duplicate Payment'),
        ('other', 'Other'),
    ]
    
    # Primary fields
    refund_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    original_transaction = models.ForeignKey(
        PaymentTransaction, 
        on_delete=models.CASCADE,
        related_name='refund_requests'
    )
    refund_transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_request'
    )
    
    # Refund details
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=20, choices=REFUND_REASONS)
    description = models.TextField()
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # User tracking
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_refunds'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Refund Request"
        verbose_name_plural = "Refund Requests"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['requested_by', 'status']),
        ]
    
    def __str__(self):
        return f"Refund Request {self.refund_id} - ${self.requested_amount}"
    
    def approve(self, approved_by, approved_amount=None):
        """Approve refund request"""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_amount = approved_amount or self.requested_amount
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_amount', 'approved_at'])
    
    def reject(self, rejected_by, reason):
        """Reject refund request"""
        self.status = 'rejected'
        self.approved_by = rejected_by
        self.admin_notes = reason
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'admin_notes', 'approved_at'])


class PaymentWebhook(models.Model):
    """Webhook events from payment providers"""
    webhook_id = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    
    # Webhook data
    raw_data = models.JSONField()
    processed = models.BooleanField(default=False)
    
    # Processing tracking
    processing_attempts = models.IntegerField(default=0)
    last_processing_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Webhook"
        verbose_name_plural = "Payment Webhooks"
        indexes = [
            models.Index(fields=['provider', 'processed']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type}"
