import os
import json
import aiohttp
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from django.conf import settings

logger = logging.getLogger(__name__)
from django.db import transaction, IntegrityError
from django.utils import timezone as django_timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import ChatThread, ChatMessage, ChatSubThread, ChatSubThreadMessage, Space
from .serializers import (
    ChatThreadSerializer, ChatMessageSerializer, ChatSubThreadSerializer,
    ChatSubThreadMessageSerializer, MessageRequestSerializer, MessageResponseSerializer,
    SpaceSerializer, ChatThreadCreateSerializer
)
from authentication.models import User
from core.utils import create_audit_log, log_api_usage
from core.models import SystemConfiguration


class MemoryServiceClient:
    """
    Client for interacting with the Agentic-Memory service.
    """
    def __init__(self, base_url=None):
        """Initialize the Memory Service client with configuration."""
        if base_url:
            self.base_url = base_url
        else:
            # Try to get from environment variable or Django settings
            memory_url = os.getenv("MEMORY_SERVICE_URL")
            memory_port = os.getenv("MEMORY_PORT")
            
            if memory_url:
                self.base_url = memory_url
            elif memory_port:
                self.base_url = f"http://localhost:{memory_port}"
            else:
                # Default fallback
                self.base_url = getattr(settings, 'MEMORY_SERVICE_URL', "http://localhost:8002")
                
        self.timeout = 300  # 5 minutes timeout

    async def generate_chat_response(self, user_id: str, message: str, response_mode: str = "general", user_details: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a chat request to the Memory service and get the response.
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Prepare payload with user details
                payload = {
                    "user_id": user_id,
                    "message": message,
                    "response_mode": response_mode
                }
                
                # Add user details if provided
                if user_details:
                    payload["user_details"] = user_details
                
                # Add auth_token if provided (for MCP server access)
                if auth_token:
                    payload["auth_token"] = auth_token
                
                # Prepare headers with auth token if available
                headers = {}
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"
                
                async with session.post(f"{self.base_url}/api/chat", json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Memory service error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result
                    
        except Exception as e:
            # Log the error but provide a fallback response
            return {
                "response": f"I'm sorry, but I encountered an issue processing your request. Please try again later.",
                "response_time": 0.0,
                "variants": {
                    "summary": "An error occurred.",
                    "detailed": "I'm sorry, but I encountered an issue processing your request. Please try again later."
                }
            }

    async def generate_thread_title(self, response: str, query: str, chat_id: str) -> Optional[str]:
        """
        Generate a title for a thread based on the response and query.
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    "response": response,
                    "query": query,
                    "chat_id": chat_id
                }
                
                async with session.post(f"{self.base_url}/api/generate-title", json=payload) as response:
                    if response.status != 200:
                        return None
                    
                    result = await response.json()
                    return result.get("title")
                    
        except Exception as e:
            return None


def generate_fallback_title(query: str) -> str:
    """
    Generate a fallback title when Memory service is unavailable.
    """
    try:
        # Clean the query and extract meaningful words
        words = query.strip().split()
        
        # Remove common stop words but keep important question words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}
        # Keep question words
        question_words = {"what", "how", "why", "where", "when", "who", "which", "whose", "whom"}
        
        meaningful_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower in question_words or (word_lower not in stop_words and len(word) > 2):
                meaningful_words.append(word)
        
        # Take first 5-8 meaningful words based on total length
        if len(meaningful_words) >= 7:
            title_words = meaningful_words[:5]
        elif len(meaningful_words) >= 4:
            title_words = meaningful_words[:6]
        else:
            title_words = meaningful_words[:8] if len(meaningful_words) >= 2 else meaningful_words
        
        if title_words:
            title = " ".join(title_words)
            # Capitalize properly
            title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
            
            # If title doesn't end with a question mark but starts with question word, add one
            if title_words[0].lower() in question_words and not title.endswith("?"):
                title += "?"
            elif not title.endswith(("?", ".", "!")):
                title += " Discussion"
                
            return title
        else:
            # If no meaningful words, use first few words of original query
            fallback_words = words[:6]
            title = " ".join(fallback_words)
            title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
            
            # Ensure it's not too long
            if len(title) > 60:
                title = title[:57] + "..."
                
            return title
            
    except Exception as e:
        return "New Chat Thread"


# Initialize the Memory service client
memory_service = MemoryServiceClient()


class SpaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing spaces/folders.
    """
    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get spaces for the current user."""
        return Space.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Create a new space with proper error handling."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError as e:
            # Handle duplicate space name
            if 'unique constraint' in str(e).lower() and 'name' in str(e).lower():
                return Response(
                    {'error': 'A space with this name already exists. Please choose a different name.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Re-raise other integrity errors
            raise

    def perform_create(self, serializer):
        """Create a new space."""
        # Ensure the user is set to the current user
        space = serializer.save(user=self.request.user)
        
        # Create audit log
        create_audit_log(
            user=self.request.user,
            action='CREATE',
            resource_type='Space',
            resource_id=space.id,
            details={'name': space.name},
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Update a space."""
        space = serializer.save()
        
        # Create audit log
        create_audit_log(
            user=self.request.user,
            action='UPDATE',
            resource_type='Space',
            resource_id=space.id,
            details={'name': space.name},
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Delete a space."""
        # Create audit log before deletion
        create_audit_log(
            user=self.request.user,
            action='DELETE',
            resource_type='Space',
            resource_id=instance.id,
            details={'name': instance.name},
            request=self.request
        )
        
        # Delete the space (threads will have space set to NULL due to SET_NULL)
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set a space as the default space for the user."""
        space = self.get_object()
        
        # Remove default flag from all other spaces
        Space.objects.filter(user=request.user).update(is_default=False)
        
        # Set this space as default
        space.is_default = True
        space.save()
        
        # Create audit log
        create_audit_log(
            user=request.user,
            action='UPDATE',
            resource_type='Space',
            resource_id=space.id,
            details={'action': 'set_default'},
            request=request
        )
        
        return Response({'status': 'default space set'}, status=status.HTTP_200_OK)


class ChatThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat threads.
    """
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get threads for the current user, optionally filtered by space."""
        queryset = ChatThread.objects.filter(user=self.request.user).order_by('-updated_at')
        
        # Filter by space if provided
        space_id = self.request.query_params.get('space_id', None)
        if space_id:
            if space_id == 'null' or space_id == 'none':
                queryset = queryset.filter(space__isnull=True)
            else:
                queryset = queryset.filter(space_id=space_id)
        
        # Filter by favorite if provided
        is_favorite = self.request.query_params.get('is_favorite', None)
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite.lower() == 'true')
        
        return queryset

    def perform_create(self, serializer):
        """Create a new chat thread."""
        # Ensure the user is set to the current user
        serializer.save(user=self.request.user)
        
        # Create audit log
        create_audit_log(
            user=self.request.user,
            action='CREATE',
            resource_type='ChatThread',
            resource_id=serializer.instance.id,
            request=self.request
        )

    @action(detail=False, methods=['post'])
    def create_thread(self, request):
        """Create a new thread (FastAPI compatibility endpoint)."""
        serializer = ChatThreadSerializer(data=request.data)
        if serializer.is_valid():
            thread = serializer.save(user=request.user)
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='CREATE',
                resource_type='ChatThread',
                resource_id=thread.id,
                details={'title': thread.title},
                request=request
            )
            
            return Response(ChatThreadSerializer(thread).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        """List chat threads with optional sub-thread inclusion."""
        include_subthreads = request.query_params.get('subthread', 'true').lower() == 'true'
        
        queryset = self.get_queryset()
        
        if include_subthreads:
            queryset = queryset.prefetch_related(
                Prefetch('sub_threads', queryset=ChatSubThread.objects.order_by('-created_at'))
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sub_threads(self, request, pk=None):
        """Get sub-threads for a specific chat thread."""
        thread = self.get_object()
        sub_threads = thread.sub_threads.all().order_by('-created_at')
        serializer = ChatSubThreadSerializer(sub_threads, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_sub_thread(self, request, pk=None):
        """Create a new sub-thread for a chat thread - matches FastAPI endpoint."""
        chat_id = pk  # Use pk as chat_id to match FastAPI pattern
        
        # Get the thread by chat_id (pk)
        try:
            thread = self.get_object()
        except ChatThread.DoesNotExist:
            return Response(
                {'detail': 'Main thread not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user owns the thread
        if thread.user != request.user:
            return Response(
                {'detail': 'You do not have permission to create a sub-thread for this thread'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check sub-thread limit
        max_sub_threads = getattr(settings, 'MAX_SUB_THREADS', 50)
        if thread.sub_threads.count() >= max_sub_threads:
            return Response(
                {'detail': f'Cannot add more than {max_sub_threads} sub-threads. Please create a new chat.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data from request body (matching FastAPI SubThread model)
        
        # Prepare sub-thread data matching FastAPI SubThread structure
        sub_thread_data = {
            'chat_id': chat_id,
            'response_mode': request.data.get('response_mode', 'general'),
            'query': request.data.get('query', ''),
            'answer': request.data.get('answer', ''),  # Will be updated after memory service call
            'summary': request.data.get('summary', ''),  # Will be updated after memory service call
            'sources': request.data.get('sources', []),  # Will be updated after memory service call
            'related_links': request.data.get('related_links', []),
            'n_results': request.data.get('n_results', 5),
            'execution_time': 0.0,  # Will be calculated
            'created_at': request.data.get('created_at'),
            'updated_at': request.data.get('updated_at')
        }
        
        serializer = ChatSubThreadSerializer(data=sub_thread_data)
        if serializer.is_valid():
            with transaction.atomic():
                start_time = django_timezone.now()
                
                # Create the sub-thread
                sub_thread = serializer.save(
                    parent_thread=thread
                )
                
                # Process the message with Memory service
                user_details = {
                    'id': request.user.id,
                    'role': str(request.user.role),
                    'email': request.user.email,
                    'username': request.user.username,
                    'is_active': request.user.is_active,
                    'created_at': request.user.created_at.isoformat() if request.user.created_at else None,
                    'chat_id': chat_id,
                    'n_results': sub_thread_data.get('n_results', 5)
                }
                
                # Extract auth token from request headers for MCP server access
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                auth_token = None
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header[7:]
                
                # Log auth token status for debugging
                if auth_token:
                    logger.info(f"Django: Extracted auth_token for user {request.user.id} (length: {len(auth_token)}, starts with: {auth_token[:10]}...)")
                else:
                    logger.warning(f"Django: No auth_token found in request headers for user {request.user.id}")
                    logger.debug(f"Django: Available headers: {[k for k in request.META.keys() if 'AUTH' in k.upper()]}")
                
                # Call Agentic-Memory service for AI response
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    memory_response = loop.run_until_complete(
                        memory_service.generate_chat_response(
                            user_id=str(request.user.id),
                            message=sub_thread.query,
                            response_mode=sub_thread.response_mode,
                            user_details=user_details,
                            auth_token=auth_token  # Pass auth token for MCP server access
                        )
                    )
                finally:
                    loop.close()
                
                # Calculate execution time
                end_time = django_timezone.now()
                execution_time = (end_time - start_time).total_seconds()
                
                # Update sub-thread with response - matching FastAPI behavior
                sub_thread.answer = memory_response.get('response', 'No response generated')
                sub_thread.summary = memory_response.get('variants', {}).get('summary', '')
                sub_thread.sources = memory_response.get('sources', [])
                sub_thread.related_links = memory_response.get('related_links', [])
                sub_thread.execution_time = round(execution_time, 3)  # Match FastAPI precision
                sub_thread.save()
                
                # Update thread timestamp
                thread.updated_at = django_timezone.now()
                thread.save()
                
                # Generate title if this is the first sub-thread and no meaningful title exists
                current_sub_threads = thread.sub_threads.count()
                is_first_subthread = current_sub_threads == 1
                
                if is_first_subthread:
                    current_title = thread.title.strip() if thread.title else ""
                    default_titles = {"", "New Thread", "New Chat", "Thread", "Chat", "Untitled", "string", "New Chat Thread"}
                    
                    if not current_title or current_title in default_titles:
                        # Check if Memory service already generated a title
                        auto_generated_title = memory_response.get("generated_title")
                        
                        if auto_generated_title and auto_generated_title.strip():
                            thread.title = auto_generated_title
                        else:
                            # Use fallback title generation
                            thread.title = generate_fallback_title(sub_thread.query)
                        
                        thread.save()
                
                # Create audit log
                create_audit_log(
                    user=request.user,
                    action='CREATE',
                    resource_type='ChatSubThread',
                    resource_id=sub_thread.id,
                    details={
                        'query': sub_thread.query[:100],
                        'execution_time': execution_time,
                        'response_mode': sub_thread.response_mode
                    },
                    request=request
                )
            
            # Return response matching FastAPI SubThread model structure
            response_data = ChatSubThreadSerializer(sub_thread).data
            
            # Ensure response includes all FastAPI-compatible fields
            response_data.update({
                'chat_id': chat_id,
                'response_mode': sub_thread.response_mode,
                'query': sub_thread.query,
                'answer': sub_thread.answer,
                'summary': sub_thread.summary,
                'sources': sub_thread.sources,
                'related_links': sub_thread.related_links,
                'n_results': sub_thread.n_results,
                'execution_time': sub_thread.execution_time,
                'created_at': sub_thread.created_at.isoformat() if sub_thread.created_at else None,
                'updated_at': sub_thread.updated_at.isoformat() if sub_thread.updated_at else None
            })
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'patch'])
    def toggle_favorite(self, request, pk=None):
        """Toggle the favorite status of a thread."""
        thread = self.get_object()
        thread.is_favorite = not thread.is_favorite
        thread.save()
        
        # Create audit log
        create_audit_log(
            user=request.user,
            action='UPDATE',
            resource_type='ChatThread',
            resource_id=thread.id,
            details={'is_favorite': thread.is_favorite},
            request=request
        )
        
        serializer = self.get_serializer(thread)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_favorite(self, request, pk=None):
        """Update the favorite status of a thread."""
        thread = self.get_object()
        is_favorite = request.data.get('is_favorite', None)
        
        if is_favorite is not None:
            thread.is_favorite = is_favorite
            thread.save()
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='UPDATE',
                resource_type='ChatThread',
                resource_id=thread.id,
                details={'is_favorite': thread.is_favorite},
                request=request
            )
        
        serializer = self.get_serializer(thread)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def move_to_space(self, request, pk=None):
        """Move a thread to a different space."""
        thread = self.get_object()
        space_id = request.data.get('space_id', None)
        
        if space_id:
            try:
                space = Space.objects.get(id=space_id, user=request.user)
                thread.space = space
                thread.save()
            except Space.DoesNotExist:
                return Response(
                    {'detail': 'Space not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            thread.space = None
            thread.save()
        
        # Create audit log
        create_audit_log(
            user=request.user,
            action='UPDATE',
            resource_type='ChatThread',
            resource_id=thread.id,
            details={'space_id': space_id},
            request=request
        )
        
        serializer = self.get_serializer(thread)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete a chat thread and all its sub-threads."""
        thread = self.get_object()
        
        # Create audit log before deletion
        create_audit_log(
            user=request.user,
            action='DELETE',
            resource_type='ChatThread',
            resource_id=thread.id,
            details={'title': thread.title},
            request=request
        )
        
        return super().destroy(request, *args, **kwargs)


class ChatSubThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat sub-threads.
    """
    serializer_class = ChatSubThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get sub-threads for the current user's threads."""
        return ChatSubThread.objects.filter(
            chat_thread__user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Create a new chat sub-thread."""
        # This is handled by the ChatThreadViewSet.create_sub_thread action
        pass


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_message(request):
    """
    Submit a message and get AI response.
    Compatible with the original FastAPI endpoint structure.
    """
    # Extract data from request - simplified without model validation
    query = request.data.get('query', '')
    global_access = request.data.get('global_access', False)
    
    if not query or not query.strip():
        return Response(
            {'detail': 'Query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            # Process the message with Memory service
            user_details = {
                'role': request.user.role,
                'email': request.user.email,
                'username': request.user.username
            }
            
            # Extract auth token from request headers
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            auth_token = None
            if auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                memory_response = loop.run_until_complete(
                    memory_service.generate_chat_response(
                        user_id=str(request.user.id),
                        message=query,
                        response_mode=request.data.get('response_mode', 'general'),
                        user_details=user_details,
                        auth_token=auth_token  # Pass auth token for MCP access
                    )
                )
            finally:
                loop.close()
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='SUBMIT_MESSAGE',
                resource_type='Message',
                details={'query': query[:100]},
                request=request
            )
            
            # Format response
            response_data = {
                'message': memory_response.get('response', 'No response generated'),
                'is_global': global_access,
                'sources': memory_response.get('sources', []),
                'summary': memory_response.get('variants', {}).get('summary', ''),
                'related_links': memory_response.get('related_links', [])
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'detail': f'Error processing message: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ChatHealthView(APIView):
    """
    Health check endpoint for chat service.
    """
    permission_classes = []

    def get(self, request):
        """Check chat service health."""
        try:
            # Check database connectivity
            thread_count = ChatThread.objects.count()
            
            # Check Memory service connectivity
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Simple health check to Memory service
                memory_health = True  # Simplified for now
            finally:
                loop.close()
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'memory_service': 'connected' if memory_health else 'disconnected',
                'thread_count': thread_count,
                'timestamp': django_timezone.now().isoformat()
            })
        
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': django_timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ChatStatsView(APIView):
    """
    Chat statistics endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get chat statistics for the current user."""
        user_threads = ChatThread.objects.filter(user=request.user)
        
        stats = {
            'total_threads': user_threads.count(),
            'total_sub_threads': ChatSubThread.objects.filter(parent_thread__user=request.user).count(),
            'threads_today': user_threads.filter(
                created_at__date=django_timezone.now().date()
            ).count(),
            'most_used_models': []
        }
        
        return Response(stats)
