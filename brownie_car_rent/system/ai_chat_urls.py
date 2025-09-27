"""
URL routing for AI Chat Assistant API endpoints.
"""
from django.urls import path
from . import ai_chat_api_views

app_name = 'ai_chat_api'

urlpatterns = [
    # Core chat endpoints
    path('session/create/', ai_chat_api_views.create_chat_session, name='create_session'),
    path('message/send/', ai_chat_api_views.send_message, name='send_message'),
    path('history/', ai_chat_api_views.get_chat_history, name='chat_history'),
    path('escalate/', ai_chat_api_views.escalate_to_human, name='escalate_to_human'),
    
    # Booking endpoints
    path('booking/preview/', ai_chat_api_views.preview_booking, name='preview_booking'),
    path('booking/create/', ai_chat_api_views.create_booking, name='create_booking'),
    
    # Car data endpoints
    path('cars/', ai_chat_api_views.get_cars_data, name='get_cars'),
    path('cars/<int:car_id>/', ai_chat_api_views.get_single_car, name='get_car'),
]