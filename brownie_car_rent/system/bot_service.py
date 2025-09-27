import re
import random
from django.utils import timezone
from .models import ChatBotResponse, ChatRoom, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatBotService:
    """Service class for handling automated bot responses"""
    
    def __init__(self):
        self.default_responses = {
            'greeting': [
                "Hello! I'm your virtual assistant. How can I help you today?",
                "Hi there! Welcome to our car rental service. What can I assist you with?",
                "Greetings! I'm here to help you with your car rental needs. What would you like to know?",
            ],
            'booking_inquiry': [
                "I'd be happy to help you with booking information! You can browse available cars and make a reservation through our booking system.",
                "For booking inquiries, I can help you understand our process. Would you like to know about available cars or how to make a reservation?",
            ],
            'pricing': [
                "Our pricing depends on the car type and rental duration. You can check specific prices on our booking page.",
                "Car rental prices vary by vehicle type and rental period. Visit our booking section to see current rates.",
            ],
            'availability': [
                "To check car availability, please visit our booking page where you can see all available vehicles for your desired dates.",
                "Car availability changes in real-time. Check our booking system for the most current availability.",
            ],
            'contact': [
                "You can reach our support team through this chat or visit our contact page for more information.",
                "Our support team is available to help! You can continue chatting here or request to speak with a human agent.",
            ],
            'support': [
                "I'm here to help! What specific issue are you experiencing? If you need human assistance, I can connect you with a support agent.",
                "What can I help you with today? For complex issues, I can transfer you to one of our human support agents.",
            ],
            'escalation': [
                "I understand you'd like to speak with a human agent. Let me connect you with our support team.",
                "No problem! I'm connecting you with a human support agent who can provide more detailed assistance.",
            ],
            'goodbye': [
                "Thank you for contacting us! Have a great day and safe travels!",
                "Goodbye! Feel free to reach out anytime if you need assistance with your car rental needs.",
            ],
            'default': [
                "I'm not sure I understand that. Can you please rephrase your question?",
                "I didn't quite catch that. Could you please clarify what you're looking for?",
                "I'm still learning! Can you ask that in a different way? Or would you like me to connect you with a human agent?",
            ]
        }
    
    def get_intent_from_message(self, message):
        """Determine the intent based on message content"""
        message_lower = message.lower()
        
        # Check for greeting patterns
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon']):
            return 'greeting'
        
        # Check for booking-related patterns
        if any(word in message_lower for word in ['book', 'reserve', 'reservation', 'rent', 'rental']):
            return 'booking_inquiry'
        
        # Check for pricing patterns
        if any(word in message_lower for word in ['price', 'cost', 'rate', 'fee', 'charge', 'expensive', 'cheap']):
            return 'pricing'
        
        # Check for availability patterns
        if any(word in message_lower for word in ['available', 'availability', 'free', 'vacant', 'cars available']):
            return 'availability'
        
        # Check for contact patterns
        if any(word in message_lower for word in ['contact', 'phone', 'email', 'address', 'location']):
            return 'contact'
        
        # Check for support patterns
        if any(word in message_lower for word in ['help', 'problem', 'issue', 'trouble', 'support', 'assistance']):
            return 'support'
        
        # Check for escalation patterns
        if any(word in message_lower for word in ['human', 'agent', 'person', 'staff', 'representative', 'transfer']):
            return 'escalation'
        
        # Check for goodbye patterns
        if any(word in message_lower for word in ['bye', 'goodbye', 'thanks', 'thank you', 'done', 'finish']):
            return 'goodbye'
        
        return 'default'
    
    def get_bot_response(self, message, room):
        """Generate bot response based on message content"""
        intent = self.get_intent_from_message(message)
        
        # Try to get a custom response from the database
        try:
            bot_responses = ChatBotResponse.objects.filter(
                intent=intent,
                is_active=True
            ).order_by('-priority')
            
            for bot_response in bot_responses:
                keywords = bot_response.get_keywords_list()
                if any(keyword in message.lower() for keyword in keywords):
                    return bot_response.response_text, intent
        except:
            pass
        
        # Fall back to default responses
        responses = self.default_responses.get(intent, self.default_responses['default'])
        response_text = random.choice(responses)
        
        return response_text, intent
    
    def should_escalate(self, message, room):
        """Determine if the conversation should be escalated to human agent"""
        message_lower = message.lower()
        
        # Escalation keywords
        escalation_keywords = [
            'human', 'agent', 'person', 'staff', 'representative', 
            'transfer', 'speak to someone', 'talk to person', 'real person'
        ]
        
        # Check if user explicitly requests human help
        if any(keyword in message_lower for keyword in escalation_keywords):
            return True
        
        # Check if this is the user's nth message without resolution
        user_messages = ChatMessage.objects.filter(
            room=room,
            sender_type='user'
        ).count()
        
        if user_messages >= 5:  # After 5 user messages, suggest escalation
            return True
        
        return False
    
    def create_bot_message(self, room, response_text, intent='default'):
        """Create a bot message in the database"""
        return ChatMessage.objects.create(
            room=room,
            sender_type='bot',
            content=response_text,
            metadata={'intent': intent}
        )
    
    def process_user_message(self, room, user_message):
        """Process a user message and generate appropriate bot response"""
        # Check if escalation is needed
        if self.should_escalate(user_message, room):
            if room.status == 'bot_only':
                # Update room status to request escalation
                room.status = 'pending_escalation'
                room.save()
                
                escalation_message = (
                    "I understand you'd like to speak with a human agent. "
                    "I'm notifying our support team right now. Someone will be with you shortly!"
                )
                
                bot_message = self.create_bot_message(room, escalation_message, 'escalation')
                
                # Create system message for agents
                system_message = ChatMessage.objects.create(
                    room=room,
                    sender_type='system',
                    content=f"User has requested human assistance. Room {room.room_id} is waiting for agent assignment.",
                    metadata={'action': 'escalation_request'}
                )
                
                return bot_message, True  # True indicates escalation occurred
        
        # Generate normal bot response
        response_text, intent = self.get_bot_response(user_message, room)
        bot_message = self.create_bot_message(room, response_text, intent)
        
        return bot_message, False  # False indicates no escalation
    
    def send_welcome_message(self, room):
        """Send initial welcome message when user joins chat"""
        welcome_text = (
            "Hello! I'm your virtual assistant for car rentals. "
            "I can help you with:\n"
            "• Car availability and booking\n"
            "• Pricing information\n"
            "• General support questions\n\n"
            "If you need to speak with a human agent, just let me know! "
            "How can I assist you today?"
        )
        
        return self.create_bot_message(room, welcome_text, 'greeting')


# Initialize bot service
bot_service = ChatBotService()
