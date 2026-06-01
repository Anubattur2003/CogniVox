from datetime import timedelta
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status, generics, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole, SubscriptionPlan
from .serializers import (
    UserCreateSerializer, UserSerializer, LoginSerializer, 
    TokenSerializer, PasswordChangeSerializer
)
from core.utils import load_config

# Load configuration
config = load_config()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer"""
    
    def validate(self, attrs):
        # Try to authenticate with username first
        username = attrs.get('username')
        password = attrs.get('password')
        
        user = authenticate(username=username, password=password)
        
        # If authentication failed, try with email as username
        if not user:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        
        # Get the token
        refresh = RefreshToken.for_user(user)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'token_type': 'bearer'
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'access_token': serializer.validated_data['access'],
            'token_type': serializer.validated_data['token_type']
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """User login view"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access_token': str(refresh.access_token),
            'token_type': 'bearer'
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """User registration view"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Auto-generate username from email if not provided
        username = serializer.validated_data.get('username') or serializer.validated_data['email']
        serializer.validated_data['username'] = username
        
        # Check if username is taken
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Username already taken'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the default subscription plan
            default_plan = SubscriptionPlan.objects.get(name="Free")
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'detail': 'Default subscription plan not found'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create user
        user = serializer.save()
        user.subscription_plan = default_plan
        user.save()
        
        # Generate token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access_token': str(refresh.access_token),
            'token_type': 'bearer'
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    """Get current user information"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'role': user.role
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """List all users (admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only admins can see all users
        if self.request.user.role == UserRole.ADMIN:
            return User.objects.all()
        else:
            # Regular users can only see themselves
            return User.objects.filter(id=self.request.user.id)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail view (admin only for other users)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_id = self.kwargs.get('pk')
        
        # Users can only access their own profile unless they're admin
        if self.request.user.role != UserRole.ADMIN and str(self.request.user.id) != str(user_id):
            raise PermissionDenied("You can only access your own profile.")
        
        return generics.get_object_or_404(User, id=user_id)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def refresh_token(request):
    """Refresh JWT token"""
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response({
            'access_token': access_token,
            'token_type': 'bearer'
        })
    except Exception as e:
        return Response(
            {'detail': 'Invalid refresh token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def logout(request):
    """Logout user"""
    try:
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # Token might already be invalid
        
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
