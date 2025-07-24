from django.urls import path
from . import chat_views

app_name = 'chat'

urlpatterns = [
    # Chat URLs
    path('', chat_views.chat_page, name='chat_page'),
    path('agent/dashboard/', chat_views.agent_dashboard, name='agent_dashboard'),
    path('agent/chat/<str:room_id>/', chat_views.agent_chat, name='agent_chat'),
    path('agent/close-chat/<str:room_id>/', chat_views.close_chat, name='close_chat'),
    path('agent/bot-responses/', chat_views.bot_responses, name='bot_responses'),
    path('agent/add-bot-response/', chat_views.add_bot_response, name='add_bot_response'),
    path('agent/analytics/', chat_views.chat_analytics, name='chat_analytics'),
]
