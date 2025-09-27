"""
Session model service for the AI chat assistant.
This service extracts and maintains a session-level model of the website content.
"""
import json
import decimal
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Car, Order
from django.contrib.auth import get_user_model
User = get_user_model()


# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class SessionModelService:
    """Service to extract and maintain a structured session model of the website content."""
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'CHAT_SESSION_CACHE_TIMEOUT', 300)  # 5 minutes default
        self.cache = {}
        self.cache_timestamps = {}
    
    def _is_cache_valid(self, session_id):
        """Check if the cached session model is still valid."""
        if session_id not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[session_id]
        current_time = timezone.now()
        
        return (current_time - cache_time).total_seconds() < self.cache_timeout
    
    def get_session_model(self, session_id, force_refresh=False):
        """
        Get the session model for a given session ID.
        If the model doesn't exist or is expired, create a new one.
        """
        if not force_refresh and session_id in self.cache and self._is_cache_valid(session_id):
            return self.cache[session_id]
        
        # Create a new session model
        session_model = self._build_session_model()
        
        # Cache the session model
        self.cache[session_id] = session_model
        self.cache_timestamps[session_id] = timezone.now()
        
        return session_model
    
    def _build_session_model(self):
        """Build a complete session model with all site data."""
        return {
            'fleet': self._get_fleet_data(),
            'categories': self._get_categories(),
            'policies': self._get_policies(),
            'contact_info': self._get_contact_info(),
            'locations': self._get_locations(),
            'faqs': self._get_faqs(),
            'booking_info': self._get_booking_info(),
        }
    
    def _get_fleet_data(self):
        """Extract all car entries with complete details."""
        cars = Car.objects.all()
        
        fleet_data = []
        for car in cars:
            car_data = {
                'id': car.id,
                'name': car.car_name,
                'company_name': car.company_name,
                'category': self._determine_category(car),
                'price_per_day': float(car.cost_par_day),
                'currency': 'USD',  # Assuming USD is the default currency
                'seats': car.num_of_seats,
                'availability': self._check_availability(car),
                'content': car.content,
                'popularity': car.like,
                'images': [self._get_full_image_url(car.image)] if car.image else [],
                'features': self._extract_features(car.content),
                'transmission': self._extract_transmission(car.content),
                'fuel_type': self._extract_fuel_type(car.content),
            }
            fleet_data.append(car_data)
        
        return fleet_data
    
    def _determine_category(self, car):
        """Determine car category based on name and content."""
        name_lower = car.car_name.lower()
        content_lower = car.content.lower()
        
        # Determine category based on car name and content
        if any(luxury in name_lower or luxury in content_lower for luxury in ['luxury', 'premium', 'mercedes', 'bmw', 'audi']):
            return 'Luxury'
        elif any(suv in name_lower or suv in content_lower for suv in ['suv', 'crossover', 'off-road']):
            return 'SUV'
        elif any(sedan in name_lower or sedan in content_lower for sedan in ['sedan', 'saloon']):
            return 'Sedan'
        elif any(compact in name_lower or compact in content_lower for compact in ['compact', 'hatchback', 'small']):
            return 'Compact'
        elif any(convertible in name_lower or convertible in content_lower for convertible in ['convertible', 'cabriolet']):
            return 'Convertible'
        
        # Default category
        return 'Other'
    
    def _check_availability(self, car):
        """Check if a car is currently available for booking."""
        # This is a simplified implementation; in a real system, you'd check against existing orders
        current_orders = Order.objects.filter(
            Q(car_name__icontains=car.car_name) & 
            Q(status__in=['pending', 'confirmed']) &
            (
                Q(date_from__lte=timezone.now().date(), date_to__gte=timezone.now().date()) |
                Q(pick_up_date__lte=timezone.now().date(), drop_off_date__gte=timezone.now().date())
            )
        ).count()
        
        return 'available' if current_orders == 0 else 'booked'
    
    def _extract_features(self, content):
        """Extract car features from content description."""
        features = []
        content_lower = content.lower()
        
        # Common car features to look for
        feature_keywords = {
            'bluetooth': ['bluetooth', 'wireless connectivity'],
            'gps': ['gps', 'navigation', 'sat nav'],
            'air conditioning': ['air conditioning', 'ac', 'climate control'],
            'leather seats': ['leather seats', 'leather interior'],
            'sunroof': ['sunroof', 'moonroof'],
            'backup camera': ['backup camera', 'rear camera', 'parking camera'],
            'cruise control': ['cruise control'],
            'usb': ['usb', 'usb charging'],
            'heated seats': ['heated seats'],
            'aux input': ['aux', 'auxiliary input'],
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _extract_transmission(self, content):
        """Extract transmission type from content description."""
        content_lower = content.lower()
        
        if any(auto in content_lower for auto in ['automatic', 'auto transmission']):
            return 'Automatic'
        elif any(manual in content_lower for manual in ['manual', 'stick shift', 'standard']):
            return 'Manual'
        
        # Default to automatic if not specified
        return 'Automatic'
    
    def _extract_fuel_type(self, content):
        """Extract fuel type from content description."""
        content_lower = content.lower()
        
        if any(petrol in content_lower for petrol in ['petrol', 'gasoline']):
            return 'Petrol'
        elif any(diesel in content_lower for diesel in ['diesel']):
            return 'Diesel'
        elif any(hybrid in content_lower for hybrid in ['hybrid']):
            return 'Hybrid'
        elif any(electric in content_lower for electric in ['electric']):
            return 'Electric'
        
        # Default to petrol if not specified
        return 'Petrol'
    
    def _get_full_image_url(self, image_field):
        """Build full URL for car image."""
        if not image_field:
            return None
        
        # If we have access to request context, build absolute URL
        try:
            from django.contrib.sites.shortcuts import get_current_site
            from django.conf import settings
            
            # Build full URL with domain
            if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL:
                # Handle both relative and absolute MEDIA_URL
                if settings.MEDIA_URL.startswith('http'):
                    return settings.MEDIA_URL.rstrip('/') + '/' + image_field.name
                else:
                    # For relative MEDIA_URL, we need to add the domain
                    # Use a fallback since we don't have request context here
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    return base_url.rstrip('/') + settings.MEDIA_URL.rstrip('/') + '/' + image_field.name
            else:
                # Fallback to relative URL
                return image_field.url
        except Exception:
            # Fallback to relative URL
            return image_field.url if image_field else None
    
    def _get_categories(self):
        """Get all car categories with counts."""
        fleet = self._get_fleet_data()
        categories = {}
        
        for car in fleet:
            category = car['category']
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        return [{'name': k, 'count': v} for k, v in categories.items()]
    
    def _get_policies(self):
        """Get company policies for car rentals."""
        return {
            'cancellation': 'Free cancellation up to 48 hours before pickup. Cancellations made less than 48 hours before pickup may be charged a cancellation fee of up to one day\'s rental.',
            'insurance': 'Basic insurance is included in all rentals. Premium insurance options are available at an additional cost.',
            'deposit': 'A security deposit of $100-200 (depending on car type) is required for all rentals.',
            'age_requirements': 'Drivers must be at least 21 years old. Drivers under 25 may be subject to a young driver surcharge.',
            'payment_methods': 'We accept all major credit cards, Paystack, and Pay Later options for qualified customers.',
            'fuel': 'All vehicles are provided with a full tank of fuel and should be returned with a full tank.',
            'mileage': 'Unlimited mileage for all rentals.',
            'additional_drivers': 'Additional drivers can be added to the rental agreement for a fee of $10 per day.',
            'international_drivers': 'International drivers must present a valid driver\'s license and passport.'
        }
    
    def _get_contact_info(self):
        """Get company contact information."""
        return {
            'company_name': 'Brownie Car Rentals',
            'email': 'info@browniecarrent.com',
            'phone': '+234 123 456 7890',
            'hours': 'Monday to Friday: 8am - 8pm, Saturday: 9am - 6pm, Sunday: 10am - 4pm',
            'social_media': {
                'facebook': 'https://facebook.com/browniecarrentals',
                'twitter': 'https://twitter.com/browniecarrent',
                'instagram': 'https://instagram.com/browniecarrent'
            }
        }
    
    def _get_locations(self):
        """Get pickup/dropoff locations."""
        return [
            {
                'name': 'Lagos Airport',
                'address': 'Murtala Muhammed International Airport, Lagos, Nigeria',
                'coordinates': {'lat': 6.5774, 'lng': 3.3212},
                'hours': '24/7',
                'phone': '+234 123 456 7890'
            },
            {
                'name': 'Lagos Downtown',
                'address': '123 Victoria Island, Lagos, Nigeria',
                'coordinates': {'lat': 6.4281, 'lng': 3.4219},
                'hours': 'Monday to Friday: 8am - 8pm, Saturday: 9am - 6pm, Sunday: 10am - 4pm',
                'phone': '+234 123 456 7891'
            },
            {
                'name': 'Abuja Airport',
                'address': 'Nnamdi Azikiwe International Airport, Abuja, Nigeria',
                'coordinates': {'lat': 9.0065, 'lng': 7.2631},
                'hours': '24/7',
                'phone': '+234 123 456 7892'
            },
            {
                'name': 'Abuja City Center',
                'address': '456 Central District, Abuja, Nigeria',
                'coordinates': {'lat': 9.0765, 'lng': 7.3986},
                'hours': 'Monday to Friday: 8am - 8pm, Saturday: 9am - 6pm, Sunday: 10am - 4pm',
                'phone': '+234 123 456 7893'
            },
            {
                'name': 'Port Harcourt Airport',
                'address': 'Port Harcourt International Airport, Nigeria',
                'coordinates': {'lat': 5.0159, 'lng': 6.9695},
                'hours': '24/7',
                'phone': '+234 123 456 7894'
            }
        ]
    
    def _get_faqs(self):
        """Get frequently asked questions."""
        return [
            {
                'question': 'What documents do I need to rent a car?',
                'answer': 'You will need a valid driver\'s license, a credit card in your name, and a valid ID or passport.'
            },
            {
                'question': 'Is there a minimum age requirement to rent a car?',
                'answer': 'Yes, drivers must be at least 21 years old. Drivers under 25 may be subject to a young driver surcharge.'
            },
            {
                'question': 'What is the fuel policy?',
                'answer': 'All vehicles are provided with a full tank of fuel and should be returned with a full tank.'
            },
            {
                'question': 'Can I modify or cancel my booking?',
                'answer': 'Yes, you can modify or cancel your booking online through your account or by calling our customer service. Free cancellation is available up to 48 hours before pickup.'
            },
            {
                'question': 'Is insurance included in the rental price?',
                'answer': 'Basic insurance is included in all rentals. Premium insurance options are available at an additional cost.'
            },
            {
                'question': 'Can I pick up the car at one location and return it to another?',
                'answer': 'Yes, we offer one-way rentals. Please note that additional fees may apply.'
            },
            {
                'question': 'Do you have unlimited mileage?',
                'answer': 'Yes, all our rentals come with unlimited mileage.'
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept all major credit cards, Paystack, and Pay Later options for qualified customers.'
            }
        ]
    
    def _get_booking_info(self):
        """Get booking-related information."""
        return {
            'min_booking_days': 1,
            'max_booking_days': 30,
            'allowed_booking_advance_days': 180,
            'deposit_amounts': {
                'Luxury': 200,
                'SUV': 150,
                'Sedan': 100,
                'Compact': 100,
                'Convertible': 200,
                'Other': 100
            },
            'extras': [
                {'name': 'GPS Navigation', 'price_per_day': 5.00},
                {'name': 'Child Seat', 'price_per_day': 8.00},
                {'name': 'Additional Driver', 'price_per_day': 10.00},
                {'name': 'Roadside Assistance', 'price_per_day': 7.50},
                {'name': 'Wifi Hotspot', 'price_per_day': 6.00}
            ],
            'insurance_options': [
                {'name': 'Basic (included)', 'price_per_day': 0.00},
                {'name': 'Premium', 'price_per_day': 15.00},
                {'name': 'Full Coverage', 'price_per_day': 25.00}
            ]
        }
    
    def update_session_model(self, session_id, updates):
        """Update specific parts of the session model."""
        if session_id not in self.cache:
            self.get_session_model(session_id)
        
        # Update the session model with the provided updates
        for key, value in updates.items():
            if key in self.cache[session_id]:
                self.cache[session_id][key] = value
        
        # Update the timestamp
        self.cache_timestamps[session_id] = timezone.now()
        
        return self.cache[session_id]

    def to_json(self, session_id):
        """Convert session model to JSON string."""
        model = self.get_session_model(session_id)
        return json.dumps(model, cls=DecimalEncoder)


# Initialize the session model service
session_model_service = SessionModelService()