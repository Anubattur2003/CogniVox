from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, UserRole


class TokenSerializer(serializers.Serializer):
    """Serializer for JWT token response"""
    access_token = serializers.CharField()
    token_type = serializers.CharField(default="bearer")


class TokenDataSerializer(serializers.Serializer):
    """Serializer for token data validation"""
    username = serializers.CharField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False, allow_null=True)


class UserBaseSerializer(serializers.Serializer):
    """Base user serializer with email"""
    email = serializers.EmailField()


class UserCreateSerializer(UserBaseSerializer):
    """Serializer for user registration"""
    username = serializers.CharField(required=False, allow_null=True, max_length=150)
    first_name = serializers.CharField(required=False, allow_null=True, max_length=30)
    last_name = serializers.CharField(required=False, allow_null=True, max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.USER)

    def validate_password(self, value):
        """Validate password using Django's built-in validators"""
        validate_password(value)
        return value

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(UserBaseSerializer):
    """Serializer for user data response"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=30, required=False, allow_null=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_active', 'role']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate user credentials"""
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Try to authenticate with email first, then username
            user = authenticate(username=username, password=password)
            if not user:
                # Try with email as username
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate_new_password(self, value):
        """Validate new password"""
        validate_password(value)
        return value

    def save(self):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user