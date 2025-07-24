from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import ChatRoom, ChatMessage, ChatBotResponse
from .bot_service import bot_service
import json
import uuid


def chat_page(request):
    """
    Public chat page for users to start a conversation
    """
    # Generate a unique room ID for the user
    room_id = str(uuid.uuid4())
    
    # If user is authenticated, try to get their existing room
    if request.user.is_authenticated:
        existing_room = ChatRoom.objects.filter(
            user=request.user,
            status__in=['bot_only', 'pending_escalation', 'active']
        ).first()
        
        if existing_room:
            room_id = existing_room.room_id
    
    context = {
        'room_id': room_id,
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
    }
    
    return render(request, 'system/chat.html', context)


@staff_member_required
def agent_dashboard(request):
    """
    Dashboard for support agents to manage chat sessions
    """
    # Get all active and pending escalation rooms
    active_rooms = ChatRoom.objects.filter(
        status__in=['pending_escalation', 'active']
    ).select_related('user', 'assigned_agent').order_by('-updated_at')
    
    # Get rooms assigned to current agent
    my_rooms = ChatRoom.objects.filter(
        assigned_agent=request.user,
        status='active'
    ).select_related('user').order_by('-updated_at')
    
    # Get recent messages for each room
    room_data = []
    for room in active_rooms:
        latest_message = ChatMessage.objects.filter(
            room=room
        ).order_by('-created_at').first()
        
        room_data.append({
            'room': room,
            'latest_message': latest_message,
            'unread_count': ChatMessage.objects.filter(
                room=room,
                sender_type='user',
                is_read=False
            ).count()
        })
    
    # Get analytics data for dashboard
    from django.db.models import Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Get analytics data
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    # Chat volume stats
    total_chats = ChatRoom.objects.count()
    active_chats = ChatRoom.objects.filter(status='active').count()
    pending_chats = ChatRoom.objects.filter(status='pending_escalation').count()
    
    # Recent activity
    recent_chats = ChatRoom.objects.filter(
        created_at__gte=last_week
    ).count()
    
    # Bot effectiveness
    bot_only_resolved = ChatRoom.objects.filter(
        status='closed',
        assigned_agent__isnull=True
    ).count()
    
    # Average response time (simplified)
    avg_messages_per_chat = ChatMessage.objects.values('room').annotate(
        message_count=Count('id')
    ).aggregate(avg_count=Avg('message_count'))['avg_count'] or 0
    
    context = {
        'room_data': room_data,
        'my_rooms': my_rooms,
        'agent': request.user,
        'total_chats': total_chats,
        'active_chats': active_chats,
        'pending_chats': pending_chats,
        'recent_chats': recent_chats,
        'bot_only_resolved': bot_only_resolved,
        'avg_messages_per_chat': round(avg_messages_per_chat, 2),
        'bot_effectiveness': round((bot_only_resolved / max(total_chats, 1)) * 100, 2),
    }
    
    return render(request, 'system/agent_dashboard.html', context)


@staff_member_required
def agent_chat(request, room_id):
    """
    Chat interface for agents to communicate with users
    """
    room = get_object_or_404(ChatRoom, room_id=room_id)
    
    # Assign agent to room if not already assigned
    if not room.assigned_agent:
        room.assigned_agent = request.user
        room.status = 'active'
        room.save()
        
        # Send system message about agent joining
        ChatMessage.objects.create(
            room=room,
            sender_type='system',
            content=f"Agent {request.user.username} has joined the conversation.",
            metadata={'action': 'agent_joined'}
        )
    
    # Mark user messages as read
    ChatMessage.objects.filter(
        room=room,
        sender_type='user',
        is_read=False
    ).update(is_read=True)
    
    # Get chat history
    messages = ChatMessage.objects.filter(
        room=room
    ).select_related('sender_user').order_by('created_at')
    
    context = {
        'room': room,
        'messages': messages,
        'agent': request.user,
    }
    
    return render(request, 'system/agent_chat.html', context)


@staff_member_required
@csrf_exempt
def close_chat(request, room_id):
    """
    Close a chat session
    """
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, room_id=room_id)
        
        # Update room status
        room.status = 'closed'
        room.save()
        
        # Send system message about chat closure
        ChatMessage.objects.create(
            room=room,
            sender_type='system',
            content=f"Chat session has been closed by {request.user.username}.",
            metadata={'action': 'chat_closed'}
        )
        
        messages.success(request, f'Chat session {room_id} has been closed.')
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'status': 'success', 'message': 'Chat closed successfully'})
        
        return redirect('system:agent_dashboard')
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@staff_member_required
def bot_responses(request):
    """
    Manage bot responses for the chat system
    """
    responses = ChatBotResponse.objects.all().order_by('-priority', 'intent')
    
    context = {
        'responses': responses,
    }
    
    return render(request, 'system/bot_responses.html', context)


@staff_member_required
@csrf_exempt
def add_bot_response(request):
    """
    Add a new bot response
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            response = ChatBotResponse.objects.create(
                intent=data.get('intent'),
                keywords=data.get('keywords', ''),
                response_text=data.get('response_text'),
                priority=data.get('priority', 1),
                is_active=data.get('is_active', True)
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bot response added successfully',
                'response_id': response.id
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@staff_member_required
def chat_analytics(request):
    """
    Analytics dashboard for chat system
    """
    from django.db.models import Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Get analytics data
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Chat volume stats
    total_chats = ChatRoom.objects.count()
    active_chats = ChatRoom.objects.filter(status='active').count()
    pending_chats = ChatRoom.objects.filter(status='pending_escalation').count()
    
    # Recent activity
    recent_chats = ChatRoom.objects.filter(
        created_at__gte=last_week
    ).count()
    
    # Bot effectiveness
    bot_only_resolved = ChatRoom.objects.filter(
        status='closed',
        assigned_agent__isnull=True
    ).count()
    
    escalated_chats = ChatRoom.objects.filter(
        status__in=['active', 'closed'],
        assigned_agent__isnull=False
    ).count()
    
    # Average response time (simplified)
    avg_messages_per_chat = ChatMessage.objects.values('room').annotate(
        message_count=Count('id')
    ).aggregate(avg_count=Avg('message_count'))['avg_count'] or 0
    
    context = {
        'total_chats': total_chats,
        'active_chats': active_chats,
        'pending_chats': pending_chats,
        'recent_chats': recent_chats,
        'bot_only_resolved': bot_only_resolved,
        'escalated_chats': escalated_chats,
        'avg_messages_per_chat': round(avg_messages_per_chat, 2),
        'bot_effectiveness': round((bot_only_resolved / max(total_chats, 1)) * 100, 2),
    }
    
    return render(request, 'system/chat_analytics.html', context)
