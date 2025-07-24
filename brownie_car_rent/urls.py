"""car_rental_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path(r'', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path(r'', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import path, include
    3. Add a URL to urlpatterns:  path(r'blog/', include(blog_urls))
"""
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from system.views import admin_car_list, admin_msg, order_list, car_created, order_update, order_delete, msg_delete, base_dash, home, admin_reports, update_order_status, admin_msg_respond
from django.http import JsonResponse
from django.db import connection
from account.views import (
    register_view, 
    admin_register_view, 
    login_view, 
    logout_view,
    verify_email_view,
    verify_email_pending_view,
    resend_verification_view,
    password_reset_request_view,
    password_reset_sent_view,
    password_reset_confirm_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_dash/', base_dash, name='base_dash'),
    path('admin_reports/', admin_reports, name='admin_reports'),
    path('admin_index/', admin_car_list, name='adminIndex'),  # Admin dashboard
    # Root path routes to different views based on user type
    path('', home, name='home'),  # Public home page
    path('listOrder/', order_list, name="order_list"),
    path('<int:id>/editOrder/', order_update, name="order_edit"),
    path('<int:id>/deleteOrder/', order_delete, name="order_delete"),
    path('<int:id>/approveOrder/', update_order_status, name="order_approve"),
    path('create/', car_created, name="car_create"),
    path('message/', admin_msg, name='message'),
    path('<int:id>/deletemsg/', msg_delete, name="msg_delete"),
    path('<int:id>/respondmsg/', admin_msg_respond, name="admin_msg_respond"),
    path('car/', include('system.urls')),
    path('api/', include('api.urls')),  # Include API URLs
    # Chat URLs
    path('chat/', include('system.chat_urls')),
    # Authentication URLs
    path('register/', register_view, name='register'),
    path('verify_email/', verify_email_view, name='verify_email'),
    path('verify_email_pending/', verify_email_pending_view, name='verify_email_pending'),
    path('resend_verification/', resend_verification_view, name='resend_verification'),
    path('admin_register/', admin_register_view, name='admin_register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Password Reset URLs
    path('password_reset/', password_reset_request_view, name='password_reset_request'),
    path('password_reset_sent/', password_reset_sent_view, name='password_reset_sent'),
    path('password_reset_confirm/<str:token>/', password_reset_confirm_view, name='password_reset_confirm'),
    
    # Health check endpoint for Docker
    path('health/', lambda request: JsonResponse({'status': 'healthy', 'database': _check_db_connection()}), name='health_check'),
]

def _check_db_connection():
    """Helper function to check database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return 'connected'
    except Exception:
        return 'disconnected'
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs if available
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
