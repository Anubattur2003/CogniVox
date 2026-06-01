# Manual migration to remove model-related fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatsubthread_answer_chatsubthread_chat_id_and_more"),
    ]

    operations = [
        # Remove model_used_id ForeignKey from ChatMessage (this is what actually exists in DB)
        migrations.RunSQL(
            sql='ALTER TABLE chat_messages DROP COLUMN IF EXISTS model_used_id CASCADE;',
            reverse_sql='-- Cannot reverse this migration',
        ),
        # Remove model_name from ChatSubThread
        migrations.RunSQL(
            sql='ALTER TABLE chat_sub_threads DROP COLUMN IF EXISTS model_name CASCADE;',
            reverse_sql='-- Cannot reverse this migration',
        ),
        # Remove model_used_id ForeignKey from ChatSubThreadMessage (this is what actually exists in DB)
        migrations.RunSQL(
            sql='ALTER TABLE chat_sub_thread_messages DROP COLUMN IF EXISTS model_used_id CASCADE;',
            reverse_sql='-- Cannot reverse this migration',
        ),
    ]

