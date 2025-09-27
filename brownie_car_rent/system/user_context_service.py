"""
Enhanced User Context Service for AI Chat System
Handles user identification, session persistence, progressive profiling, and personalization
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from .models import ChatRoom, ChatMessage
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class UserContextType:
    """User context type constants"""
    ANONYMOUS = 'anonymous'
    IDENTIFIED_GUEST = 'identified_guest'
    REGISTERED_USER = 'registered_user'
    RETURNING_CUSTOMER = 'returning_customer'

class UserContext:
    """Enhanced user context with progressive identification"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.user_type = UserContextType.ANONYMOUS
        self.user = None
        self.guest_info = {}
        self.session_data = {}
        self.conversation_history = []
        self.preferences = {}
        self.behavioral_data = {}
        self.created_at = timezone.now()
        self.last_activity = timezone.now()
        self.fingerprint = None
        self.device_info = {}
        self.is_returning = False
        self.interaction_count = 0
        self.collected_info = {}
        
    def to_dict(self):
        """Convert context to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'user_type': self.user_type,
            'user_id': self.user.id if self.user else None,
            'guest_info': self.guest_info,
            'session_data': self.session_data,
            'preferences': self.preferences,
            'behavioral_data': self.behavioral_data,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'fingerprint': self.fingerprint,
            'device_info': self.device_info,
            'is_returning': self.is_returning,
            'interaction_count': self.interaction_count,
            'collected_info': self.collected_info,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create context from dictionary"""
        context = cls(data['session_id'])
        context.user_type = data.get('user_type', UserContextType.ANONYMOUS)
        if data.get('user_id'):
            try:
                context.user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                pass
        context.guest_info = data.get('guest_info', {})
        context.session_data = data.get('session_data', {})
        context.preferences = data.get('preferences', {})
        context.behavioral_data = data.get('behavioral_data', {})
        context.fingerprint = data.get('fingerprint')
        context.device_info = data.get('device_info', {})
        context.is_returning = data.get('is_returning', False)
        context.interaction_count = data.get('interaction_count', 0)
        context.collected_info = data.get('collected_info', {})
        
        # Parse timestamps
        if data.get('created_at'):
            context.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('last_activity'):
            context.last_activity = datetime.fromisoformat(data['last_activity'].replace('Z', '+00:00'))
        
        return context

class UserContextService:
    """Service for managing enhanced user contexts with progressive identification"""
    
    def __init__(self):
        self.context_timeout = 3600 * 24 * 7  # 7 days for persistence
        self.fingerprint_timeout = 3600 * 24 * 30  # 30 days for fingerprint
        
    def get_or_create_context(self, session_id: str, request=None) -> UserContext:
        """Get or create user context with enhanced detection"""
        # Try to get existing context
        cache_key = f"user_context:{session_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            context = UserContext.from_dict(cached_data)
            context.last_activity = timezone.now()
            self._save_context(context)
            return context
        
        # Create new context
        context = UserContext(session_id)
        
        # Extract device and browser information
        if request:
            context.device_info = self._extract_device_info(request)
            context.fingerprint = self._generate_fingerprint(request)
            
            # Check for returning user by fingerprint
            returning_context = self._find_returning_user(context.fingerprint)
            if returning_context:
                context.is_returning = True
                context.behavioral_data = returning_context.get('behavioral_data', {})
                context.preferences = returning_context.get('preferences', {})
                logger.info(f"Detected returning user with fingerprint: {context.fingerprint[:8]}...")
        
        # Determine initial user type
        if request and request.user.is_authenticated:
            context.user = request.user
            context.user_type = self._determine_user_type(request.user)
            context.collected_info.update({
                'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'email': request.user.email,
                'is_authenticated': True
            })
        
        self._save_context(context)
        return context
    
    def _extract_device_info(self, request) -> dict:
        """Extract device and browser information"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self._get_client_ip(request)
        
        # Basic parsing of user agent
        device_info = {
            'user_agent': user_agent,
            'ip_address': ip_address,
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
            'is_mobile': self._is_mobile_device(user_agent),
            'browser': self._detect_browser(user_agent),
            'os': self._detect_os(user_agent),
            'screen_resolution': None,  # Will be updated via JavaScript
            'timezone': None,  # Will be updated via JavaScript
        }
        
        return device_info
    
    def _generate_fingerprint(self, request) -> str:
        """Generate browser fingerprint for user recognition"""
        # Combine multiple factors for fingerprinting
        factors = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', ''),
            request.META.get('HTTP_ACCEPT', ''),
            self._get_client_ip(request),
        ]
        
        # Create hash from combined factors
        fingerprint_string = '|'.join(factors)
        fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
        
        return fingerprint
    
    def _find_returning_user(self, fingerprint: str) -> Optional[dict]:
        """Find returning user by fingerprint"""
        if not fingerprint:
            return None
            
        fingerprint_key = f"user_fingerprint:{fingerprint}"
        return cache.get(fingerprint_key)
    
    def _determine_user_type(self, user) -> str:
        """Determine user type based on history and context"""
        # Check if user has previous orders
        from .models import Order
        
        order_count = Order.objects.filter(
            customer=user,
            status__in=['confirmed', 'completed']
        ).count()
        
        if order_count > 0:
            return UserContextType.RETURNING_CUSTOMER
        else:
            return UserContextType.REGISTERED_USER
    
    def update_context_with_info(self, context: UserContext, info_type: str, value: str):
        """Update context with progressively collected information"""
        context.collected_info[info_type] = value
        context.last_activity = timezone.now()
        
        # Update user type based on collected info
        if info_type == 'email' and context.user_type == UserContextType.ANONYMOUS:
            context.user_type = UserContextType.IDENTIFIED_GUEST
        
        # Try to match with existing user
        if info_type == 'email' and not context.user:
            try:
                existing_user = User.objects.get(email=value)
                context.user = existing_user
                context.user_type = self._determine_user_type(existing_user)
                context.collected_info['is_authenticated'] = True
                logger.info(f"Matched guest to existing user: {existing_user.email}")
            except User.DoesNotExist:
                pass
        
        self._save_context(context)
    
    def update_behavioral_data(self, context: UserContext, action: str, data: dict):
        """Update behavioral data for personalization"""
        if 'actions' not in context.behavioral_data:
            context.behavioral_data['actions'] = []
        
        action_data = {
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'data': data
        }
        
        context.behavioral_data['actions'].append(action_data)
        context.interaction_count += 1
        
        # Keep only last 50 actions
        if len(context.behavioral_data['actions']) > 50:
            context.behavioral_data['actions'] = context.behavioral_data['actions'][-50:]
        
        # Update preferences based on behavior
        self._update_preferences_from_behavior(context, action, data)
        
        self._save_context(context)
    
    def _update_preferences_from_behavior(self, context: UserContext, action: str, data: dict):
        """Update user preferences based on behavioral patterns"""
        if action == 'car_interest':
            car_category = data.get('category')
            if car_category:
                if 'preferred_categories' not in context.preferences:
                    context.preferences['preferred_categories'] = {}
                    
                category_count = context.preferences['preferred_categories'].get(car_category, 0)
                context.preferences['preferred_categories'][car_category] = category_count + 1
        
        elif action == 'price_inquiry':
            price_range = data.get('price_range')
            if price_range:
                context.preferences['budget_range'] = price_range
        
        elif action == 'location_interest':
            location = data.get('location')
            if location:
                if 'frequent_locations' not in context.preferences:
                    context.preferences['frequent_locations'] = []
                    
                if location not in context.preferences['frequent_locations']:
                    context.preferences['frequent_locations'].append(location)
    
    def get_personalized_greeting(self, context: UserContext) -> str:
        """Generate personalized greeting based on user context"""
        name = self._get_display_name(context)
        user_type = context.user_type
        is_returning = context.is_returning
        interaction_count = context.interaction_count
        
        if user_type == UserContextType.RETURNING_CUSTOMER:
            if is_returning:
                return f"Welcome back, {name}! Ready for your next adventure? I see you're a valued customer."
            else:
                return f"Hello {name}! Great to see a returning customer. How can I help with your next rental?"
        
        elif user_type == UserContextType.REGISTERED_USER:
            if interaction_count > 0:
                return f"Hi {name}! How can I assist you with your car rental needs today?"
            else:
                return f"Welcome to Brownie Car Rentals, {name}! I'm here to help you find the perfect car."
        
        elif user_type == UserContextType.IDENTIFIED_GUEST:
            return f"Hello {name}! Thanks for chatting with us. What can I help you find today?"
        
        else:  # ANONYMOUS
            if is_returning:
                return "Welcome back! I remember you've been here before. How can I help you today?"
            elif interaction_count > 3:
                return "Hello again! What can I help you with this time?"
            else:
                return "Hello! I'm Brownie Assistant. I can help you view cars, check prices, or make a booking. What would you like to do?"
    
    def get_personalized_suggestions(self, context: UserContext) -> List[str]:
        """Get personalized suggestions based on user context"""
        suggestions = []
        preferences = context.preferences
        
        # Category-based suggestions
        if 'preferred_categories' in preferences:
            top_category = max(preferences['preferred_categories'].items(), key=lambda x: x[1])[0]
            suggestions.append(f"Browse {top_category} Cars")
        
        # Budget-based suggestions
        if 'budget_range' in preferences:
            suggestions.append("Get Price Quote")
        
        # Location-based suggestions
        if 'frequent_locations' in preferences and preferences['frequent_locations']:
            location = preferences['frequent_locations'][0]
            suggestions.append(f"Cars in {location}")
        
        # Default suggestions if no preferences
        if not suggestions:
            suggestions = ["Browse Fleet", "Check Prices", "Book Now"]
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def _get_display_name(self, context: UserContext) -> str:
        """Get appropriate display name for user"""
        if context.user:
            name = f"{context.user.first_name} {context.user.last_name}".strip()
            return name or context.user.username
        
        if context.collected_info.get('name'):
            return context.collected_info['name']
        
        if context.collected_info.get('email'):
            # Extract name from email
            email_name = context.collected_info['email'].split('@')[0]
            return email_name.replace('.', ' ').replace('_', ' ').title()
        
        return "there"  # Friendly fallback
    
    def get_avatar_info(self, context: UserContext) -> dict:
        """Get avatar information for user"""
        avatar_info = {
            'type': 'generated',
            'initials': 'U',
            'color': '#007bff',
            'image_url': None,
            'has_profile_pic': False
        }
        
        display_name = self._get_display_name(context)
        
        # Generate initials
        if display_name and display_name != "there":
            name_parts = display_name.split()
            if len(name_parts) >= 2:
                avatar_info['initials'] = f"{name_parts[0][0]}{name_parts[1][0]}".upper()
            elif len(name_parts) == 1:
                avatar_info['initials'] = name_parts[0][:2].upper()
        
        # Generate color based on name
        if display_name != "there":
            avatar_info['color'] = self._generate_avatar_color(display_name)
        
        # Check for profile picture
        if context.user and hasattr(context.user, 'profile_picture'):
            if context.user.profile_picture:
                avatar_info['image_url'] = context.user.profile_picture.url
                avatar_info['has_profile_pic'] = True
                avatar_info['type'] = 'profile_pic'
        
        # Try Gravatar if email available
        email = context.collected_info.get('email') or (context.user.email if context.user else None)
        if email and not avatar_info['has_profile_pic']:
            gravatar_url = self._get_gravatar_url(email)
            avatar_info['gravatar_url'] = gravatar_url
        
        return avatar_info
    
    def _generate_avatar_color(self, name: str) -> str:
        """Generate consistent color for avatar based on name"""
        colors = [
            '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
            '#6610f2', '#e83e8c', '#fd7e14', '#20c997', '#6f42c1'
        ]
        
        # Hash name to get consistent color
        name_hash = hashlib.md5(name.encode()).hexdigest()
        color_index = int(name_hash[:2], 16) % len(colors)
        return colors[color_index]
    
    def _get_gravatar_url(self, email: str, size: int = 80) -> str:
        """Generate Gravatar URL"""
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=mp"
    
    def _save_context(self, context: UserContext):
        """Save context to cache with fingerprint tracking"""
        cache_key = f"user_context:{context.session_id}"
        cache.set(cache_key, context.to_dict(), self.context_timeout)
        
        # Save fingerprint mapping for returning user detection
        if context.fingerprint:
            fingerprint_key = f"user_fingerprint:{context.fingerprint}"
            fingerprint_data = {
                'last_session': context.session_id,
                'last_seen': context.last_activity.isoformat(),
                'behavioral_data': context.behavioral_data,
                'preferences': context.preferences,
                'total_sessions': context.behavioral_data.get('session_count', 0) + 1
            }
            cache.set(fingerprint_key, fingerprint_data, self.fingerprint_timeout)
    
    # Helper methods
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_mobile_device(self, user_agent: str) -> bool:
        """Detect if device is mobile"""
        mobile_patterns = ['Mobile', 'Android', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone']
        return any(pattern in user_agent for pattern in mobile_patterns)
    
    def _detect_browser(self, user_agent: str) -> str:
        """Detect browser type"""
        if 'Chrome' in user_agent:
            return 'Chrome'
        elif 'Firefox' in user_agent:
            return 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            return 'Safari'
        elif 'Edge' in user_agent:
            return 'Edge'
        elif 'Opera' in user_agent:
            return 'Opera'
        return 'Unknown'
    
    def _detect_os(self, user_agent: str) -> str:
        """Detect operating system"""
        if 'Windows' in user_agent:
            return 'Windows'
        elif 'Mac OS' in user_agent:
            return 'macOS'
        elif 'Linux' in user_agent:
            return 'Linux'
        elif 'Android' in user_agent:
            return 'Android'
        elif 'iOS' in user_agent:
            return 'iOS'
        return 'Unknown'

# Global service instance
user_context_service = UserContextService()