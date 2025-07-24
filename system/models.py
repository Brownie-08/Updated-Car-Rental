from django.db import models
from django.conf import settings
from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


# Function to define the upload location for car images
def uploaded_location(instance, filename):
    return ("%s/%s") % (instance.car_name, filename)

# Model for Car
class Car(models.Model):
    image = models.ImageField(upload_to=uploaded_location, null=True, blank=True, width_field="width_field", height_field="height_field")
    height_field = models.IntegerField(default=0)
    width_field = models.IntegerField(default=0)
    car_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    num_of_seats = models.IntegerField()
    cost_par_day = models.DecimalField(max_digits=10, decimal_places=2)  # Changed to DecimalField
    content = models.TextField()
    like = models.IntegerField(default=0)

    def __str__(self):
        return self.car_name

    def get_absolute_url(self):
        return "/car/%s/" % (self.id)

# Model for Order
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    car_name = models.CharField(max_length=255)
    dealer_name = models.CharField(max_length=255)
    cell_no = models.CharField(max_length=15)
    address = models.TextField()
    date_from = models.DateField(default=timezone.now)
    date_to = models.DateField(default=timezone.now)
    
    # Additional location and date fields
    pick_up_location = models.CharField(max_length=255, null=True, blank=True)
    drop_off_location = models.CharField(max_length=255, null=True, blank=True)
    pick_up_date = models.DateField(null=True, blank=True)
    drop_off_date = models.DateField(null=True, blank=True)
    
    # Billing fields
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rental_days = models.IntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # 10% tax
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Order tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.order_number} - {self.car_name}"

    def get_absolute_url(self):
        return "/car/detail/%s/" % (self.id)

    def calculate_billing(self):
        """Calculate all billing amounts"""
        from decimal import Decimal
        
        duration = (self.date_to - self.date_from).days + 1
        self.rental_days = duration
        self.subtotal = Decimal(str(self.daily_rate)) * Decimal(str(duration))
        self.tax_amount = (self.subtotal * Decimal(str(self.tax_rate))) / Decimal('100')
        self.total_amount = self.subtotal + self.tax_amount
        
    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.order_number:
            import uuid
            self.order_number = f"BR-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate billing before saving
        self.calculate_billing()
        
        super().save(*args, **kwargs)
    
    def get_rental_duration_display(self):
        """Return formatted rental duration"""
        return f"{self.rental_days} day{'s' if self.rental_days > 1 else ''}"
    
    def get_status_display_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'completed': 'info'
        }
        return status_classes.get(self.status, 'secondary')

    def calculate_total_cost(self, cost_par_day):
        """Legacy method for backwards compatibility"""
        duration = (self.date_to - self.date_from).days + 1
        return cost_par_day * duration

# Model for Private Messages
class PrivateMsg(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]
    
    # Original message details
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Message management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    
    # Response details
    response_message = models.TextField(blank=True, null=True)
    response_sent_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='message_responses')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Private Message"
        verbose_name_plural = "Private Messages"
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['email', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.name} - {self.email} ({self.get_status_display()})"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.status = 'read'
            self.save(update_fields=['is_read', 'status'])
    
    def mark_as_replied(self, admin_user):
        """Mark message as replied"""
        self.status = 'replied'
        self.responded_by = admin_user
        self.response_sent_at = timezone.now()
        self.save(update_fields=['status', 'responded_by', 'response_sent_at'])
    
    def get_priority_class(self):
        """Return CSS class for priority badge"""
        priority_classes = {
            'low': 'default',
            'normal': 'info',
            'high': 'warning',
            'urgent': 'danger'
        }
        return priority_classes.get(self.priority, 'default')
    
    def get_status_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'new': 'primary',
            'read': 'info',
            'replied': 'success',
            'closed': 'default'
        }
        return status_classes.get(self.status, 'default')


class EmailLog(models.Model):
    """Model to track email sending history"""
    
    EMAIL_TYPES = [
        ('booking_confirmation', 'Booking Confirmation'),
        ('booking_status_update', 'Booking Status Update'),
        ('admin_notification', 'Admin Notification'),
        ('contact_form', 'Contact Form'),
        ('password_reset', 'Password Reset'),
        ('verification', 'Email Verification'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed to Send'),
        ('pending', 'Pending'),
    ]
    
    recipient_email = models.EmailField()
    sender_email = models.EmailField()
    subject = models.CharField(max_length=255)
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Email details
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['recipient_email', 'email_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} - {self.status}"
    
    def mark_as_sent(self):
        """Mark email as successfully sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message):
        """Mark email as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def increment_attempts(self):
        """Increment the number of sending attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])


# Chat System Models
class ChatRoom(models.Model):
    """Model to represent chat rooms between users and support agents"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated to Agent'),
        ('bot_only', 'Bot Only'),
        ('pending_escalation', 'Pending Escalation'),
    ]
    
    room_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms', null=True, blank=True)
    assigned_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_rooms')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_rooms')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='bot_only')
    is_bot_handled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Optional fields for tracking
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Chat Room {self.room_id} - {self.user.username}"
    
    def escalate_to_agent(self, agent=None):
        """Escalate chat room from bot to human agent"""
        self.is_bot_handled = False
        self.status = 'escalated'
        if agent:
            self.agent = agent
            self.status = 'active'
        self.save(update_fields=['is_bot_handled', 'status', 'agent'])
    
    def close_room(self):
        """Close the chat room"""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])
    
    def get_latest_messages(self, limit=50):
        """Get latest messages in the room"""
        return self.messages.order_by('-created_at')[:limit]


class ChatMessage(models.Model):
    """Model to store chat messages"""
    
    SENDER_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text')  # text, image, file, system
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Optional fields for rich content
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional data
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['sender_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender_type} in {self.room.room_id}: {self.content[:50]}..."
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])


class ChatBotResponse(models.Model):
    """Model to store predefined bot responses"""
    
    INTENT_CHOICES = [
        ('greeting', 'Greeting'),
        ('booking_inquiry', 'Booking Inquiry'),
        ('pricing', 'Pricing'),
        ('availability', 'Availability'),
        ('contact', 'Contact Information'),
        ('support', 'Support Request'),
        ('escalation', 'Escalation Request'),
        ('goodbye', 'Goodbye'),
        ('default', 'Default Response'),
    ]
    
    intent = models.CharField(max_length=30, choices=INTENT_CHOICES)
    keywords = models.TextField(help_text="Comma-separated keywords that trigger this response")
    response_text = models.TextField()
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)  # Higher priority responses are checked first
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'intent']
        verbose_name = 'Bot Response'
        verbose_name_plural = 'Bot Responses'
    
    def __str__(self):
        return f"{self.get_intent_display()}: {self.response_text[:50]}..."
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        return [kw.strip().lower() for kw in self.keywords.split(',') if kw.strip()]
