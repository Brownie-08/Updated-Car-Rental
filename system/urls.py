from django.urls import path
from django.contrib import admin
from .import views
from . import chat_views

app_name = 'system'

urlpatterns = [
    path('', views.home, name='home'),

    path('carlist/', views.car_list, name="car_list"),
    path('createOrder/', views.order_created, name="order_created"),
    path('createOrder/<int:car_id>/', views.order_created, name="order_create_with_car"),

    path('<int:id>/edit/', views.car_update, name="car_edit"),

    path('<int:id>/', views.car_detail, name="car_detail"),
    path('detail/<int:id>/', views.order_detail, name="order_detail"),
    path('order/<int:id>/generate_receipt/', views.generate_receipt, name='generate_receipt'),

    path('<int:id>/delete/', views.car_delete, name="car_delete"),
    path('<int:id>/deleteOrder/', views.order_delete, name="order_delete"),

    path('contact/', views.contact, name="contact"),

    path('newcar/', views.newcar, name="newcar"),
    path('<int:id>/like/', views.like_update, name="like"),
    
    path('popularcar/', views.popular_car, name="popularcar"),
    path('about/', views.about, name="about"),
    path('services/', views.services, name="services"),
    path('reviews/', views.reviews, name="reviews"),
    path('booking/', views.booking, name="booking"),
    path('debug/', views.debug_info, name='debug_info'),
    path('test-car-list/', views.test_car_list, name='test_car_list'),
    path('test-booking/', views.test_booking, name='test_booking'),
    
    # Chat URLs - moved to separate chat_urls.py to avoid conflicts
]
