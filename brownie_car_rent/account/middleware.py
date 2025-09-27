"""
Custom middleware for enhanced error handling and logging.
"""

import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for handling errors gracefully and providing user-friendly responses.
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions and provide appropriate responses.
        """
        # Log the error
        logger.error(
            f"Error occurred: {exception}",
            extra={
                'request': request,
                'user': request.user if hasattr(request, 'user') else None,
                'path': request.path,
                'method': request.method,
                'traceback': traceback.format_exc()
            }
        )
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': True,
                'message': 'An error occurred. Please try again.',
                'debug_info': str(exception) if settings.DEBUG else None
            }, status=500)
        
        # Handle regular requests
        context = {
            'error_message': 'An unexpected error occurred. Please try again.',
            'error_code': 500,
            'debug_info': str(exception) if settings.DEBUG else None
        }
        
        return render(request, 'errors/500.html', context, status=500)


class UserFriendlyErrorMiddleware(MiddlewareMixin):
    """
    Middleware to catch common errors and provide user-friendly messages.
    """
    
    def process_exception(self, request, exception):
        """
        Process specific exceptions and provide user-friendly messages.
        """
        from django.core.exceptions import ValidationError, PermissionDenied
        from django.db import IntegrityError
        from django.contrib.auth.models import AnonymousUser
        
        # Handle validation errors
        if isinstance(exception, ValidationError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': 'Please check your input and try again.',
                    'validation_errors': exception.message_dict if hasattr(exception, 'message_dict') else [str(exception)]
                }, status=400)
            
            messages.error(request, 'Please check your input and try again.')
            return None
        
        # Handle permission denied
        if isinstance(exception, PermissionDenied):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': 'You do not have permission to perform this action.'
                }, status=403)
            
            messages.error(request, 'You do not have permission to perform this action.')
            return render(request, 'errors/403.html', status=403)
        
        # Handle database integrity errors
        if isinstance(exception, IntegrityError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': 'A database error occurred. Please try again.'
                }, status=500)
            
            messages.error(request, 'A database error occurred. Please try again.')
            return None
        
        # Let other exceptions be handled by the default error handler
        return None


class SecurityMiddleware(MiddlewareMixin):
    """
    Additional security middleware for enhanced protection.
    """
    
    def process_request(self, request):
        """
        Process incoming requests for security checks.
        """
        # Rate limiting (basic implementation)
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Log user activity
            logger.info(
                f"User activity: {request.user.username} - {request.method} {request.path}",
                extra={
                    'user_id': request.user.id,
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')
                }
            )
        
        return None
    
    def get_client_ip(self, request):
        """
        Get the client's IP address.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
