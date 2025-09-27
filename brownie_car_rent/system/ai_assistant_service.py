"""
AI Assistant Service for Car Rental Chat System.
Handles multi-turn conversations, maintains context, and provides guided booking flow.
"""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

from .session_model_service import session_model_service
from .nlu_service import nlu_service
from .user_context_service import user_context_service
from .models import ChatRoom, ChatMessage, Car, Order
from django.contrib.auth import get_user_model

User = get_user_model()


class ConversationContext:
    """Manages conversation context and slot filling for multi-turn conversations."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.slots = {}
        self.booking_state = 'initial'
        self.current_intent = None
        self.last_message_time = timezone.now()
        self.conversation_history = []
        self.selected_cars = []
        self.comparison_mode = False
        self.has_greeted = False
        self.last_prompt = None
        self.message_count = 0
        self.last_message_type = None
    
    def update_slots(self, entities):
        """Update conversation slots with new entities."""
        for key, value in entities.items():
            if value:  # Only update if value is not empty
                self.slots[key] = value
        self.last_message_time = timezone.now()
    
    def get_slot(self, slot_name, default=None):
        """Get value from a specific slot."""
        return self.slots.get(slot_name, default)
    
    def clear_slots(self, slot_names=None):
        """Clear specific slots or all slots."""
        if slot_names:
            for slot in slot_names:
                self.slots.pop(slot, None)
        else:
            self.slots.clear()
    
    def add_to_history(self, message_type, content):
        """Add message to conversation history."""
        self.conversation_history.append({
            'type': message_type,
            'content': content,
            'timestamp': timezone.now()
        })
        
        # Keep only last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


class AIAssistantService:
    """AI Assistant service for handling car rental conversations."""
    
    def __init__(self):
        self.contexts = {}
        self.context_timeout = 1800  # 30 minutes
        
        # Response templates
        self.response_templates = {
            'greeting': self._get_greeting_response,
            'browse_inventory': self._handle_browse_inventory,
            'get_price': self._handle_get_price,
            'book_reserve': self._handle_booking_request,
            'ask_policy': self._handle_policy_questions,
            'contact_support': self._handle_contact_support,
            'compare_cars': self._handle_compare_cars,
            'escalate_to_human': self._handle_human_escalation,
            'availability': self._handle_availability,
            'faq_general': self._handle_faq_general,
            'ask_hours': self._handle_business_hours,
            'ask_age_requirement': self._handle_age_requirement,
            'ask_documents': self._handle_documents_required,
            'ask_insurance': self._handle_insurance_info,
            'ask_fuel_policy': self._handle_fuel_policy,
            'ask_mileage': self._handle_mileage_policy,
            'ask_payment': self._handle_payment_options,
            'ask_discount': self._handle_discounts_promos,
            'ask_extras': self._handle_extras_addons,
            'emergency_help': self._handle_emergency_help,
            'compliment': self._handle_compliment,
            'complaint': self._handle_complaint,
            'change_booking': self._handle_change_booking,
            'cancel_booking': self._handle_cancel_booking,
            'ask_directions': self._handle_directions,
            'request_images': self._handle_request_images,
            'goodbye': self._handle_goodbye,
            'other': self._handle_fallback,
            'default': self._handle_default
        }
    
    def get_context(self, session_id):
        """Get or create conversation context for a session."""
        self._cleanup_expired_contexts()
        
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id)
        
        return self.contexts[session_id]
    
    def _cleanup_expired_contexts(self):
        """Remove expired conversation contexts."""
        current_time = timezone.now()
        expired_sessions = []
        
        for session_id, context in self.contexts.items():
            if (current_time - context.last_message_time).seconds > self.context_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.contexts[session_id]
    
    def process_message(self, session_id, message, user=None, request=None):
        """Process a user message and generate an appropriate response."""
        # Get enhanced user context
        user_context = user_context_service.get_or_create_context(session_id, request)
        
        # Get conversation context
        context = self.get_context(session_id)
        
        # Update behavioral data
        user_context_service.update_behavioral_data(
            user_context, 'message_sent', {'message': message, 'intent_detected': None}
        )
        
        # Check for duplicate message requests
        if (context.last_prompt and 
            context.last_prompt.strip().lower() == message.strip().lower() and 
            context.message_count > 0):
            return self._create_response_with_context(
                "I understand you're asking about that again. Let me help you with something specific.",
                user_context, context, session_id, 'duplicate_request',
                quick_replies=[
                    {'text': 'Show Available Cars', 'action': 'browse_inventory'},
                    {'text': 'Get Quote', 'action': 'get_price'},
                    {'text': 'Speak to Agent', 'action': 'escalate_to_human'}
                ]
            )
        
        # Analyze the message using NLU
        nlu_result = nlu_service.analyze_message(message)
        intent = nlu_result['intent']
        entities = nlu_result['entities']
        confidence = nlu_result['confidence']
        
        # Update behavioral data with detected intent
        user_context_service.update_behavioral_data(
            user_context, 'message_sent', {'message': message, 'intent_detected': intent}
        )
        
        # Extract and update user information from entities
        self._extract_user_info_from_entities(user_context, entities)
        
        # Update context with new information
        context.current_intent = intent
        context.message_count += 1
        context.last_message_type = intent
        context.last_prompt = message
        context.update_slots(entities)
        context.add_to_history('user', message)
        
        # Get session model for car data
        session_model = session_model_service.get_session_model(session_id)
        
        # Generate response based on intent
        if intent in self.response_templates:
            response_data = self.response_templates[intent](
                context, entities, session_model, user_context
            )
        else:
            response_data = self._handle_default(context, entities, session_model, user_context)
        
        # Enhance response with user context
        response_data = self._enhance_response_with_context(response_data, user_context, context)
        
        # Add response to conversation history
        context.add_to_history('assistant', response_data.get('text', ''))
        
        # Add metadata
        response_data.update({
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'session_id': session_id,
            'timestamp': timezone.now().isoformat(),
            'booking_state': context.booking_state,
            'user_context': {
                'user_type': user_context.user_type,
                'is_returning': user_context.is_returning,
                'interaction_count': user_context.interaction_count,
                'avatar_info': user_context_service.get_avatar_info(user_context)
            }
        })
        
        return response_data
    
    def _get_greeting_response(self, context, entities, session_model, user_context):
        """Handle greeting messages with personalized context."""
        # Prevent duplicate greetings
        if context.has_greeted and context.message_count > 1:
            # Get personalized "welcome back" message
            display_name = user_context_service._get_display_name(user_context)
            if display_name != "there":
                text = f"Welcome back, {display_name} — how can I help?"
            else:
                text = "Welcome back — how can I help?"
                
            return {
                'text': text,
                'type': 'text',
                'quick_replies': user_context_service.get_personalized_suggestions(user_context)
            }
        
        # First greeting - use personalized greeting
        context.has_greeted = True
        text = user_context_service.get_personalized_greeting(user_context)
        
        # Get personalized quick replies
        quick_replies = []
        suggestions = user_context_service.get_personalized_suggestions(user_context)
        
        for suggestion in suggestions:
            if 'Browse' in suggestion:
                action = 'browse_inventory'
            elif 'Price' in suggestion or 'Quote' in suggestion:
                action = 'get_price'
            elif 'Book' in suggestion:
                action = 'book_reserve'
            else:
                action = 'browse_inventory'
                
            quick_replies.append({
                'text': suggestion,
                'action': action
            })
        
        # Always add "Speak to Agent" option
        quick_replies.append({
            'text': 'Speak to Agent',
            'action': 'escalate_to_human'
        })
        
        return {
            'text': text,
            'type': 'text',
            'quick_replies': quick_replies,
            'actions': ['show_welcome']
        }
    
    def _handle_browse_inventory(self, context, entities, session_model, user):
        """Handle requests to browse car inventory."""
        fleet = session_model.get('fleet', [])
        
        # Filter by category if specified
        if context.get_slot('car_categories'):
            category = context.get_slot('car_categories')[0]
            fleet = [car for car in fleet if car.get('category', '').lower() == category.lower()]
        
        # Filter by availability
        available_cars = [car for car in fleet if car.get('availability') == 'available']
        
        if not available_cars:
            return {
                'text': 'I apologize, but I couldn\'t find any available cars matching your criteria at the moment. Would you like me to show all cars or help you with something else?',
                'type': 'text',
                'quick_replies': [
                    {'text': 'Show All Cars', 'action': 'show_all_cars'},
                    {'text': 'Contact Support', 'action': 'contact_support'}
                ]
            }
        
        # Show top 3 cars as cards
        cars_to_show = available_cars[:3]
        
        text = f"I found {len(available_cars)} available cars. Here are the top matches:"
        
        car_cards = []
        for car in cars_to_show:
            card = {
                'id': car['id'],
                'name': car['name'],
                'category': car['category'],
                'price_per_day': car['price_per_day'],
                'currency': car['currency'],
                'seats': car['seats'],
                'transmission': car['transmission'],
                'fuel_type': car['fuel_type'],
                'features': car['features'][:3],  # Show top 3 features
                'image': car['images'][0] if car['images'] else None,
                'actions': [
                    {'text': 'Select', 'action': 'select_car', 'car_id': car['id']},
                    {'text': 'Details', 'action': 'view_details', 'car_id': car['id']},
                    {'text': 'Compare', 'action': 'add_to_compare', 'car_id': car['id']}
                ]
            }
            car_cards.append(card)
        
        quick_replies = [
            {'text': 'View More Cars', 'action': 'view_more_cars'},
            {'text': 'Book Now', 'action': 'book_reserve'}
        ]
        
        return {
            'text': text,
            'type': 'car_cards',
            'car_cards': car_cards,
            'quick_replies': quick_replies,
            'actions': ['show_car_cards']
        }
    
    def _handle_get_price(self, context, entities, session_model, user):
        """Handle price inquiries."""
        fleet = session_model.get('fleet', [])
        categories = session_model.get('categories', [])
        
        price_ranges = []
        for category in categories:
            cat_name = category['name']
            cat_cars = [car for car in fleet if car.get('category') == cat_name]
            
            if cat_cars:
                prices = [car['price_per_day'] for car in cat_cars]
                price_ranges.append({
                    'category': cat_name,
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'car_count': len(cat_cars)
                })
        
        text = "Here are our price ranges by car category:\n\n"
        for price_range in price_ranges:
            text += f"**{price_range['category']}**: ${price_range['min_price']:.2f} - ${price_range['max_price']:.2f} per day ({price_range['car_count']} cars)\n"
        
        return {
            'text': text,
            'type': 'price_breakdown',
            'price_breakdown': price_ranges,
            'quick_replies': [
                {'text': 'Browse Cars', 'action': 'browse_inventory'},
                {'text': 'Make Booking', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_booking_request(self, context, entities, session_model, user):
        """Handle booking requests with guided flow."""
        text = "I'd be happy to help you with a booking! To get started, I'll need some information:\n\n"
        text += "1. Pickup and dropoff dates\n"
        text += "2. Pickup location\n"
        text += "3. Car preference (optional)\n"
        text += "4. Contact information\n\n"
        text += "Please tell me your preferred dates. For example: 'I need a car from tomorrow for 3 days' or 'January 15th to January 20th'"
        
        context.booking_state = 'requesting_dates'
        
        return {
            'text': text,
            'type': 'text',
            'booking_step': 'dates',
            'step_progress': '1/4',
            'quick_replies': [
                {'text': 'Tomorrow for 3 days', 'action': 'quick_date', 'dates': 'tomorrow_3days'},
                {'text': 'Next week for 5 days', 'action': 'quick_date', 'dates': 'nextweek_5days'}
            ]
        }
    
    def _handle_policy_questions(self, context, entities, session_model, user):
        """Handle policy-related questions."""
        policies = session_model.get('policies', {})
        
        text = "Here are our main rental policies:\n\n"
        for key, value in policies.items():
            title_formatted = key.replace('_', ' ').title()
            text += f"**{title_formatted}:** {value}\n\n"
        
        return {
            'text': text,
            'type': 'text',
            'quick_replies': [
                {'text': 'Contact Support', 'action': 'contact_support'},
                {'text': 'Book Now', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_contact_support(self, context, entities, session_model, user):
        """Handle contact support requests."""
        contact_info = session_model.get('contact_info', {})
        
        text = f"I'd be happy to connect you with our support team!\n\n"
        text += f"**{contact_info.get('company_name', 'Brownie Car Rentals')}**\n"
        text += f"📧 Email: {contact_info.get('email', 'info@browniecarrent.com')}\n"
        text += f"📞 Phone: {contact_info.get('phone', '+234 123 456 7890')}\n"
        text += f"🕐 Hours: {contact_info.get('hours', 'Mon-Fri 8am-8pm, Sat 9am-6pm, Sun 10am-4pm')}\n\n"
        text += "You can also continue chatting here and I'll do my best to help, or request to speak with a human agent."
        
        return {
            'text': text,
            'type': 'contact_info',
            'contact_info': contact_info,
            'quick_replies': [
                {'text': 'Human Agent', 'action': 'escalate_to_human'},
                {'text': 'Continue Here', 'action': 'continue_chat'}
            ]
        }
    
    def _handle_goodbye(self, context, entities, session_model, user):
        """Handle goodbye messages."""
        farewells = [
            "Thank you for choosing Brownie Car Rentals! Have a great day and safe travels!",
            "It was my pleasure helping you today. Drive safely and enjoy your rental!",
            "Thanks for chatting with me! Feel free to return anytime if you need assistance with your car rental."
        ]
        
        import random
        text = random.choice(farewells)
        
        # Clear conversation context after goodbye
        if context.session_id in self.contexts:
            del self.contexts[context.session_id]
        
        return {
            'text': text,
            'type': 'text',
            'actions': ['end_conversation']
        }
    
    def _handle_compare_cars(self, context, entities, session_model, user):
        """Handle car comparison requests."""
        if not context.selected_cars:
            return {
                'text': "To compare cars, please first select some cars from our inventory. I can show you available cars to choose from.",
                'type': 'text',
                'quick_replies': [
                    {'text': 'Browse Cars', 'action': 'browse_inventory'},
                    {'text': 'View Popular', 'action': 'view_popular_cars'}
                ]
            }
        
        if len(context.selected_cars) < 2:
            return {
                'text': f"You currently have {len(context.selected_cars)} car selected. Please select at least 2 cars to compare.",
                'type': 'text',
                'quick_replies': [
                    {'text': 'Add More Cars', 'action': 'browse_inventory'},
                    {'text': 'Clear Selection', 'action': 'clear_selection'}
                ]
            }
        
        # Generate comparison table
        fleet = session_model.get('fleet', [])
        comparison_cars = []
        
        for car_id in context.selected_cars:
            car = next((c for c in fleet if c['id'] == car_id), None)
            if car:
                comparison_cars.append(car)
        
        text = f"Here's a comparison of your {len(comparison_cars)} selected cars:\n\n"
        
        return {
            'text': text,
            'type': 'car_comparison',
            'comparison_cars': comparison_cars,
            'quick_replies': [
                {'text': 'Select One', 'action': 'choose_from_comparison'},
                {'text': 'Add More Cars', 'action': 'browse_inventory'},
                {'text': 'Book Selected', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_human_escalation(self, message, context):
        """Handle requests to escalate to human agent."""
        context.booking_state = 'escalated'
        
        text = "I'm connecting you with one of our human agents. Please hold on while I transfer you.\n\n"
        text += "In the meantime, here's a summary of our conversation:\n"
        
        # Create conversation summary
        if context.conversation_history:
            recent_messages = context.conversation_history[-5:]  # Last 5 messages
            for msg in recent_messages:
                if msg['type'] == 'user':
                    text += f"• You asked: {msg['content'][:100]}...\n"
        
        text += "\nA human agent will be with you shortly!"
        
        return {
            'text': text,
            'type': 'escalation',
            'actions': ['escalate_to_human'],
            'escalation_data': {
                'user_message': message,
                'context_summary': context.slots,
                'conversation_history': context.conversation_history[-10:],
                'booking_state': context.booking_state
            }
        }
    
    def _handle_fallback(self, message, context):
        """Handle fallback for unknown intents."""
        return self._handle_default(context, {}, {}, None)
    
    def _handle_availability(self, context, entities, session_model, user):
        """Handle availability inquiries."""
        fleet = session_model.get('fleet', [])
        available_cars = [car for car in fleet if car.get('availability') == 'available']
        
        if entities.get('car_names') or entities.get('car_categories'):
            # Filter by specific car or category
            filtered_cars = available_cars
            
            if entities.get('car_names'):
                car_name = entities['car_names'][0].lower()
                filtered_cars = [car for car in filtered_cars if car_name in car['name'].lower()]
            
            if entities.get('car_categories'):
                category = entities['car_categories'][0].lower()
                filtered_cars = [car for car in filtered_cars if category in car.get('category', '').lower()]
            
            if filtered_cars:
                text = f"Great news! We have {len(filtered_cars)} {entities.get('car_categories', [''])[0]} cars available:\n\n"
                for car in filtered_cars[:3]:
                    text += f"• **{car['name']}** - ${car['price_per_day']}/day\n"
            else:
                text = "I'm sorry, but the specific car you're looking for isn't currently available. However, I can show you similar alternatives!"
        else:
            text = f"We currently have **{len(available_cars)} cars available** for rent across all categories!\n\n"
            text += "Would you like to see available cars by category or view our complete fleet?"
        
        return {
            'text': text,
            'type': 'text',
            'quick_replies': [
                {'text': 'View Available Cars', 'action': 'browse_inventory'},
                {'text': 'Check Specific Car', 'action': 'browse_inventory'},
                {'text': 'Book Now', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_faq_general(self, context, entities, session_model, user):
        """Handle general FAQ inquiries."""
        text = "I'm here to help with all your car rental questions! Here are some popular topics:\n\n"
        text += "🚗 **Vehicle Information** - Browse our fleet, check availability\n"
        text += "💰 **Pricing & Payments** - Get quotes, payment options\n"
        text += "📋 **Policies** - Rental terms, insurance, age requirements\n"
        text += "📍 **Locations** - Pickup/drop-off locations and directions\n"
        text += "🎯 **Booking** - Make reservations, modify bookings\n\n"
        text += "What would you like to know more about?"
        
        return {
            'text': text,
            'type': 'faq',
            'quick_replies': [
                {'text': 'View Cars', 'action': 'browse_inventory'},
                {'text': 'Pricing Info', 'action': 'get_price'},
                {'text': 'Rental Policies', 'action': 'ask_policy'},
                {'text': 'Book Now', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_business_hours(self, context, entities, session_model, user):
        """Handle business hours inquiries."""
        contact_info = session_model.get('contact_info', {})
        hours = contact_info.get('hours', 'Monday to Friday: 8am - 8pm, Saturday: 9am - 6pm, Sunday: 10am - 4pm')
        
        text = f"📅 **Brownie Car Rental Business Hours:**\n\n"
        text += f"{hours}\n\n"
        text += "🌟 **Special Services:**\n"
        text += "• 24/7 Emergency roadside assistance\n"
        text += "• Airport pickup/drop-off available 24/7\n"
        text += "• Online booking available anytime\n\n"
        text += "Need help outside business hours? You can book online or contact our emergency line!"
        
        return {
            'text': text,
            'type': 'business_hours',
            'quick_replies': [
                {'text': 'Book Online Now', 'action': 'book_reserve'},
                {'text': 'Emergency Help', 'action': 'emergency_help'},
                {'text': 'Contact Info', 'action': 'contact_support'}
            ]
        }
    
    def _handle_age_requirement(self, context, entities, session_model, user):
        """Handle age requirement questions."""
        text = "👤 **Age Requirements for Car Rental:**\n\n"
        text += "✅ **Minimum Age:** 21 years old\n"
        text += "⚠️ **Young Driver Fee:** Applies to drivers aged 21-24 (additional $15/day)\n"
        text += "🔞 **No Upper Age Limit:** As long as you have a valid license\n\n"
        text += "📋 **What You'll Need:**\n"
        text += "• Valid driver's license (held for at least 1 year)\n"
        text += "• Government-issued photo ID\n"
        text += "• Credit card in your name\n\n"
        text += "💡 **Tip:** International visitors need an International Driving Permit (IDP)"
        
        return {
            'text': text,
            'type': 'age_requirements',
            'quick_replies': [
                {'text': 'What Documents?', 'action': 'ask_documents'},
                {'text': 'View Cars', 'action': 'browse_inventory'},
                {'text': 'Book Now', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_documents_required(self, context, entities, session_model, user):
        """Handle document requirements."""
        text = "📋 **Required Documents for Car Rental:**\n\n"
        text += "🆔 **Essential Documents:**\n"
        text += "• Valid driver's license (must be current)\n"
        text += "• Government-issued photo ID (passport or national ID)\n"
        text += "• Credit card in the primary driver's name\n\n"
        text += "🌍 **For International Visitors:**\n"
        text += "• International Driving Permit (IDP)\n"
        text += "• Passport\n"
        text += "• Home country driver's license\n\n"
        text += "💳 **Payment:**\n"
        text += "• Major credit card (Visa, MasterCard, Amex)\n"
        text += "• Debit cards accepted for some vehicles\n"
        text += "• Card must have sufficient credit for security deposit"
        
        return {
            'text': text,
            'type': 'documents',
            'quick_replies': [
                {'text': 'Age Requirements', 'action': 'ask_age_requirement'},
                {'text': 'Security Deposit?', 'action': 'ask_policy'},
                {'text': 'Ready to Book', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_insurance_info(self, context, entities, session_model, user):
        """Handle insurance information."""
        text = "🛡️ **Insurance Coverage Options:**\n\n"
        text += "✅ **Included in Every Rental:**\n"
        text += "• Basic liability insurance\n"
        text += "• Collision damage waiver\n"
        text += "• Theft protection\n\n"
        text += "⭐ **Premium Coverage Available:**\n"
        text += "• Personal accident insurance (+$15/day)\n"
        text += "• Zero deductible option (+$25/day)\n"
        text += "• Roadside assistance premium (+$10/day)\n\n"
        text += "💡 **What's Covered:**\n"
        text += "• Damage to the rental vehicle\n"
        text += "• Third-party liability\n"
        text += "• Emergency roadside assistance\n\n"
        text += "❓ Questions about coverage? Our team can help you choose the right protection!"
        
        return {
            'text': text,
            'type': 'insurance',
            'quick_replies': [
                {'text': 'What if accident?', 'action': 'ask_policy'},
                {'text': 'Rental Policies', 'action': 'ask_policy'},
                {'text': 'Book with Insurance', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_fuel_policy(self, context, entities, session_model, user):
        """Handle fuel policy questions."""
        text = "⛽ **Fuel Policy - Full to Full:**\n\n"
        text += "🔄 **How It Works:**\n"
        text += "• Pick up with a full tank\n"
        text += "• Return with a full tank\n"
        text += "• No fuel charges when returned full\n\n"
        text += "💰 **If Not Returned Full:**\n"
        text += "• Fuel charge: Market rate + $5 service fee per gallon\n"
        text += "• We'll refuel for you at local rates\n\n"
        text += "🎯 **Pro Tips:**\n"
        text += "• Fill up at nearby gas stations (usually cheaper)\n"
        text += "• Keep your fuel receipt\n"
        text += "• Check fuel gauge before driving off\n\n"
        text += "📍 Need help finding nearby gas stations? Just ask!"
        
        return {
            'text': text,
            'type': 'fuel_policy',
            'quick_replies': [
                {'text': 'Other Policies', 'action': 'ask_policy'},
                {'text': 'Find Locations', 'action': 'ask_directions'},
                {'text': 'Book Now', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_mileage_policy(self, context, entities, session_model, user):
        """Handle mileage policy questions."""
        text = "🛣️ **Mileage Policy - Unlimited Miles!**\n\n"
        text += "✅ **What You Get:**\n"
        text += "• Unlimited mileage on all rentals\n"
        text += "• No distance restrictions\n"
        text += "• Perfect for road trips and long journeys\n\n"
        text += "🚗 **Freedom to Explore:**\n"
        text += "• Drive across the country if you want!\n"
        text += "• No surprise charges for extra miles\n"
        text += "• One flat daily rate covers everything\n\n"
        text += "📍 **Popular Road Trip Destinations:**\n"
        text += "• Lagos to Abuja (475 miles)\n"
        text += "• Cross-country adventures\n"
        text += "• Weekend getaways anywhere\n\n"
        text += "Ready to hit the road? 🌟"
        
        return {
            'text': text,
            'type': 'mileage_policy',
            'quick_replies': [
                {'text': 'Plan Road Trip', 'action': 'book_reserve'},
                {'text': 'View Long-term Cars', 'action': 'browse_inventory'},
                {'text': 'Other Policies', 'action': 'ask_policy'}
            ]
        }
    
    def _handle_payment_options(self, context, entities, session_model, user):
        """Handle payment options questions."""
        text = "💳 **Flexible Payment Options:**\n\n"
        text += "🌟 **Accepted Payment Methods:**\n"
        text += "• Major credit cards (Visa, MasterCard, Amex)\n"
        text += "• Paystack (instant online payment)\n"
        text += "• Bank transfers\n"
        text += "• Pay later options for qualified customers\n\n"
        text += "💰 **Payment Options:**\n"
        text += "• **Pay Online:** Secure, instant booking\n"
        text += "• **Pay at Pickup:** Cash or card accepted\n"
        text += "• **Corporate Billing:** For business accounts\n\n"
        text += "🔒 **Security Deposit:**\n"
        text += "• $100-200 depending on vehicle class\n"
        text += "• Held on credit card, released after return\n"
        text += "• No deposit with some premium packages\n\n"
        text += "Questions about payment? I can help! 💪"
        
        return {
            'text': text,
            'type': 'payment_options',
            'quick_replies': [
                {'text': 'Book & Pay Online', 'action': 'book_reserve'},
                {'text': 'Corporate Rates', 'action': 'ask_discount'},
                {'text': 'Security Deposit?', 'action': 'ask_policy'}
            ]
        }
    
    def _handle_discounts_promos(self, context, entities, session_model, user):
        """Handle discount and promo inquiries."""
        text = "🎉 **Current Deals & Discounts:**\n\n"
        text += "💼 **Corporate Discounts:**\n"
        text += "• 15% off for registered businesses\n"
        text += "• Volume discounts for fleet bookings\n"
        text += "• Special rates for long-term rentals\n\n"
        text += "📚 **Student Discounts:**\n"
        text += "• 10% off with valid student ID\n"
        text += "• Available on compact and economy cars\n\n"
        text += "⏰ **Time-Based Savings:**\n"
        text += "• Weekly rentals: 15% discount\n"
        text += "• Monthly rentals: 25% discount\n"
        text += "• Off-peak season: Up to 20% off\n\n"
        text += "🎁 **Loyalty Program:**\n"
        text += "• Earn points with every rental\n"
        text += "• Free upgrades for VIP members\n\n"
        text += "💡 **Pro Tip:** Book online for best rates!"
        
        return {
            'text': text,
            'type': 'discounts',
            'quick_replies': [
                {'text': 'Apply Discount', 'action': 'book_reserve'},
                {'text': 'Corporate Rates', 'action': 'contact_support'},
                {'text': 'Student Discount', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_extras_addons(self, context, entities, session_model, user):
        """Handle extras and add-ons inquiries."""
        booking_info = session_model.get('booking_info', {})
        extras = booking_info.get('extras', [])
        
        text = "🎯 **Available Extras & Add-ons:**\n\n"
        
        if extras:
            for extra in extras:
                text += f"• **{extra['name']}** - ${extra['price_per_day']}/day\n"
        else:
            text += "🧭 **Navigation & Tech:**\n"
            text += "• GPS Navigation - $5/day\n"
            text += "• WiFi Hotspot - $6/day\n"
            text += "• Phone chargers & USB ports\n\n"
            text += "👶 **Family Options:**\n"
            text += "• Child car seats - $8/day\n"
            text += "• Booster seats - $6/day\n"
            text += "• Baby stroller rentals\n\n"
            text += "🚗 **Convenience:**\n"
            text += "• Additional driver - $10/day\n"
            text += "• Roadside assistance premium - $7.50/day\n"
            text += "• Ski racks & bike racks\n"
        
        text += "\n✨ **Free Inclusions:**\n"
        text += "• Basic roadside assistance\n"
        text += "• Unlimited mileage\n"
        text += "• 24/7 customer support\n\n"
        text += "Want to add any extras to your booking?"
        
        return {
            'text': text,
            'type': 'extras',
            'quick_replies': [
                {'text': 'Book with Extras', 'action': 'book_reserve'},
                {'text': 'Just Basic Rental', 'action': 'book_reserve'},
                {'text': 'Family Packages', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_emergency_help(self, context, entities, session_model, user):
        """Handle emergency assistance requests."""
        text = "🚨 **Emergency Assistance Available 24/7**\n\n"
        text += "📞 **Immediate Help:**\n"
        text += "• **Emergency Hotline:** +234 123 456 7890\n"
        text += "• **Roadside Assistance:** Free with all rentals\n"
        text += "• **Average Response Time:** 30 minutes\n\n"
        text += "🛠️ **We Can Help With:**\n"
        text += "• Flat tire changes\n"
        text += "• Dead battery jump-starts\n"
        text += "• Lockout assistance\n"
        text += "• Fuel delivery (minimum charge applies)\n"
        text += "• Towing to nearest service center\n\n"
        text += "🚗 **In Case of Accident:**\n"
        text += "1. Ensure everyone's safety first\n"
        text += "2. Call emergency services if needed\n"
        text += "3. Contact our 24/7 hotline immediately\n"
        text += "4. Don't admit fault or sign any documents\n\n"
        text += "Need help right now? Call us immediately! 🆘"
        
        return {
            'text': text,
            'type': 'emergency',
            'quick_replies': [
                {'text': 'Call Emergency', 'action': 'contact_support'},
                {'text': 'Insurance Info', 'action': 'ask_insurance'},
                {'text': 'Report Accident', 'action': 'escalate_to_human'}
            ]
        }
    
    def _handle_compliment(self, context, entities, session_model, user):
        """Handle compliments and positive feedback."""
        responses = [
            "Thank you so much! 😊 I'm here to make your car rental experience smooth and enjoyable!",
            "That's wonderful to hear! 🌟 I'm glad I could help you today!",
            "Your kind words mean a lot! 💪 I'm always here when you need assistance with car rentals!",
            "Thanks for the positive feedback! 🎉 Is there anything else I can help you with today?"
        ]
        
        import random
        text = random.choice(responses)
        text += "\n\nHow else can I assist you with your car rental needs?"
        
        return {
            'text': text,
            'type': 'compliment_response',
            'quick_replies': [
                {'text': 'Browse Cars', 'action': 'browse_inventory'},
                {'text': 'Book Now', 'action': 'book_reserve'},
                {'text': 'Share Feedback', 'action': 'contact_support'}
            ]
        }
    
    def _handle_complaint(self, context, entities, session_model, user):
        """Handle complaints and negative feedback."""
        text = "I sincerely apologize that you're not having a good experience. 😔\n\n"
        text += "Your feedback is extremely valuable to us, and I want to make this right immediately.\n\n"
        text += "🎯 **How I Can Help:**\n"
        text += "• Connect you with a supervisor right now\n"
        text += "• Document your concerns for immediate review\n"
        text += "• Provide alternative solutions\n"
        text += "• Ensure your issue gets priority attention\n\n"
        text += "Would you like me to escalate this to a human agent who can provide personalized assistance?"
        
        # Update context to mark as complaint for prioritization
        context.booking_state = 'complaint_logged'
        
        return {
            'text': text,
            'type': 'complaint_response',
            'quick_replies': [
                {'text': 'Speak to Manager', 'action': 'escalate_to_human'},
                {'text': 'Explain Issue', 'action': 'contact_support'},
                {'text': 'Alternative Solution', 'action': 'browse_inventory'}
            ]
        }
    
    def _handle_change_booking(self, context, entities, session_model, user):
        """Handle booking modification requests."""
        text = "✏️ **Modify Your Booking**\n\n"
        text += "I can help you change your reservation! Here's what you can modify:\n\n"
        text += "📅 **Date Changes:**\n"
        text += "• Pickup/drop-off dates\n"
        text += "• Rental duration\n"
        text += "• Free changes up to 24 hours before pickup\n\n"
        text += "📍 **Location Changes:**\n"
        text += "• Pickup location\n"
        text += "• Drop-off location\n"
        text += "• Subject to availability\n\n"
        text += "🚗 **Vehicle Changes:**\n"
        text += "• Upgrade or downgrade\n"
        text += "• Different car category\n"
        text += "• Add/remove extras\n\n"
        text += "💡 **To modify your booking, I'll need:**\n"
        text += "• Your booking confirmation number\n"
        text += "• Details of changes you want to make\n\n"
        text += "Ready to help you make those changes! 🎯"
        
        return {
            'text': text,
            'type': 'change_booking',
            'quick_replies': [
                {'text': 'Speak to Agent', 'action': 'escalate_to_human'},
                {'text': 'Contact Support', 'action': 'contact_support'},
                {'text': 'New Booking Instead', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_cancel_booking(self, context, entities, session_model, user):
        """Handle booking cancellation requests."""
        text = "❌ **Booking Cancellation**\n\n"
        text += "I understand you need to cancel your reservation. Here's our cancellation policy:\n\n"
        text += "✅ **Free Cancellation:**\n"
        text += "• Up to 24 hours before pickup: No charge\n"
        text += "• Easy online cancellation process\n"
        text += "• Instant refund processing\n\n"
        text += "⚠️ **Last-Minute Cancellations:**\n"
        text += "• Less than 24 hours: 50% of daily rate\n"
        text += "• No-show: Full day charge\n"
        text += "• Emergency exceptions considered\n\n"
        text += "💰 **Refund Process:**\n"
        text += "• Refunds processed within 3-5 business days\n"
        text += "• Returned to original payment method\n"
        text += "• Confirmation email sent\n\n"
        text += "To proceed with cancellation, I'll connect you with our support team who can process this immediately."
        
        return {
            'text': text,
            'type': 'cancel_booking',
            'quick_replies': [
                {'text': 'Cancel My Booking', 'action': 'escalate_to_human'},
                {'text': 'Modify Instead', 'action': 'change_booking'},
                {'text': 'Keep Booking', 'action': 'browse_inventory'}
            ]
        }
    
    def _handle_directions(self, context, entities, session_model, user):
        """Handle location and directions requests."""
        locations = session_model.get('locations', [])
        
        text = "📍 **Our Convenient Locations:**\n\n"
        
        for location in locations:
            text += f"**{location['name']}**\n"
            text += f"📧 {location['address']}\n"
            text += f"⏰ {location['hours']}\n"
            text += f"📞 {location['phone']}\n\n"
        
        text += "🗺️ **Getting Directions:**\n"
        text += "• Use GPS coordinates provided\n"
        text += "• Public transportation info available\n"
        text += "• Free parking at most locations\n\n"
        text += "🚖 **Airport Shuttle:**\n"
        text += "• Free shuttle service from terminals\n"
        text += "• Look for Brownie Car Rental signs\n"
        text += "• Call ahead for pickup coordination\n\n"
        text += "Need specific directions to any location?"
        
        return {
            'text': text,
            'type': 'directions',
            'quick_replies': [
                {'text': 'Airport Location', 'action': 'contact_support'},
                {'text': 'Downtown Office', 'action': 'contact_support'},
                {'text': 'Book Pickup', 'action': 'book_reserve'}
            ]
        }
    
    def _handle_request_images(self, context, entities, session_model, user):
        """Handle requests for car images."""
        text = "📸 **Car Photos & Images**\n\n"
        text += "I'd love to show you photos of our amazing fleet! Here's how you can view them:\n\n"
        text += "🖼️ **High-Quality Photos:**\n"
        text += "• Interior and exterior shots\n"
        text += "• Multiple angles of each vehicle\n"
        text += "• Real photos of actual rental cars\n\n"
        text += "🔍 **How to View:**\n"
        text += "• Browse our fleet to see car images\n"
        text += "• Click on any car for detailed photo gallery\n"
        text += "• 360° view available for select vehicles\n\n"
        text += "📱 **Mobile App:**\n"
        text += "• Download for better photo viewing\n"
        text += "• Augmented reality features\n"
        text += "• Compare cars side-by-side\n\n"
        text += "Want to see photos of a specific car type?"
        
        return {
            'text': text,
            'type': 'images',
            'quick_replies': [
                {'text': 'Browse Fleet Photos', 'action': 'browse_inventory'},
                {'text': 'Luxury Car Photos', 'action': 'browse_inventory'},
                {'text': 'SUV Gallery', 'action': 'browse_inventory'}
            ]
        }
    
    def _handle_default(self, context, entities, session_model, user):
        """Handle unrecognized intents."""
        fallback_responses = [
            "I'm not sure I understand that completely. Can you please rephrase your question?",
            "I didn't quite catch that. Could you clarify what you're looking for?",
            "I'm still learning! Can you ask that in a different way?"
        ]
        
        import random
        text = random.choice(fallback_responses)
        text += "\n\n🎯 **I can help you with:**\n"
        text += "• 🚗 Browsing our car inventory\n"
        text += "• 💰 Getting price quotes and deals\n"
        text += "• 📅 Making reservations\n"
        text += "• 📋 Answering policy questions\n"
        text += "• 📍 Location and directions\n"
        text += "• 🆘 Emergency assistance\n\n"
        text += "What would you like to know about?"
        
        return {
            'text': text,
            'type': 'text',
            'quick_replies': [
                {'text': 'Browse Cars', 'action': 'browse_inventory'},
                {'text': 'Get Prices', 'action': 'get_price'},
                {'text': 'Book Car', 'action': 'book_reserve'},
                {'text': 'Human Agent', 'action': 'escalate_to_human'}
            ]
        }


    def _extract_user_info_from_entities(self, user_context, entities):
        """Extract and update user information from NLU entities."""
        # Extract name if mentioned
        if 'names' in entities and entities['names']:
            name = entities['names'][0]
            user_context_service.update_context_with_info(user_context, 'name', name)
        
        # Extract email if mentioned
        if 'emails' in entities and entities['emails']:
            email = entities['emails'][0]
            user_context_service.update_context_with_info(user_context, 'email', email)
        
        # Extract phone if mentioned
        if 'phones' in entities and entities['phones']:
            phone = entities['phones'][0]
            user_context_service.update_context_with_info(user_context, 'phone', phone)
        
        # Track location interests
        if 'locations' in entities and entities['locations']:
            for location in entities['locations']:
                user_context_service.update_behavioral_data(
                    user_context, 'location_interest', {'location': location}
                )
        
        # Track car category interests
        if 'car_categories' in entities and entities['car_categories']:
            for category in entities['car_categories']:
                user_context_service.update_behavioral_data(
                    user_context, 'car_interest', {'category': category}
                )
    
    def _create_response_with_context(self, text, user_context, context, session_id, 
                                    response_type, quick_replies=None, actions=None):
        """Create a response with enhanced user context."""
        response = {
            'text': text,
            'type': response_type,
            'session_id': session_id,
            'timestamp': timezone.now().isoformat(),
            'booking_state': context.booking_state,
            'user_context': {
                'user_type': user_context.user_type,
                'is_returning': user_context.is_returning,
                'interaction_count': user_context.interaction_count,
                'avatar_info': user_context_service.get_avatar_info(user_context)
            }
        }
        
        if quick_replies:
            response['quick_replies'] = quick_replies
        if actions:
            response['actions'] = actions
        
        return response
    
    def _enhance_response_with_context(self, response_data, user_context, context):
        """Enhance response with user context information."""
        # Add user context to response
        response_data['user_context'] = {
            'user_type': user_context.user_type,
            'is_returning': user_context.is_returning,
            'interaction_count': user_context.interaction_count,
            'avatar_info': user_context_service.get_avatar_info(user_context),
            'display_name': user_context_service._get_display_name(user_context)
        }
        
        # Enhance quick replies with personalization if not already present
        if 'quick_replies' not in response_data or not response_data['quick_replies']:
            suggestions = user_context_service.get_personalized_suggestions(user_context)
            quick_replies = []
            
            for suggestion in suggestions[:2]:  # Max 2 personalized suggestions
                if 'Browse' in suggestion:
                    action = 'browse_inventory'
                elif 'Price' in suggestion or 'Quote' in suggestion:
                    action = 'get_price'
                elif 'Book' in suggestion:
                    action = 'book_reserve'
                else:
                    action = 'browse_inventory'
                    
                quick_replies.append({
                    'text': suggestion,
                    'action': action
                })
            
            if quick_replies:
                response_data['quick_replies'] = quick_replies
        
        return response_data


# Initialize the AI assistant service
ai_assistant_service = AIAssistantService()
