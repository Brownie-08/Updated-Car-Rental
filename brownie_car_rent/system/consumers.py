import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .bot_service import bot_service
from django.contrib.auth.models import User
from .models import ChatMessage, ChatRoom


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Get or create chat room
        room = await self.get_or_create_room()
        
        # Send welcome message if this is a new room
        if await self.is_new_room(room):
            await self.send_welcome_message(room)
        
        # Send chat history to the newly connected user
        await self.send_chat_history(room)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        message_type = text_data_json.get('type', 'user_message')

        if message_type == 'user_message':
            # Get the room and user
            room = await self.get_or_create_room()
            user = self.scope['user']

            # Save the user message
            chat_message = await self.save_message(room, user, message, 'user')

            # Send user message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': user.username if user.is_authenticated else 'Anonymous',
                    'timestamp': chat_message.created_at.isoformat(),
                    'sender_type': 'user'
                }
            )

            # Process message with bot if room is in bot mode
            if room.status in ['bot_only', 'pending_escalation']:
                await self.process_bot_response(room, message)

        elif message_type == 'agent_message':
            # Handle agent messages
            room = await self.get_or_create_room()
            user = self.scope['user']
            
            # Check if user is staff (agent)
            if user.is_authenticated and user.is_staff:
                # Save agent message
                chat_message = await self.save_message(room, user, message, 'agent')
                
                # Send agent message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': f"Agent {user.username}",
                        'timestamp': chat_message.created_at.isoformat(),
                        'sender_type': 'agent'
                    }
                )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']
        sender_type = event.get('sender_type', 'user')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'sender': sender,
            'timestamp': timestamp,
            'sender_type': sender_type
        }))

    @database_sync_to_async
    def get_or_create_room(self):
        """Get or create a chat room"""
        room, created = ChatRoom.objects.get_or_create(
            room_id=self.room_name,
            defaults={
                'user': self.scope['user'] if self.scope['user'].is_authenticated else None,
                'status': 'bot_only'
            }
        )
        return room

    @database_sync_to_async
    def is_new_room(self, room):
        """Check if this is a new room with no messages"""
        return ChatMessage.objects.filter(room=room).count() == 0

    @database_sync_to_async
    def save_message(self, room, user, content, sender_type):
        """Save a message to the database"""
        return ChatMessage.objects.create(
            room=room,
            sender_user=user if user.is_authenticated else None,
            sender_type=sender_type,
            content=content
        )

    @database_sync_to_async
    def get_chat_history(self, room):
        """Get chat history for a room"""
        messages = ChatMessage.objects.filter(room=room).order_by('created_at')
        return [{
            'message': msg.content,
            'sender': msg.sender_user.username if msg.sender_user else msg.sender_type.title(),
            'timestamp': msg.created_at.isoformat(),
            'sender_type': msg.sender_type
        } for msg in messages]

    async def send_chat_history(self, room):
        """Send chat history to the connected user"""
        history = await self.get_chat_history(room)

        for message_data in history:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                **message_data
            }))

    async def send_welcome_message(self, room):
        """Send welcome message from bot"""
        bot_message = await sync_to_async(bot_service.send_welcome_message)(room)

        # Send welcome message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': bot_message.content,
                'sender': 'Bot Assistant',
                'timestamp': bot_message.created_at.isoformat(),
                'sender_type': 'bot'
            }
        )

    async def process_bot_response(self, room, user_message):
        """Process user message and generate bot response"""
        bot_message, escalated = await sync_to_async(bot_service.process_user_message)(room, user_message)

        # Send bot response to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': bot_message.content,
                'sender': 'Bot Assistant',
                'timestamp': bot_message.created_at.isoformat(),
                'sender_type': 'bot'
            }
        )

        # If escalated, notify agents
        if escalated:
            await self.notify_agents_of_escalation(room)

    async def notify_agents_of_escalation(self, room):
        """Notify agents about escalation request"""
        # Send notification to agents group
        await self.channel_layer.group_send(
            'agents',
            {
                'type': 'escalation_notification',
                'room_id': room.room_id,
                'message': f'User in room {room.room_id} has requested human assistance'
            }
        )
