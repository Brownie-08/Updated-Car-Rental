"""
API Views for AI Chat Assistant.
Handles REST endpoints for chat sessions, messages, and booking operations.
"""
import json
import uuid
from datetime import datetime, date
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ChatRoom, ChatMessage, Car, Order
from .session_model_service import session_model_service
from .ai_assistant_service import ai_assistant_service
from .payment_services import PaystackPaymentService, StripePaymentService
from .currency_utils import convert_usd_to_ngn, convert_usd_to_kobo, format_currency_display

User = get_user_model()


class JSONResponseMixin:
    """Mixin to add JSON response functionality."""
    
    def json_response(self, data, status=200):
        return JsonResponse(data, status=status, json_dumps_params={'indent': 2})
    
    def error_response(self, message, status=400, error_code=None):
        return JsonResponse({
            'error': True,
            'message': message,
            'error_code': error_code
        }, status=status)


@csrf_exempt
@require_http_methods(["GET"])
def create_chat_session(request):
    """
    Create or retrieve a chat session.
    Returns session model with car data.
    """
    try:
        # Generate session ID
        session_id = request.GET.get('session_id', str(uuid.uuid4()))
        
        # Get or create chat room
        user = request.user if request.user.is_authenticated else None
        
        # Try to get existing room for authenticated users
        chat_room = None
        if user:
            chat_room = ChatRoom.objects.filter(
                user=user,
                status__in=['bot_only', 'active', 'pending_escalation']
            ).first()
        
        if not chat_room:
            chat_room = ChatRoom.objects.create(
                room_id=session_id,
                user=user,
                status='bot_only',
                is_bot_handled=True,
                user_ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        else:
            session_id = chat_room.room_id
        
        # Get session model with site data
        session_model = session_model_service.get_session_model(session_id)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'room_id': chat_room.room_id,
            'session_model': session_model,
            'user_authenticated': user is not None,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to create chat session: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    Send a message to the AI assistant and get a response.
    Handles the main chat interaction.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        action = data.get('action')  # For quick reply actions
        action_data = data.get('action_data', {})
        
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'Session ID is required'
            }, status=400)
        
        if not message and not action:
            return JsonResponse({
                'error': True,
                'message': 'Message or action is required'
            }, status=400)
        
        # Get or create chat room
        chat_room = ChatRoom.objects.filter(room_id=session_id).first()
        if not chat_room:
            user = request.user if request.user.is_authenticated else None
            chat_room = ChatRoom.objects.create(
                room_id=session_id,
                user=user,
                status='bot_only',
                is_bot_handled=True
            )
        
        # Handle quick reply actions
        if action:
            message = _handle_action(action, action_data, session_id)
            if not message:
                return JsonResponse({
                    'error': True,
                    'message': 'Invalid action'
                }, status=400)
        
        # Save user message
        user_message = ChatMessage.objects.create(
            room=chat_room,
            sender_type='user',
            content=message
        )
        
        # Process message with AI assistant
        user = request.user if request.user.is_authenticated else None
        response_data = ai_assistant_service.process_message(
            session_id, message, user, request
        )
        
        # Save assistant response
        assistant_message = ChatMessage.objects.create(
            room=chat_room,
            sender_type='bot',
            content=response_data.get('text', ''),
            metadata=response_data
        )
        
        # Update room status
        chat_room.updated_at = timezone.now()
        chat_room.save(update_fields=['updated_at'])
        
        # Return response
        return JsonResponse({
            'success': True,
            'message_id': assistant_message.id,
            'response': response_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': True,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to process message: {str(e)}'
        }, status=500)


def _handle_action(action, action_data, session_id):
    """Handle quick reply actions and convert them to natural language messages."""
    context = ai_assistant_service.get_context(session_id)
    
    action_handlers = {
        'browse_inventory': lambda: 'Show me available cars',
        'get_price': lambda: 'What are your car prices?',
        'book_reserve': lambda: 'I want to book a car',
        'contact_support': lambda: 'I need to contact support',
        'select_car': lambda: f'I want to select car {action_data.get("car_id")}',
        'select_car_for_booking': lambda: _handle_car_selection(action_data, context),
        'select_location': lambda: _handle_location_selection(action_data, context),
        'quick_date': lambda: _handle_quick_date(action_data, context),
        'confirm_booking': lambda: 'I want to confirm my booking',
        'escalate_to_human': lambda: 'I want to speak with a human agent'
    }
    
    handler = action_handlers.get(action)
    if handler:
        try:
            return handler()
        except Exception as e:
            print(f"Error handling action {action}: {e}")
            return None
    
    return None


def _handle_car_selection(action_data, context):
    """Handle car selection action."""
    car_id = action_data.get('car_id')
    if car_id:
        context.update_slots({'selected_car_id': car_id})
        return f'I want to select car ID {car_id} for booking'
    return None


def _handle_location_selection(action_data, context):
    """Handle location selection action."""
    location = action_data.get('location')
    if location:
        context.update_slots({'pickup_location': location})
        return f'I want to pick up at {location}'
    return None


def _handle_quick_date(action_data, context):
    """Handle quick date selection."""
    date_option = action_data.get('dates')
    today = timezone.now().date()
    
    if date_option == 'tomorrow_3days':
        pickup_date = today + timezone.timedelta(days=1)
        dropoff_date = pickup_date + timezone.timedelta(days=3)
        context.update_slots({
            'pickup_date': pickup_date,
            'dropoff_date': dropoff_date
        })
        return f'I want to pick up tomorrow ({pickup_date}) and return in 3 days ({dropoff_date})'
    elif date_option == 'nextweek_5days':
        pickup_date = today + timezone.timedelta(days=7)
        dropoff_date = pickup_date + timezone.timedelta(days=5)
        context.update_slots({
            'pickup_date': pickup_date,
            'dropoff_date': dropoff_date
        })
        return f'I want to pick up next week ({pickup_date}) for 5 days until {dropoff_date}'
    
    return None


@csrf_exempt
@require_http_methods(["POST"])
def preview_booking(request):
    """
    Preview a booking with pricing calculation.
    Used during the booking flow to show pricing before confirmation.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'Session ID is required'
            }, status=400)
        
        # Get conversation context
        context = ai_assistant_service.get_context(session_id)
        
        # Get required booking information from context
        selected_car_id = context.get_slot('selected_car_id')
        pickup_date = context.get_slot('pickup_date')
        dropoff_date = context.get_slot('dropoff_date')
        pickup_location = context.get_slot('pickup_location')
        
        if not all([selected_car_id, pickup_date, dropoff_date, pickup_location]):
            return JsonResponse({
                'error': True,
                'message': 'Missing required booking information',
                'missing_fields': {
                    'car': not selected_car_id,
                    'pickup_date': not pickup_date,
                    'dropoff_date': not dropoff_date,
                    'pickup_location': not pickup_location
                }
            }, status=400)
        
        # Get session model and find selected car
        session_model = session_model_service.get_session_model(session_id)
        fleet = session_model.get('fleet', [])
        selected_car = next((car for car in fleet if car['id'] == selected_car_id), None)
        
        if not selected_car:
            return JsonResponse({
                'error': True,
                'message': 'Selected car not found'
            }, status=404)
        
        # Calculate pricing
        try:
            if isinstance(pickup_date, str):
                pickup_date = datetime.strptime(pickup_date, '%Y-%m-%d').date()
            if isinstance(dropoff_date, str):
                dropoff_date = datetime.strptime(dropoff_date, '%Y-%m-%d').date()
            
            rental_days = (dropoff_date - pickup_date).days
            if rental_days <= 0:
                return JsonResponse({
                    'error': True,
                    'message': 'Invalid rental period'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'error': True,
                'message': 'Invalid date format'
            }, status=400)
        
        # Calculate costs
        daily_rate = Decimal(str(selected_car['price_per_day']))
        subtotal = daily_rate * rental_days
        tax_rate = Decimal('10.0')  # 10% tax
        tax_amount = subtotal * (tax_rate / Decimal('100'))
        total = subtotal + tax_amount
        
        # Get deposit amount
        booking_info = session_model.get('booking_info', {})
        deposit = Decimal(str(booking_info.get('deposit_amounts', {}).get(selected_car['category'], 100)))
        
        # Prepare booking preview
        booking_preview = {
            'car': selected_car,
            'rental_period': {
                'pickup_date': pickup_date.isoformat(),
                'dropoff_date': dropoff_date.isoformat(),
                'rental_days': rental_days
            },
            'location': {
                'pickup_location': pickup_location,
                'dropoff_location': context.get_slot('dropoff_location', pickup_location)
            },
            'pricing': {
                'daily_rate': float(daily_rate),
                'subtotal': float(subtotal),
                'tax_rate': float(tax_rate),
                'tax_amount': float(tax_amount),
                'total': float(total),
                'deposit': float(deposit),
                'currency': selected_car['currency']
            },
            'customer': {
                'name': context.get_slot('name'),
                'email': context.get_slot('email'),
                'phone': context.get_slot('phone')
            }
        }
        
        return JsonResponse({
            'success': True,
            'booking_preview': booking_preview,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': True,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to preview booking: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_booking(request):
    """
    Create a new booking/order from the chat conversation.
    This handles the final booking creation after user confirmation.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        payment_method = data.get('payment_method', 'paystack')  # Default to Paystack
        
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'Session ID is required'
            }, status=400)
        
        # Get conversation context
        context = ai_assistant_service.get_context(session_id)
        
        # Validate required information
        required_fields = [
            'selected_car_id', 'pickup_date', 'dropoff_date', 
            'pickup_location', 'name', 'email', 'phone'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not context.get_slot(field):
                missing_fields.append(field)
        
        if missing_fields:
            return JsonResponse({
                'error': True,
                'message': 'Missing required booking information',
                'missing_fields': missing_fields
            }, status=400)
        
        # Get session model and selected car
        session_model = session_model_service.get_session_model(session_id)
        fleet = session_model.get('fleet', [])
        selected_car = next((car for car in fleet if car['id'] == context.get_slot('selected_car_id')), None)
        
        if not selected_car:
            return JsonResponse({
                'error': True,
                'message': 'Selected car not found'
            }, status=404)
        
        # Get car model from database
        try:
            car_model = Car.objects.get(id=selected_car['id'])
        except Car.DoesNotExist:
            return JsonResponse({
                'error': True,
                'message': 'Car not found in database'
            }, status=404)
        
        # Parse dates
        pickup_date = context.get_slot('pickup_date')
        dropoff_date = context.get_slot('dropoff_date')
        
        if isinstance(pickup_date, str):
            pickup_date = datetime.strptime(pickup_date, '%Y-%m-%d').date()
        if isinstance(dropoff_date, str):
            dropoff_date = datetime.strptime(dropoff_date, '%Y-%m-%d').date()
        
        # Create the order
        user = request.user if request.user.is_authenticated else None
        
        order = Order.objects.create(
            customer=user,
            car_name=selected_car['name'],
            dealer_name=selected_car['company_name'],
            cell_no=context.get_slot('phone'),
            address=f"Pickup: {context.get_slot('pickup_location')}",
            date_from=pickup_date,
            date_to=dropoff_date,
            pick_up_location=context.get_slot('pickup_location'),
            drop_off_location=context.get_slot('dropoff_location', context.get_slot('pickup_location')),
            pick_up_date=pickup_date,
            drop_off_date=dropoff_date,
            daily_rate=Decimal(str(selected_car['price_per_day'])),
            status='pending'  # Will be updated after payment confirmation
        )
        
        # Calculate billing automatically (handled in model save method)
        order.save()
        
        # Prepare payment data
        payment_data = {
            'order': order,
            'amount_usd': float(order.total_amount),
            'customer_email': context.get_slot('email'),
            'customer_name': context.get_slot('name'),
            'customer_phone': context.get_slot('phone')
        }
        
        # Initialize payment based on method
        payment_url = None
        payment_reference = None
        
        if payment_method == 'paystack':
            try:
                paystack_service = PaystackPaymentService()
                payment_result = paystack_service.initialize_payment(
                    order=order,
                    amount_usd=payment_data['amount_usd'],
                    customer_email=payment_data['customer_email'],
                    customer_name=payment_data['customer_name']
                )
                
                if payment_result.get('success'):
                    payment_url = payment_result['authorization_url']
                    payment_reference = payment_result['reference']
                else:
                    # If payment initialization fails, delete the order
                    order.delete()
                    return JsonResponse({
                        'error': True,
                        'message': 'Failed to initialize payment',
                        'details': payment_result.get('message')
                    }, status=400)
                    
            except Exception as e:
                order.delete()
                return JsonResponse({
                    'error': True,
                    'message': f'Payment initialization error: {str(e)}'
                }, status=500)
        
        elif payment_method == 'stripe':
            # Implement Stripe payment initialization
            pass
        
        elif payment_method == 'pay_later':
            # For pay later, just confirm the order
            order.status = 'confirmed'
            order.save()
        
        # Update conversation context
        context.update_slots({
            'booking_id': order.order_number,
            'order_id': order.id,
            'payment_reference': payment_reference
        })
        context.booking_state = 'created'
        
        # Get chat room and add system message
        chat_room = ChatRoom.objects.filter(room_id=session_id).first()
        if chat_room:
            ChatMessage.objects.create(
                room=chat_room,
                sender_type='system',
                content=f"Booking created: {order.order_number}. Total: ${order.total_amount:.2f}",
                metadata={
                    'action': 'booking_created',
                    'order_id': order.id,
                    'order_number': order.order_number
                }
            )
        
        response_data = {
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'car_name': order.car_name,
                'pickup_date': order.pick_up_date.isoformat(),
                'dropoff_date': order.drop_off_date.isoformat(),
                'pickup_location': order.pick_up_location,
                'total_amount': float(order.total_amount),
                'currency': 'USD',
                'status': order.status
            },
            'payment': {
                'method': payment_method,
                'reference': payment_reference,
                'payment_url': payment_url
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': True,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to create booking: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_chat_history(request):
    """
    Get chat history for a session.
    """
    try:
        session_id = request.GET.get('session_id')
        limit = int(request.GET.get('limit', 50))
        
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'Session ID is required'
            }, status=400)
        
        # Get chat room
        chat_room = ChatRoom.objects.filter(room_id=session_id).first()
        if not chat_room:
            return JsonResponse({
                'error': True,
                'message': 'Chat session not found'
            }, status=404)
        
        # Get messages
        messages = ChatMessage.objects.filter(
            room=chat_room
        ).order_by('created_at')[:limit]
        
        # Format messages
        message_list = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'sender_type': msg.sender_type,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'is_read': msg.is_read
            }
            
            if msg.metadata:
                message_data['metadata'] = msg.metadata
            
            message_list.append(message_data)
        
        return JsonResponse({
            'success': True,
            'messages': message_list,
            'room_id': chat_room.room_id,
            'room_status': chat_room.status
        })
        
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to get chat history: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def escalate_to_human(request):
    """
    Escalate a chat session to a human agent.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'Session ID is required'
            }, status=400)
        
        # Get chat room
        chat_room = ChatRoom.objects.filter(room_id=session_id).first()
        if not chat_room:
            return JsonResponse({
                'error': True,
                'message': 'Chat session not found'
            }, status=404)
        
        # Update room status for escalation
        chat_room.status = 'pending_escalation'
        chat_room.is_bot_handled = False
        chat_room.save()
        
        # Add system message
        ChatMessage.objects.create(
            room=chat_room,
            sender_type='system',
            content="Your conversation has been escalated to our support team. A human agent will be with you shortly.",
            metadata={'action': 'escalated_to_human'}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Chat escalated to human agent',
            'room_status': chat_room.status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': True,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to escalate chat: {str(e)}'
        }, status=500)


# Utility function to get cars data (for external API calls)
@require_http_methods(["GET"])
def get_cars_data(request):
    """
    Get cars data for external consumption.
    """
    try:
        category = request.GET.get('category')
        available_only = request.GET.get('available_only', 'true').lower() == 'true'
        
        # Use session model to get car data
        session_id = 'api_' + str(uuid.uuid4())
        session_model = session_model_service.get_session_model(session_id)
        fleet = session_model.get('fleet', [])
        
        # Apply filters
        if category:
            fleet = [car for car in fleet if car.get('category', '').lower() == category.lower()]
        
        if available_only:
            fleet = [car for car in fleet if car.get('availability') == 'available']
        
        return JsonResponse({
            'success': True,
            'cars': fleet,
            'total': len(fleet)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to get cars data: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_single_car(request, car_id):
    """
    Get single car details.
    """
    try:
        # Use session model to get car data
        session_id = 'api_' + str(uuid.uuid4())
        session_model = session_model_service.get_session_model(session_id)
        fleet = session_model.get('fleet', [])
        
        # Find car by ID
        car = next((c for c in fleet if c['id'] == int(car_id)), None)
        
        if not car:
            return JsonResponse({
                'error': True,
                'message': 'Car not found'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'car': car
        })
        
    except ValueError:
        return JsonResponse({
            'error': True,
            'message': 'Invalid car ID'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Failed to get car details: {str(e)}'
        }, status=500)
