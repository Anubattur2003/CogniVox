from django.contrib import admin
from .models import ChatThread, ChatMessage, ChatSubThread, ChatSubThreadMessage, Space


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Space model
    """
    list_display = ('id', 'user', 'name', 'color', 'is_default', 'thread_count_display', 'created_at', 'updated_at')
    list_filter = ('is_default', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'name', 'description')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'description', 'color', 'icon', 'is_default')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def thread_count_display(self, obj):
        """
        Display thread count for the space
        """
        return obj.threads.count()
    thread_count_display.short_description = 'Threads'


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatThread model
    """
    list_display = ('id', 'user', 'space', 'title', 'is_active', 'is_favorite', 'message_count_display', 'created_at', 'updated_at')
    list_filter = ('is_active', 'is_favorite', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'title')
    ordering = ('-updated_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'space', 'title', 'is_active', 'is_favorite')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def message_count_display(self, obj):
        """
        Display message count for the thread
        """
        return obj.message_count
    message_count_display.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatMessage model
    """
    list_display = ('id', 'thread', 'message_type', 'content_preview', 'created_at')
    list_filter = ('message_type', 'created_at')
    search_fields = ('thread__title', 'content', 'thread__user__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('thread', 'message_type', 'content')}),
        ('Model Info', {'fields': ('tokens_used',)}),
        ('Metadata', {'fields': ('metadata',)}),
        ('Timestamp', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        """
        Show a preview of the message content
        """
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(ChatSubThread)
class ChatSubThreadAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatSubThread model
    """
    list_display = ('id', 'parent_thread', 'title', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('parent_thread__title', 'title', 'context')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('parent_thread', 'title', 'context', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatSubThreadMessage)
class ChatSubThreadMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatSubThreadMessage model
    """
    list_display = ('id', 'sub_thread', 'message_type', 'content_preview', 'created_at')
    list_filter = ('message_type', 'created_at')
    search_fields = ('sub_thread__title', 'content')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('sub_thread', 'message_type', 'content')}),
        ('Model Info', {'fields': ('tokens_used',)}),
        ('Metadata', {'fields': ('metadata',)}),
        ('Timestamp', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        """
        Show a preview of the message content
        """
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
