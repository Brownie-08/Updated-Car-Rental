from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    
    # Car endpoints
    path('cars/', views.CarListView.as_view(), name='car_list'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car_detail'),
    path('cars/<int:car_id>/availability/', views.CarAvailabilityView.as_view(), name='car_availability'),
    
    # Order endpoints
    path('orders/', views.OrderListCreateView.as_view(), name='order_list_create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),
    path('orders/history/', views.UserOrderHistoryView.as_view(), name='order_history'),
    
    # Message endpoints
    path('messages/', views.MessageListCreateView.as_view(), name='message_list_create'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    
    # Utility endpoints
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('cars/popular/', views.popular_cars, name='popular_cars'),
    path('cars/brands/', views.car_brands, name='car_brands'),
    # path('cars/locations/', views.car_locations, name='car_locations'),  # Removed - no location field
]
