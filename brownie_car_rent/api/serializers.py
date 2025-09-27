from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from account.models import CustomUser
from system.models import Car, Order, PrivateMsg


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'phone_number', 
                 'date_of_birth', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name',
                 'phone_number', 'date_of_birth', 'profile_picture', 'email_verified',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'email_verified', 'created_at', 'updated_at']


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs


class CarSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = ['id', 'image', 'image_url', 'car_name', 'company_name', 'num_of_seats', 'cost_par_day', 
                 'content', 'like']
        read_only_fields = ['id', 'like']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class CarListSerializer(serializers.ModelSerializer):
    """Simplified serializer for car listings"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = ['id', 'image_url', 'car_name', 'company_name', 'num_of_seats', 'cost_par_day', 'like']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'car_name', 'dealer_name', 'cell_no', 'address', 'date_from', 'date_to', 'total_cost']
        read_only_fields = ['id', 'customer_name', 'total_cost']

    def get_total_cost(self, obj):
        # Calculate total cost based on car's cost_par_day and duration
        try:
            car = Car.objects.get(car_name=obj.car_name)
            return obj.calculate_total_cost(car.cost_par_day)
        except Car.DoesNotExist:
            return 0

    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to:
            if date_from >= date_to:
                raise serializers.ValidationError("End date must be after start date.")
            
            from django.utils import timezone
            if date_from < timezone.now().date():
                raise serializers.ValidationError("Start date cannot be in the past.")
        
        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['car_name', 'dealer_name', 'cell_no', 'address', 'date_from', 'date_to']

    def validate(self, attrs):
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to:
            if date_from >= date_to:
                raise serializers.ValidationError("End date must be after start date.")
            
            from django.utils import timezone
            if date_from < timezone.now().date():
                raise serializers.ValidationError("Start date cannot be in the past.")
        
        return attrs

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


class PrivateMsgSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateMsg
        fields = ['id', 'name', 'email', 'message']
        read_only_fields = ['id']

    def validate_email(self, value):
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except Exception:
            raise serializers.ValidationError("Enter a valid email address.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    verification_code = serializers.CharField(max_length=6)

    def validate_verification_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Verification code must be 6 digits.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
