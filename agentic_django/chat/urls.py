from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets with trailing_slash=False to handle both /threads and /threads/
router = DefaultRouter(trailing_slash=False)
router.register(r'spaces', views.SpaceViewSet, basename='space')
router.register(r'threads', views.ChatThreadViewSet, basename='chatthread')

urlpatterns = [
    # Sub-thread endpoints matching FastAPI pattern - must be before router to override
    path('threads/<str:pk>/sub_threads/', views.ChatThreadViewSet.as_view({'get': 'sub_threads', 'post': 'create_sub_thread'}), name='thread-sub-threads-with-slash'),
    path('threads/<str:pk>/sub_threads', views.ChatThreadViewSet.as_view({'get': 'sub_threads', 'post': 'create_sub_thread'}), name='thread-sub-threads'),
    
    # Create thread endpoint
    path('threads/create_thread/', views.ChatThreadViewSet.as_view({'post': 'create_thread'}), name='create-thread'),
    
    # Include router URLs - this will handle both /threads and /threads/
    path('', include(router.urls)),
    
    # Add explicit patterns to handle both with and without trailing slash
    path('threads/', views.ChatThreadViewSet.as_view({'get': 'list', 'post': 'create'}), name='threads-with-slash'),
    
    # Chat endpoints
    path('submit/', views.submit_message, name='submit_message'),
    path('stream/<str:task_id>/', views.stream_message, name='stream_message_with_slash'),
    path('stream/<str:task_id>', views.stream_message, name='stream_message'),
    
    # Health and stats
    path('health/', views.ChatHealthView.as_view(), name='chat_health'),
    path('stats/', views.ChatStatsView.as_view(), name='chat_stats'),
]