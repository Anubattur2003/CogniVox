# Generated migration for UUID conversion
# WARNING: This migration will DELETE ALL EXISTING CHAT DATA
# This is necessary to convert from integer IDs to UUIDs

from django.db import migrations, models
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_chatthread_is_favorite_space_chatthread_space'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Step 1: Drop all existing tables to avoid data conflicts
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS chat_sub_thread_messages CASCADE;',
            reverse_sql='',  # No reverse - this is a destructive operation
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS chat_sub_threads CASCADE;',
            reverse_sql='',
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS chat_messages CASCADE;',
            reverse_sql='',
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS chat_threads CASCADE;',
            reverse_sql='',
        ),
        
        # Step 2: Recreate ChatThread with UUID
        migrations.CreateModel(
            name='ChatThread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_favorite', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='chat_threads', to=settings.AUTH_USER_MODEL)),
                ('space', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='threads', to='chat.space')),
            ],
            options={
                'db_table': 'chat_threads',
                'ordering': ['-updated_at'],
            },
        ),
        
        # Step 3: Recreate ChatMessage with UUID FK
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('message_type', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')], max_length=10)),
                ('content', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('tokens_used', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('thread', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='messages', to='chat.chatthread')),
            ],
            options={
                'db_table': 'chat_messages',
                'ordering': ['created_at'],
            },
        ),
        
        # Step 4: Recreate ChatSubThread with UUID
        migrations.CreateModel(
            name='ChatSubThread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('chat_id', models.UUIDField(blank=True, null=True)),
                ('query', models.TextField(blank=True, null=True)),
                ('answer', models.TextField(blank=True, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('sources', models.JSONField(blank=True, default=list)),
                ('related_links', models.JSONField(blank=True, default=list)),
                ('response_mode', models.CharField(default='general', max_length=50)),
                ('n_results', models.IntegerField(default=5)),
                ('execution_time', models.FloatField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('context', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent_thread', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='sub_threads', to='chat.chatthread')),
            ],
            options={
                'db_table': 'chat_sub_threads',
                'ordering': ['-created_at'],
            },
        ),
        
        # Step 5: Recreate ChatSubThreadMessage with UUID FK
        migrations.CreateModel(
            name='ChatSubThreadMessage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('message_type', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')], max_length=10)),
                ('content', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('tokens_used', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sub_thread', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='messages', to='chat.chatsubthread')),
            ],
            options={
                'db_table': 'chat_sub_thread_messages',
                'ordering': ['created_at'],
            },
        ),
    ]

