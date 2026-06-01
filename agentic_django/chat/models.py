import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class Space(models.Model):
    """
    Spaces/Folders for organizing chat threads.
    Users can create multiple spaces to organize their conversations.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='spaces'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color for UI
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon name for UI
    is_default = models.BooleanField(default=False)  # Default space for new threads
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'spaces'
        ordering = ['-created_at']
        unique_together = [['user', 'name']]  # Prevent duplicate space names per user

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class ChatThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_threads'
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.SET_NULL,
        related_name='threads',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_threads'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread {self.id} - {self.title or 'Untitled'}"

    @property
    def message_count(self):
        return self.messages.count()

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()
    
    @property
    def sub_thread_count(self):
        return self.sub_threads.count()


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional data
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type.title()} message in Thread {self.thread.id}"


class ChatSubThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='sub_threads'
    )
    # Fields matching FastAPI SubThread model
    chat_id = models.UUIDField(blank=True, null=True)  # Reference to parent thread UUID
    query = models.TextField(blank=True, null=True)  # User's question/input
    answer = models.TextField(blank=True, null=True)  # AI response
    summary = models.TextField(blank=True, null=True)  # Summary of the response
    sources = models.JSONField(default=list, blank=True)  # Source documents
    related_links = models.JSONField(default=list, blank=True)  # Related links
    response_mode = models.CharField(max_length=50, default='general')  # Response mode
    n_results = models.IntegerField(default=5)  # Number of results to return
    execution_time = models.FloatField(null=True, blank=True)  # Processing time in seconds
    
    # Existing fields
    title = models.CharField(max_length=255, blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sub_threads'
        ordering = ['-created_at']

    def __str__(self):
        return f"SubThread {self.id} of Thread {self.parent_thread.id}"

    @property
    def message_count(self):
        return self.messages.count()


class ChatSubThreadMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.AutoField(primary_key=True)
    sub_thread = models.ForeignKey(
        ChatSubThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'chat_sub_thread_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type.title()} message in SubThread {self.sub_thread.id}"
