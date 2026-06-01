"""
Authentication URL configuration.
Matches FastAPI authentication endpoints structure.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout, name='logout'),
    
    # JWT Token endpoints
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.refresh_token, name='token_refresh'),
    
    # User management endpoints
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Admin endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
]