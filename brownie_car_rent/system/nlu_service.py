"""
Natural Language Understanding (NLU) Service for AI Chat Assistant.
Handles intent detection and entity extraction for car rental inquiries.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

import dateutil.parser
from dateutil.relativedelta import relativedelta


class NLUService:
    """Service for natural language understanding and entity extraction."""
    
    def __init__(self):
        self.intents = {
            'greeting': {
                'patterns': [
                    r'\b(hello|hi|hey|greetings?|good\s+(morning|afternoon|evening))\b',
                    r'\b(welcome|start|begin)\b',
                    r'\b(howdy|what\'s\s+up|sup)\b'
                ]
            },
            'browse_inventory': {
                'patterns': [
                    r'\b(show|list|browse|see|view|display)\b.*\b(cars?|vehicles?|fleet|inventory)\b',
                    r'\b(what\s+(cars?|vehicles?)|available\s+(cars?|vehicles?))\b',
                    r'\b(car\s+(options|catalog|selection))\b'
                ]
            },
            'get_price': {
                'patterns': [
                    r'\b(price|cost|rate|fee|charge|pricing|how\s+much)\b',
                    r'\b(cheap|expensive|affordable|budget)\b',
                    r'\b(price\s+(for|of)|cost\s+(for|of))\b'
                ]
            },
            'compare_cars': {
                'patterns': [
                    r'\b(compare|comparison|difference|vs|versus)\b',
                    r'\b(which\s+(is|car)\s+(better|best|cheaper))\b',
                    r'\b(difference\s+between)\b'
                ]
            },
            'book_reserve': {
                'patterns': [
                    r'\b(book|booking|reserve|reservation|rent|rental)\b',
                    r'\b(make\s+(booking|reservation))\b',
                    r'\b(i\s+(want\s+to|would\s+like\s+to)\s+(book|reserve|rent))\b'
                ]
            },
            'availability': {
                'patterns': [
                    r'\b(available|availability|free|vacant)\b',
                    r'\b(is\s+.+\s+available)\b',
                    r'\b(when\s+(is|are)\s+.+\s+available)\b'
                ]
            },
            'ask_policy': {
                'patterns': [
                    r'\b(policy|policies|rules?|terms?|condition|cancellation|insurance)\b',
                    r'\b(what\s+(if|happens)|can\s+i\s+(cancel|modify))\b',
                    r'\b(deposit|payment\s+method|age\s+requirement)\b'
                ]
            },
            'contact_support': {
                'patterns': [
                    r'\b(contact|call|phone|email|support|help|assistance)\b',
                    r'\b(speak\s+(to|with)|talk\s+(to|with)|human|agent|person)\b',
                    r'\b(customer\s+service|support\s+team)\b'
                ]
            },
            'request_images': {
                'patterns': [
                    r'\b(image|images|photo|photos|picture|pictures)\b',
                    r'\b(show\s+me\s+(image|photo|picture))\b',
                    r'\b(what\s+does\s+.+\s+look\s+like)\b'
                ]
            },
            'ask_directions': {
                'patterns': [
                    r'\b(direction|directions|location|address|where|map)\b',
                    r'\b(how\s+to\s+(get\s+to|find))\b',
                    r'\b(pickup\s+location|drop\s*off\s+location)\b'
                ]
            },
            'change_booking': {
                'patterns': [
                    r'\b(change|modify|update|edit)\b.*\b(booking|reservation)\b',
                    r'\b(reschedule|postpone|extend)\b'
                ]
            },
            'cancel_booking': {
                'patterns': [
                    r'\b(cancel|cancellation)\b.*\b(booking|reservation)\b',
                    r'\b(delete|remove)\b.*\b(booking|reservation)\b'
                ]
            },
            'faq_general': {
                'patterns': [
                    r'\b(faq|frequently\s+asked|common\s+questions?)\b',
                    r'\b(what\s+(do|can)\s+you\s+(do|help))\b',
                    r'\b(how\s+does\s+(it|this)\s+work)\b',
                    r'\b(tell\s+me\s+about)\b'
                ]
            },
            'ask_hours': {
                'patterns': [
                    r'\b(hours?|opening|closing|open|close|schedule)\b',
                    r'\b(what\s+time|when\s+(are\s+you|do\s+you))\b.*\b(open|close)\b',
                    r'\b(business\s+hours|operating\s+hours)\b'
                ]
            },
            'ask_age_requirement': {
                'patterns': [
                    r'\b(age\s+(requirement|limit)|how\s+old|minimum\s+age)\b',
                    r'\b(can\s+.+\s+year\s+old\s+rent)\b',
                    r'\b(young\s+driver|underage)\b'
                ]
            },
            'ask_documents': {
                'patterns': [
                    r'\b(documents?|documentation|papers?|id|license)\b.*\b(need|required)\b',
                    r'\b(what\s+do\s+i\s+need|requirements?)\b',
                    r'\b(driver\'s\s+license|passport|credit\s+card)\b'
                ]
            },
            'ask_insurance': {
                'patterns': [
                    r'\b(insurance|coverage|insured)\b',
                    r'\b(what\s+if\s+.+\s+(accident|damage))\b',
                    r'\b(comprehensive|collision|liability)\b'
                ]
            },
            'ask_fuel_policy': {
                'patterns': [
                    r'\b(fuel|gas|gasoline|petrol)\b.*\b(policy|rule)\b',
                    r'\b(full\s+tank|empty\s+tank|fuel\s+level)\b',
                    r'\b(refuel|refueling)\b'
                ]
            },
            'ask_mileage': {
                'patterns': [
                    r'\b(mileage|kilometer|km|mile)\b.*\b(limit|unlimited)\b',
                    r'\b(how\s+(far|much)\s+can\s+i\s+drive)\b',
                    r'\b(distance\s+limit)\b'
                ]
            },
            'ask_payment': {
                'patterns': [
                    r'\b(payment|pay|cost|money|cash|card|paystack)\b',
                    r'\b(how\s+(do\s+i|to)\s+pay)\b',
                    r'\b(payment\s+(method|option)|credit\s+card)\b'
                ]
            },
            'ask_discount': {
                'patterns': [
                    r'\b(discount|promo|coupon|deal|offer|special)\b',
                    r'\b(cheap|cheaper|save\s+money|best\s+price)\b',
                    r'\b(student\s+discount|corporate\s+rate)\b'
                ]
            },
            'ask_extras': {
                'patterns': [
                    r'\b(extras?|add\s*on|additional|gps|child\s+seat)\b',
                    r'\b(navigation|wifi|hotspot|roadside)\b',
                    r'\b(what\s+(else|additional)\s+can\s+i\s+get)\b'
                ]
            },
            'emergency_help': {
                'patterns': [
                    r'\b(emergency|urgent|help|problem|issue|broke\s+down)\b',
                    r'\b(car\s+(won\'t\s+start|broken|problem))\b',
                    r'\b(roadside\s+(assistance|help))\b'
                ]
            },
            'compliment': {
                'patterns': [
                    r'\b(good|great|excellent|amazing|awesome|perfect|love|like)\b',
                    r'\b(you\'re\s+(helpful|great|good))\b',
                    r'\b(thank\s+you\s+so\s+much|thanks\s+a\s+lot)\b'
                ]
            },
            'complaint': {
                'patterns': [
                    r'\b(bad|terrible|awful|horrible|disappointed|unhappy)\b',
                    r'\b(complaint|complain|problem|issue|wrong)\b',
                    r'\b(not\s+(working|happy|satisfied))\b'
                ]
            },
            'goodbye': {
                'patterns': [
                    r'\b(bye|goodbye|thanks?|thank\s+you|done|finish|exit|quit)\b',
                    r'\b(have\s+a\s+good\s+(day|time))\b',
                    r'\b(see\s+you|talk\s+to\s+you\s+later|ttyl)\b'
                ]
            }
        }
        
        self.entities = {
            'car_category': [
                'luxury', 'premium', 'suv', 'sedan', 'compact', 'convertible',
                'economy', 'standard', 'intermediate', 'full-size', 'supercar',
                'executive', 'sport', 'hybrid', 'electric'
            ],
            'car_names': [
                'mercedes', 'bmw', 'audi', 'toyota', 'honda', 'nissan',
                'ford', 'chevrolet', 'hyundai', 'kia', 'lexus', 'lamborghini',
                'rolls royce', 'maybach', 'tesla', 'land rover', 'range rover'
            ],
            'locations': [
                'lagos', 'abuja', 'port harcourt', 'airport', 'downtown',
                'city center', 'victoria island', 'ikeja', 'terminal',
                'hotel district', 'business district'
            ],
            'extras': [
                'gps', 'navigation', 'child seat', 'additional driver',
                'roadside assistance', 'wifi', 'hotspot', 'insurance',
                'premium insurance', 'zero deductible'
            ]
        }
    
    def extract_intent(self, message):
        """
        Extract the primary intent from a user message.
        Returns tuple: (intent, confidence)
        """
        message_lower = message.lower().strip()
        
        best_intent = 'default'
        best_confidence = 0.0
        
        for intent, config in self.intents.items():
            confidence = 0.0
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                if matches:
                    # Calculate confidence based on match quality
                    match_confidence = len(matches) * 0.3
                    if match_confidence > confidence:
                        confidence = match_confidence
            
            # Boost confidence if multiple patterns match
            if confidence > 0.2 and confidence > best_confidence:
                best_intent = intent
                best_confidence = confidence
        
        # Ensure minimum confidence threshold
        if best_confidence < 0.15:
            best_intent = 'default'
            best_confidence = 0.1
        
        return best_intent, min(best_confidence, 1.0)
    
    def extract_entities(self, message):
        """
        Extract entities from the user message.
        Returns dictionary with extracted entities.
        """
        entities = {}
        message_lower = message.lower().strip()
        
        # Extract dates
        date_entities = self._extract_dates(message)
        if date_entities:
            entities.update(date_entities)
        
        # Extract numbers
        numbers = self._extract_numbers(message)
        if numbers:
            entities['numbers'] = numbers
        
        # Extract car categories
        categories = self._extract_car_categories(message_lower)
        if categories:
            entities['car_categories'] = categories
        
        # Extract car names/brands
        car_names = self._extract_car_names(message_lower)
        if car_names:
            entities['car_names'] = car_names
        
        # Extract locations
        locations = self._extract_locations(message_lower)
        if locations:
            entities['locations'] = locations
        
        # Extract extras/add-ons
        extras = self._extract_extras(message_lower)
        if extras:
            entities['extras'] = extras
        
        # Extract passenger count
        passengers = self._extract_passenger_count(message)
        if passengers:
            entities['passengers'] = passengers
        
        # Extract contact information
        contact = self._extract_contact_info(message)
        if contact:
            entities.update(contact)
        
        # Extract promo codes
        promo_code = self._extract_promo_code(message)
        if promo_code:
            entities['promo_code'] = promo_code
        
        return entities
    
    def _extract_dates(self, message):
        """Extract dates from message using various patterns."""
        entities = {}
        
        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY-MM-DD
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}\b',
            r'\b(today|tomorrow|yesterday)\b',
            r'\b(next\s+(week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
            r'\b(this\s+(week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    
                    # Parse relative dates
                    parsed_date = self._parse_relative_date(match.lower())
                    if parsed_date:
                        dates_found.append(parsed_date)
                    else:
                        # Try parsing absolute dates
                        parsed_date = dateutil.parser.parse(match, fuzzy=True)
                        dates_found.append(parsed_date.date())
                except:
                    continue
        
        # Assign dates to pickup/dropoff based on context
        if dates_found:
            if len(dates_found) >= 2:
                entities['pickup_date'] = dates_found[0]
                entities['dropoff_date'] = dates_found[1]
            else:
                # Determine if it's pickup or dropoff based on context
                if any(word in message.lower() for word in ['pickup', 'pick up', 'start', 'from']):
                    entities['pickup_date'] = dates_found[0]
                elif any(word in message.lower() for word in ['dropoff', 'drop off', 'return', 'until', 'to']):
                    entities['dropoff_date'] = dates_found[0]
                else:
                    entities['pickup_date'] = dates_found[0]
        
        return entities
    
    def _parse_relative_date(self, date_str):
        """Parse relative date strings like 'today', 'tomorrow', 'next week'."""
        today = timezone.now().date()
        
        if 'today' in date_str:
            return today
        elif 'tomorrow' in date_str:
            return today + timedelta(days=1)
        elif 'yesterday' in date_str:
            return today - timedelta(days=1)
        elif 'next week' in date_str:
            return today + timedelta(days=7)
        elif 'next month' in date_str:
            return today + relativedelta(months=1)
        elif 'next' in date_str:
            # Handle 'next monday', 'next tuesday', etc.
            weekdays = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            for day, num in weekdays.items():
                if day in date_str:
                    days_ahead = num - today.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)
        
        return None
    
    def _extract_numbers(self, message):
        """Extract numeric values from the message."""
        # Pattern for numbers (including written numbers)
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        numbers = re.findall(number_pattern, message)
        
        # Convert to appropriate data types
        parsed_numbers = []
        for num in numbers:
            try:
                if '.' in num:
                    parsed_numbers.append(float(num))
                else:
                    parsed_numbers.append(int(num))
            except ValueError:
                continue
        
        return parsed_numbers
    
    def _extract_car_categories(self, message):
        """Extract car category mentions."""
        found_categories = []
        for category in self.entities['car_category']:
            if category in message:
                found_categories.append(category.title())
        return found_categories
    
    def _extract_car_names(self, message):
        """Extract car brand/model mentions."""
        found_names = []
        for name in self.entities['car_names']:
            if name in message:
                found_names.append(name.title())
        return found_names
    
    def _extract_locations(self, message):
        """Extract location mentions."""
        found_locations = []
        for location in self.entities['locations']:
            if location in message:
                found_locations.append(location.title())
        return found_locations
    
    def _extract_extras(self, message):
        """Extract extras/add-ons mentions."""
        found_extras = []
        for extra in self.entities['extras']:
            if extra in message:
                found_extras.append(extra.title())
        return found_extras
    
    def _extract_passenger_count(self, message):
        """Extract number of passengers."""
        passenger_patterns = [
            r'(\d+)\s+(passenger|person|people|adult|seat)',
            r'(passenger|person|people|adult|seat)\s*:?\s*(\d+)',
            r'(\d+)\s+seat',
            r'seat\s*:?\s*(\d+)'
        ]
        
        for pattern in passenger_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Extract number from tuple match
                        if isinstance(match, tuple):
                            for item in match:
                                if item.isdigit():
                                    return int(item)
                        else:
                            return int(match)
                    except ValueError:
                        continue
        return None
    
    def _extract_contact_info(self, message):
        """Extract contact information like email, phone."""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone pattern (various formats)
        phone_patterns = [
            r'\+?234\s?\d{3}\s?\d{3}\s?\d{4}',  # Nigerian format
            r'\+?\d{1,4}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4}',  # International format
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Standard format
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, message)
            if phones:
                contact_info['phone'] = phones[0]
                break
        
        # Name extraction (simple pattern)
        name_pattern = r'\bmy\s+name\s+is\s+([A-Za-z\s]{2,30})\b'
        names = re.findall(name_pattern, message, re.IGNORECASE)
        if names:
            contact_info['name'] = names[0].strip()
        
        return contact_info
    
    def _extract_promo_code(self, message):
        """Extract promo/discount codes."""
        promo_patterns = [
            r'\b(promo|promocode|discount|coupon)\s*:?\s*([A-Z0-9]{4,15})\b',
            r'\bcode\s*:?\s*([A-Z0-9]{4,15})\b'
        ]
        
        for pattern in promo_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        return match[1].upper()
                    else:
                        return match.upper()
        return None
    
    def analyze_message(self, message):
        """
        Perform complete NLU analysis on a message.
        Returns dictionary with intent, confidence, and entities.
        """
        intent, confidence = self.extract_intent(message)
        entities = self.extract_entities(message)
        
        return {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'original_message': message
        }


# Initialize the NLU service
nlu_service = NLUService()