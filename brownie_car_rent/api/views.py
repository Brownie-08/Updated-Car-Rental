from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings

from account.models import CustomUser as User
from system.models import Car, Order, PrivateMsg
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    PasswordChangeSerializer, CarSerializer,
    OrderSerializer, OrderCreateSerializer, PrivateMsgSerializer
)


class UserRegistrationView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(TokenObtainPairView):
    """Enhanced login view with user profile data"""
    serializer_class = UserLoginSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            response.data['user'] = UserProfileSerializer(user).data
        return response


class UserProfileView(APIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CarListView(generics.ListAPIView):
    """List all available cars with filtering and search"""
    serializer_class = CarSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['car_name', 'company_name', 'content']
    ordering_fields = ['cost_par_day', 'like', 'id']
    ordering = ['-id']
    
    def get_queryset(self):
        queryset = Car.objects.all()
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(cost_par_day__gte=min_price)
        if max_price:
            queryset = queryset.filter(cost_par_day__lte=max_price)
        
        # Filter by brand
        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(company_name__icontains=brand)
        
        # Filter by search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(car_name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset


class CarDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific car"""
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [AllowAny]


class CarAvailabilityView(APIView):
    """Check car availability for specific dates"""
    permission_classes = [AllowAny]
    
    def post(self, request, car_id):
        try:
            car = Car.objects.get(id=car_id)
        except Car.DoesNotExist:
            return Response({'error': 'Car not found'}, status=status.HTTP_404_NOT_FOUND)
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response({
                'error': 'Both start_date and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for conflicting orders (simplified since no status field)
        conflicting_orders = Order.objects.filter(
            car_name=car.car_name,
            date_from__lte=end_date,
            date_to__gte=start_date
        )
        
        is_available = not conflicting_orders.exists()
        
        return Response({
            'available': is_available,
            'car': CarSerializer(car).data,
            'requested_dates': {
                'start_date': start_date,
                'end_date': end_date
            }
        })


class OrderListCreateView(generics.ListCreateAPIView):
    """List user orders and create new orders"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-id')
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """Get and update specific order details"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)
    
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        
        # Only allow status updates for pending orders
        # Note: Current Order model doesn't have status field
        # This validation is disabled for now
        # if order.status not in ['pending'] and 'status' in request.data:
        #     return Response({
        #         'error': 'Cannot modify confirmed or completed orders'
        #     }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)


class OrderCancelView(APIView):
    """Cancel an order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Note: Current Order model doesn't have status field
        # For now, we'll just delete the order as a form of cancellation
        order.delete()
        
        return Response({
            'message': 'Order cancelled successfully'
        })


class MessageListCreateView(generics.ListCreateAPIView):
    """List and create private messages"""
    serializer_class = PrivateMsgSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Note: PrivateMsg model doesn't have sender/receiver fields or created_at
        # For now, return all messages
        return PrivateMsg.objects.all()
    
    def perform_create(self, serializer):
        # Note: PrivateMsg model doesn't have sender field
        serializer.save()


class MessageDetailView(generics.RetrieveAPIView):
    """Get specific message details"""
    serializer_class = PrivateMsgSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Note: PrivateMsg model doesn't have sender/receiver fields
        # For now, return all messages
        return PrivateMsg.objects.all()


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Get dashboard statistics"""
    stats = {
        'total_cars': Car.objects.count(),
        'available_cars': Car.objects.count(),  # All cars are available in current model
        'total_orders': Order.objects.count(),
        'active_orders': Order.objects.count(),  # No status field in current model
    }
    
    if request.user.is_authenticated:
        stats.update({
            'user_orders': Order.objects.filter(customer=request.user).count(),
            'user_messages': PrivateMsg.objects.count(),  # PrivateMsg doesn't have sender/receiver fields
        })
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_cars(request):
    """Get most popular cars based on orders"""
    popular_cars = Car.objects.order_by('-like')[:6]
    
    return Response(CarSerializer(popular_cars, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def car_brands(request):
    """Get available car brands"""
    brands = Car.objects.values_list('company_name', flat=True).distinct().order_by('company_name')
    return Response(list(brands))


# Car locations endpoint removed - no location field in current model


class UserOrderHistoryView(generics.ListAPIView):
    """Get user's order history with filtering"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Note: Order model doesn't have created_at field
        queryset = Order.objects.filter(customer=self.request.user).order_by('-id')
        
        # Note: Order model doesn't have status or created_at fields
        # These filters are disabled for now
        # Filter by date range using date_from instead
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date_from__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_from__lte=end_date)
        
        return queryset
