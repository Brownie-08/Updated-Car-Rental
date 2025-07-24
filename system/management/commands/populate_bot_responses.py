from django.core.management.base import BaseCommand
from system.models import ChatBotResponse


class Command(BaseCommand):
    help = 'Populate initial bot responses for the chat system'

    def handle(self, *args, **options):
        self.stdout.write('Populating bot responses...')

        # Clear existing responses
        ChatBotResponse.objects.all().delete()

        # Create default bot responses
        responses = [
            {
                'intent': 'greeting',
                'keywords': 'hello, hi, hey, greetings, good morning, good afternoon, good evening',
                'response_text': 'Hello! Welcome to our car rental service. I\'m here to help you with your car rental needs. What can I assist you with today?',
                'priority': 10,
                'is_active': True
            },
            {
                'intent': 'booking_inquiry',
                'keywords': 'book, reserve, reservation, rent, rental, hire, available cars',
                'response_text': 'I\'d be happy to help you with booking a car! You can browse our available vehicles and make a reservation through our booking system. Would you like me to guide you through the process?',
                'priority': 9,
                'is_active': True
            },
            {
                'intent': 'pricing',
                'keywords': 'price, cost, rate, fee, charge, expensive, cheap, how much, pricing',
                'response_text': 'Our car rental prices vary depending on the vehicle type, rental duration, and season. You can view specific pricing for each car on our booking page. Would you like me to help you find pricing for a specific vehicle?',
                'priority': 8,
                'is_active': True
            },
            {
                'intent': 'availability',
                'keywords': 'available, availability, free, vacant, cars available, when available',
                'response_text': 'Car availability changes in real-time based on bookings. You can check current availability by visiting our booking page and selecting your desired dates. Is there a specific date range you\'re looking for?',
                'priority': 8,
                'is_active': True
            },
            {
                'intent': 'contact',
                'keywords': 'contact, phone, email, address, location, office, reach, call',
                'response_text': 'You can reach our support team through this chat or visit our contact page for more information. If you need immediate assistance, I can connect you with a human agent. How can I help you today?',
                'priority': 7,
                'is_active': True
            },
            {
                'intent': 'support',
                'keywords': 'help, problem, issue, trouble, support, assistance, stuck, error',
                'response_text': 'I\'m here to help! What specific issue are you experiencing? I can assist with booking questions, account issues, or general inquiries. For complex problems, I can connect you with one of our human support agents.',
                'priority': 9,
                'is_active': True
            },
            {
                'intent': 'escalation',
                'keywords': 'human, agent, person, staff, representative, transfer, speak to someone, talk to person, real person',
                'response_text': 'I understand you\'d like to speak with a human agent. Let me connect you with our support team right away. Please hold on while I transfer you to one of our agents.',
                'priority': 10,
                'is_active': True
            },
            {
                'intent': 'goodbye',
                'keywords': 'bye, goodbye, thanks, thank you, done, finish, end, close',
                'response_text': 'Thank you for choosing our car rental service! Have a great day and safe travels. Feel free to reach out anytime if you need assistance with your car rental needs.',
                'priority': 6,
                'is_active': True
            },
            {
                'intent': 'default',
                'keywords': 'default, fallback, unknown',
                'response_text': 'I\'m not sure I understand that completely. Could you please rephrase your question? I can help you with car bookings, pricing, availability, and general support. Or would you like me to connect you with a human agent?',
                'priority': 1,
                'is_active': True
            },
            # Car-specific responses
            {
                'intent': 'booking_inquiry',
                'keywords': 'sedan, suv, compact, luxury, economy, sports car, truck, van',
                'response_text': 'We have a variety of vehicle types available including sedans, SUVs, compact cars, and luxury vehicles. You can view all available cars with their specifications and pricing on our booking page. Would you like me to help you find a specific type of vehicle?',
                'priority': 8,
                'is_active': True
            },
            {
                'intent': 'booking_inquiry',
                'keywords': 'insurance, coverage, damage, accident, liability',
                'response_text': 'We offer comprehensive insurance coverage for all our rental vehicles. This includes collision coverage, liability insurance, and theft protection. You can review the full insurance details during the booking process. Would you like more information about our insurance options?',
                'priority': 8,
                'is_active': True
            },
            {
                'intent': 'booking_inquiry',
                'keywords': 'driver license, age, requirements, documents, id',
                'response_text': 'To rent a car, you need to be at least 21 years old with a valid driver\'s license. You\'ll also need a credit card for the security deposit. International customers need a valid passport and international driving permit. Do you have any specific questions about our rental requirements?',
                'priority': 8,
                'is_active': True
            },
            {
                'intent': 'booking_inquiry',
                'keywords': 'cancel, cancellation, refund, change, modify, reschedule',
                'response_text': 'You can cancel or modify your reservation through your account dashboard or by contacting our support team. Cancellation policies vary depending on when you cancel and the type of booking. Would you like me to help you with a specific reservation or connect you with an agent?',
                'priority': 8,
                'is_active': True
            },
        ]

        created_count = 0
        for response_data in responses:
            response, created = ChatBotResponse.objects.get_or_create(
                intent=response_data['intent'],
                keywords=response_data['keywords'],
                defaults={
                    'response_text': response_data['response_text'],
                    'priority': response_data['priority'],
                    'is_active': response_data['is_active']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created: {response.intent} - {response.response_text[:50]}...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {created_count} bot responses')
        )
