import json
import asyncio
import redis
from celery import shared_task
from django.conf import settings
from .views import memory_service

@shared_task(bind=True)
def generate_response_task(self, user_id, message, response_mode, user_details, auth_token, sub_thread_id=None):
    task_id = self.request.id
    
    # Establish Redis connection
    r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    channel_name = f"chat_stream_{task_id}"
    
    # Accumulators for response database storage
    accumulated_answer = ""
    accumulated_metadata = {}
    import time
    start_time = time.time()
    
    async def run_stream():
        nonlocal accumulated_answer, accumulated_metadata
        import aiohttp
        # FastAPI Memory service endpoint for streaming
        url = f"{settings.MEMORY_SERVICE_URL}/api/chat/stream"
        payload = {
            "user_id": user_id,
            "message": message,
            "response_mode": response_mode,
            "user_details": user_details,
            "auth_token": auth_token
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=300) # 5 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        r.publish(channel_name, json.dumps({"error": f"Memory service error: {err_text}"}))
                        return
                        
                    # Read the stream chunk by chunk
                    async for line in response.content:
                        if line:
                            decoded = line.decode('utf-8').strip()
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                r.publish(channel_name, data_str)
                                
                                try:
                                    data_json = json.loads(data_str)
                                    if 'token' in data_json:
                                        accumulated_answer += data_json['token']
                                    elif 'sources' in data_json or 'used_tools' in data_json or 'thinking_steps' in data_json:
                                        accumulated_metadata.update(data_json)
                                except Exception:
                                    pass
                                    
        except Exception as e:
            r.publish(channel_name, json.dumps({"error": str(e)}))
            
    # Run the async loop inside Celery
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(run_stream())
    finally:
        loop.close()
        
    execution_time = time.time() - start_time
    
    # Save the generated response back to the Django database
    if sub_thread_id:
        try:
            from chat.models import ChatSubThread
            from chat.views import generate_fallback_title
            
            sub_thread = ChatSubThread.objects.get(id=sub_thread_id)
            sub_thread.answer = accumulated_answer if accumulated_answer else "No response generated"
            sub_thread.summary = accumulated_metadata.get('summary', accumulated_answer[:200] + "..." if len(accumulated_answer) > 200 else accumulated_answer)
            sub_thread.sources = accumulated_metadata.get('sources', [])
            sub_thread.related_links = accumulated_metadata.get('related_links', [])
            sub_thread.execution_time = round(execution_time, 3)
            sub_thread.save()
            
            # Update main thread title if this is the first sub-thread
            thread = sub_thread.parent_thread
            current_sub_threads = thread.sub_threads.count()
            if current_sub_threads == 1:
                current_title = thread.title.strip() if thread.title else ""
                default_titles = {"", "New Thread", "New Chat", "Thread", "Chat", "Untitled", "string", "New Chat Thread"}
                if not current_title or current_title in default_titles:
                    thread.title = generate_fallback_title(sub_thread.query)
                    thread.save()
        except Exception as db_err:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving chat response to database: {str(db_err)}")
        
    # Publish final done status
    r.publish(channel_name, json.dumps({"status": "done"}))
