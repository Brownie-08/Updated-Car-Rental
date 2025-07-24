from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Make email unique
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expires = models.DateTimeField(blank=True, null=True)
    reset_password_token = models.UUIDField(default=uuid.uuid4, editable=False)
    reset_password_expires = models.DateTimeField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    groups = models.ManyToManyField(Group, related_name='customuser_set', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='customuser_set', blank=True)
    
    USERNAME_FIELD = 'email'  # Use email as the unique identifier
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def generate_verification_code(self):
        from django.utils.crypto import get_random_string
        self.verification_code = get_random_string(6, allowed_chars='0123456789')
        self.verification_code_expires = timezone.now() + timedelta(hours=24)
        self.save()
        return self.verification_code
    
    def generate_reset_token(self):
        self.reset_password_token = uuid.uuid4()
        self.reset_password_expires = timezone.now() + timedelta(hours=2)
        self.save()
        return self.reset_password_token
    
    def is_verification_code_valid(self, code):
        if not self.verification_code or not self.verification_code_expires:
            return False
        if timezone.now() > self.verification_code_expires:
            return False
        return self.verification_code == code
    
    def is_reset_token_valid(self, token):
        if not self.reset_password_expires:
            return False
        if timezone.now() > self.reset_password_expires:
            return False
        return str(self.reset_password_token) == str(token)
