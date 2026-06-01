from rest_framework import serializers
from .models import ChatThread, ChatMessage, ChatSubThread, ChatSubThreadMessage, Space
from authentication.models import User


class SpaceSerializer(serializers.ModelSerializer):
    """Serializer for Space model"""
    thread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Space
        fields = [
            'id', 'user', 'name', 'description', 'color', 'icon',
            'is_default', 'thread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_thread_count(self, obj):
        """Get the number of threads in this space"""
        return obj.threads.count()
    
    def validate_name(self, value):
        """Validate space name"""
        if not value.strip():
            raise serializers.ValidationError("Space name cannot be empty.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Space name must be at least 2 characters long.")
        return value.strip()


class MessageRequestSerializer(serializers.Serializer):
    """Serializer for chat message requests"""
    query = serializers.CharField(max_length=10000)
    global_access = serializers.BooleanField(default=False)

    def validate_query(self, value):
        """Validate query is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Query cannot be empty.")
        return value.strip()


class MessageResponseSerializer(serializers.Serializer):
    """Serializer for chat message responses"""
    message = serializers.CharField()
    is_global = serializers.BooleanField()


class SourceDocumentSerializer(serializers.Serializer):
    """Serializer for source documents from RAG systems"""
    document_title = serializers.CharField()
    content = serializers.CharField()
    relevance = serializers.FloatField(default=0.0)
    file_path = serializers.CharField(required=False, allow_blank=True, default="")
    download_url = serializers.URLField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, allow_null=True)

    def validate_document_title(self, value):
        """Ensure title is not empty"""
        if not value or not value.strip():
            return "Unknown Document"
        return value

    def validate_content(self, value):
        """Ensure content is not empty"""
        if not value or not value.strip():
            return "No content available"
        return value

    def validate_relevance(self, value):
        """Ensure relevance is a valid float"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model"""
    role = serializers.CharField(source='message_type', required=False)
    model_used = serializers.SerializerMethodField(read_only=True)
    is_global = serializers.SerializerMethodField(read_only=True)
    source_documents = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'thread', 'role', 'content', 'model_used', 
            'is_global', 'source_documents', 'metadata', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_model_used(self, obj):
        return obj.metadata.get('model_used', '')

    def get_is_global(self, obj):
        return obj.metadata.get('is_global', False)

    def get_source_documents(self, obj):
        return obj.metadata.get('sources', [])

    def validate_content(self, value):
        """Validate message content"""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


class ChatSubThreadMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatSubThreadMessage model"""
    role = serializers.CharField(source='message_type', required=False)
    model_used = serializers.SerializerMethodField(read_only=True)
    is_global = serializers.SerializerMethodField(read_only=True)
    source_documents = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ChatSubThreadMessage
        fields = [
            'id', 'sub_thread', 'role', 'content', 'model_used',
            'is_global', 'source_documents', 'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_model_used(self, obj):
        return obj.metadata.get('model_used', '')

    def get_is_global(self, obj):
        return obj.metadata.get('is_global', False)

    def get_source_documents(self, obj):
        return obj.metadata.get('sources', [])


class ChatSubThreadSerializer(serializers.ModelSerializer):
    """Serializer for ChatSubThread model"""
    messages = ChatSubThreadMessageSerializer(many=True, read_only=True)
    message_count = serializers.ReadOnlyField()
    sources = SourceDocumentSerializer(many=True, required=False)
    
    class Meta:
        model = ChatSubThread
        fields = [
            'id', 'parent_thread', 'chat_id', 'query', 'answer', 'summary',
            'sources', 'related_links', 'response_mode', 
            'n_results', 'execution_time', 'title', 'context', 
            'is_active', 'message_count', 'messages', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'parent_thread', 'created_at', 'updated_at', 'execution_time']

    def validate_title(self, value):
        """Validate sub-thread title"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_query(self, value):
        """Validate query is not empty when provided"""
        if value and not value.strip():
            raise serializers.ValidationError("Query cannot be empty.")
        return value


class ChatThreadSerializer(serializers.ModelSerializer):
    """Serializer for ChatThread model"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    sub_threads = ChatSubThreadSerializer(many=True, read_only=True)
    message_count = serializers.ReadOnlyField()
    sub_thread_count = serializers.ReadOnlyField()
    chat_id = serializers.SerializerMethodField()  # Add chat_id field for frontend compatibility
    user_id = serializers.SerializerMethodField()  # Add user_id field for frontend compatibility
    space_details = SpaceSerializer(source='space', read_only=True)  # Include space details
    
    class Meta:
        model = ChatThread
        fields = [
            'id', 'user', 'space', 'title', 'is_active', 'is_favorite',
            'message_count', 'sub_thread_count',
            'messages', 'sub_threads', 'created_at', 'updated_at',
            'chat_id', 'user_id', 'space_details'  # Include the new fields
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_chat_id(self, obj):
        """Return the id as chat_id for frontend compatibility"""
        return str(obj.id)
    
    def get_user_id(self, obj):
        """Return the user id as user_id for frontend compatibility"""
        return str(obj.user.id)

    def validate_title(self, value):
        """Validate thread title"""
        if value and len(value.strip()) < 1:
            raise serializers.ValidationError("Title cannot be empty.")
        return value


class ChatThreadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new chat threads"""
    
    class Meta:
        model = ChatThread
        fields = ['title', 'space', 'is_favorite']

    def create(self, validated_data):
        """Create thread with current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        
        # If no space provided, use user's default space if exists
        if 'space' not in validated_data or validated_data['space'] is None:
            default_space = Space.objects.filter(user=user, is_default=True).first()
            if default_space:
                validated_data['space'] = default_space
        
        return super().create(validated_data)


class ChatThreadListSerializer(serializers.ModelSerializer):
    """Simplified serializer for thread lists"""
    message_count = serializers.ReadOnlyField()
    sub_thread_count = serializers.ReadOnlyField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatThread
        fields = [
            'id', 'title', 'description', 'is_active',
            'message_count', 'sub_thread_count', 'last_message_at',
            'created_at', 'updated_at'
        ]

    def get_last_message_at(self, obj):
        """Get timestamp of last message in thread"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return last_message.created_at
        return obj.created_at


class TitleGenerationSerializer(serializers.Serializer):
    """Serializer for title generation requests"""
    content = serializers.CharField(max_length=10000)
    max_length = serializers.IntegerField(default=50, min_value=10, max_value=100)

    def validate_content(self, value):
        """Validate content for title generation"""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content too short for title generation.")
        return value.strip()