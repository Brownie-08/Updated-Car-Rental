# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from .forms import (
    UserLoginForm, 
    UserRegisterForm, 
    EmailVerificationForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
    ResendVerificationForm
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def send_verification_email(user):
    """Send email verification code to user"""
    try:
        # Generate verification code
        code = user.generate_verification_code()
        
        # Create email content
        subject = 'Verify Your Email - Brownie Car Rental'
        html_message = render_to_string('emails/verification_email.html', {
            'user': user,
            'verification_code': code,
            'site_name': 'Brownie Car Rental',
            'verification_url': f"{settings.SITE_URL}{reverse('verify_email')}" if hasattr(settings, 'SITE_URL') else reverse('verify_email')
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user):
    """Send password reset email to user"""
    try:
        # Generate reset token
        token = user.generate_reset_token()
        
        # Create email content
        subject = 'Reset Your Password - Brownie Car Rental'
        reset_url = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'token': token})}" if hasattr(settings, 'SITE_URL') else reverse('password_reset_confirm', kwargs={'token': token})
        
        html_message = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'Brownie Car Rental',
            'expiry_hours': 2
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def register_view(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        try:
            user = form.save()
            # Send verification email
            if send_verification_email(user):
                messages.success(request, 
                    f'Registration successful! Please check your email ({user.email}) for verification instructions.')
                return redirect('verify_email_pending')
            else:
                messages.error(request, 
                    'Registration successful, but we couldn\'t send the verification email. Please try again.')
                return redirect('resend_verification')
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, 'An error occurred during registration. Please try again.')
    
    context = {
        "title": "Create Your Account",
        "form": form,
    }
    return render(request, "auth/register.html", context)


def verify_email_view(request):
    """Email verification view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    form = EmailVerificationForm(request.POST or None)
    if form.is_valid():
        code = form.cleaned_data.get('code')
        try:
            user = User.objects.get(verification_code=code)
            if user.is_verification_code_valid(code):
                user.email_verified = True
                user.is_active = True
                user.verification_code = ''
                user.verification_code_expires = None
                user.save()
                
                # Auto-login the user
                login(request, user)
                messages.success(request, 'Email verified successfully! Welcome to Brownie Car Rental.')
                
                if user.is_superuser:
                    return redirect('base_dash')
                else:
                    return redirect('system:newcar')
            else:
                messages.error(request, 'Verification code has expired. Please request a new one.')
                return redirect('resend_verification')
        except User.DoesNotExist:
            form.add_error('code', 'Invalid verification code. Please try again.')
    
    context = {
        "title": "Verify Your Email",
        "form": form,
    }
    return render(request, "auth/verify_email.html", context)


def verify_email_pending_view(request):
    """Show pending email verification page"""
    return render(request, "auth/verify_email_pending.html", {
        "title": "Check Your Email"
    })


def resend_verification_view(request):
    """Resend verification email"""
    form = ResendVerificationForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            if send_verification_email(user):
                messages.success(request, 
                    f'Verification email resent to {email}. Please check your inbox.')
                return redirect('verify_email_pending')
            else:
                messages.error(request, 'Failed to send verification email. Please try again later.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    context = {
        "title": "Resend Verification Email",
        "form": form,
    }
    return render(request, "auth/resend_verification.html", context)


def login_view(request):
    """Enhanced login view with email authentication"""
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        remember_me = form.cleaned_data.get("remember_me")
        
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            
            # Set session expiry based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on user type
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            elif user.is_superuser:
                return redirect('base_dash')
            else:
                return redirect('system:newcar')
    
    context = {
        "form": form,
        "title": "Sign In",
    }
    return render(request, "auth/login.html", context)


def password_reset_request_view(request):
    """Password reset request view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    form = PasswordResetRequestForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            if send_password_reset_email(user):
                messages.success(request, 
                    f'Password reset instructions sent to {email}. Please check your inbox.')
                return redirect('password_reset_sent')
            else:
                messages.error(request, 'Failed to send password reset email. Please try again later.')
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            messages.success(request, 
                f'If an account with email {email} exists, password reset instructions have been sent.')
            return redirect('password_reset_sent')
    
    context = {
        "title": "Reset Password",
        "form": form,
    }
    return render(request, "auth/password_reset_request.html", context)


def password_reset_sent_view(request):
    """Password reset email sent confirmation"""
    return render(request, "auth/password_reset_sent.html", {
        "title": "Reset Email Sent"
    })


def password_reset_confirm_view(request, token):
    """Password reset confirmation with token"""
    try:
        user = User.objects.get(reset_password_token=token)
        if not user.is_reset_token_valid(token):
            messages.error(request, 'Password reset link has expired. Please request a new one.')
            return redirect('password_reset_request')
    except User.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('password_reset_request')
    
    form = PasswordResetConfirmForm(request.POST or None)
    if form.is_valid():
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.reset_password_expires = None
        user.save()
        
        messages.success(request, 'Password reset successfully! You can now log in with your new password.')
        return redirect('login')
    
    context = {
        "title": "Set New Password",
        "form": form,
        "user": user,
    }
    return render(request, "auth/password_reset_confirm.html", context)


def admin_register_view(request):
    """Admin registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        try:
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.email_verified = True  # Auto-verify admin accounts
            user.is_active = True
            user.save()
            
            messages.success(request, 'Admin account created successfully!')
            return redirect('login')
        except Exception as e:
            logger.error(f"Admin registration error: {str(e)}")
            messages.error(request, 'An error occurred during admin registration. Please try again.')
    
    context = {
        "title": "Admin Registration",
        "form": form,
    }
    return render(request, "auth/admin_register.html", context)


def logout_view(request):
    """Enhanced logout view"""
    if request.user.is_authenticated:
        user_name = request.user.get_full_name()
        logout(request)
        messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('home')
