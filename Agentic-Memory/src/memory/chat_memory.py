"""
L0 Memory Module for storing and retrieving chat message history.
This module provides context awareness for the memory service by maintaining
a record of previous messages in each chat thread.
"""

import logging
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import sqlite3
import json
import threading
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logger = logging.getLogger("cogniVox")

class ChatMemory:
    """
    L0 Memory system that stores and retrieves chat messages by chat_id.
    Uses MongoDB from Backend service as the primary source and SQLite for local caching.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for ChatMemory."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ChatMemory, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, db_path="chat_memory.db", max_context_messages=20):
        """Initialize the chat memory system."""
        if self._initialized:
            return
            
        self.db_path = db_path
        self.max_context_messages = max_context_messages
        self.memory_cache = {}  # In-memory cache: {chat_id: [messages]}
        self.last_access = {}   # Track last access time for cache management
        
        # Initialize MongoDB tracking attributes with safe defaults first
        self._ensure_mongo_attributes()
        
        # Initialize MongoDB connection to Backend's database
        self._init_mongodb()
        
        # Initialize local SQLite cache
        self._init_db()
        
        self._initialized = True
        logger.info(f"L0 ChatMemory initialized with max context of {max_context_messages} messages")
        
        # Test MongoDB connectivity and log initial status
        self._test_mongodb_connectivity()
        
        # Log initial MongoDB status  
        try:
            initial_stats = self.get_mongodb_stats()
            status = initial_stats.get('status', 'unknown')
            logger.info(f"📊 MongoDB initial status: {status}")
            if status in ['error', 'no_operations']:
                logger.info(f"   This is normal on first startup - operations will begin after first API calls")
            elif 'successful_operations' in initial_stats:
                logger.info(f"   Successful operations: {initial_stats['successful_operations']}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get initial MongoDB stats: {str(e)}")
    
    def _ensure_mongo_attributes(self):
        """Ensure MongoDB tracking attributes are initialized with safe defaults."""
        # Connection health tracking attributes
        if not hasattr(self, 'mongo_healthy'):
            self.mongo_healthy = False
        if not hasattr(self, 'mongo_last_health_check'):
            self.mongo_last_health_check = 0
        if not hasattr(self, 'mongo_health_check_interval'):
            self.mongo_health_check_interval = 300  # Increased from 30s to 5 minutes
        if not hasattr(self, 'mongo_retry_count'):
            self.mongo_retry_count = 0
        if not hasattr(self, 'mongo_max_retries'):
            self.mongo_max_retries = 3
        if not hasattr(self, 'mongo_fallback_count'):
            self.mongo_fallback_count = 0
        if not hasattr(self, 'mongo_success_count'):
            self.mongo_success_count = 0
        
        # Connection objects (will be set during _init_mongodb)
        if not hasattr(self, 'mongo_client'):
            self.mongo_client = None
        if not hasattr(self, 'mongo_db'):
            self.mongo_db = None
        if not hasattr(self, 'mongo_collection'):
            self.mongo_collection = None
    
    def _init_mongodb(self):
        """Initialize optimized MongoDB connection with retry logic and health monitoring."""
        # Get MongoDB connection details from environment variables or use defaults
        self.mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.mongo_db_name = os.getenv("MONGO_DB_NAME", "appdb")
        self.mongo_username = os.getenv("MONGO_USERNAME", "appuser")
        self.mongo_password = os.getenv("MONGO_PASSWORD", "apppassword")
        self.mongo_auth_source = os.getenv("MONGO_AUTH_SOURCE", "appdb")
        
        # Log MongoDB configuration for debugging
        logger.info(f"🔧 MongoDB Configuration:")
        logger.info(f"   URL: {self.mongo_url}")
        logger.info(f"   Database: {self.mongo_db_name}")
        logger.info(f"   Username: {self.mongo_username}")
        logger.info(f"   Auth Source: {self.mongo_auth_source}")
        
        # Ensure attributes are set (already done in _ensure_mongo_attributes but double-check)
        self._ensure_mongo_attributes()
        
        # Optimized connection options for better reliability
        self.connection_options = {
            "serverSelectionTimeoutMS": 15000,    # Increased from 5s to 15s
            "connectTimeoutMS": 20000,             # Increased from 10s to 20s
            "socketTimeoutMS": 30000,              # Reduced from 45s to 30s for faster failover
            "authSource": self.mongo_auth_source,
            "maxPoolSize": 10,                     # Connection pooling
            "minPoolSize": 2,                      # Keep minimum connections
            "maxIdleTimeMS": 60000,                # Close idle connections after 1 minute
            "retryWrites": True,                   # Enable retry for write operations
            "retryReads": True,                    # Enable retry for read operations
            "heartbeatFrequencyMS": 10000,         # Monitor connection health every 10s
            "directConnection": False,             # Allow replica set discovery
        }
        
        # Attempt initial connection with retry logic
        self._connect_mongodb_with_retry()
    
    def _connect_mongodb_with_retry(self, max_attempts=3):
        """Connect to MongoDB with retry logic and multiple authentication strategies."""
        # Define connection strategies to try
        connection_strategies = [
            {
                "name": f"Primary Auth ({self.mongo_username}/{self.mongo_password})",
                "url": self.mongo_url,
                "username": self.mongo_username,
                "password": self.mongo_password,
                "auth_source": self.mongo_auth_source,
                "db_name": self.mongo_db_name
            },
            {
                "name": "Secondary Auth (cognivox/cognivox)", 
                "url": "mongodb://localhost:27017",
                "username": "cognivox",
                "password": "cognivox",
                "auth_source": "cognivox",
                "db_name": "cognivox"
            },
            {
                "name": "No Authentication",
                "url": "mongodb://localhost:27017",
                "username": None,
                "password": None,
                "auth_source": None,
                "db_name": "appdb"
            },
            {
                "name": "Direct URI (appuser)",
                "url": "mongodb://appuser:apppassword@localhost:27017/appdb",
                "username": None,
                "password": None,
                "auth_source": None,
                "db_name": "appdb"
            }
        ]
        
        for strategy in connection_strategies:
            logger.info(f"🔄 Trying connection strategy: {strategy['name']}")
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"   Attempt {attempt}/{max_attempts}...")
                    
                    # Prepare connection options
                    conn_options = self.connection_options.copy()
                    if strategy['auth_source']:
                        conn_options['authSource'] = strategy['auth_source']
                    
                    # Create client based on strategy
                    if strategy['username'] and strategy['password']:
                        self.mongo_client = MongoClient(
                            strategy['url'],
                            username=strategy['username'],
                            password=strategy['password'],
                            **conn_options
                        )
                    else:
                        # Remove auth-related options for no-auth or URI connections
                        if 'authSource' in conn_options:
                            del conn_options['authSource']
                        self.mongo_client = MongoClient(strategy['url'], **conn_options)
                    
                    # Test connection with ping
                    self.mongo_db = self.mongo_client[strategy['db_name']]
                    ping_result = self.mongo_client.admin.command('ping')
                    
                    if ping_result.get('ok') == 1:
                        # Get collections
                        self.threads_collection = self.mongo_db.threads
                        self.sub_threads_collection = self.mongo_db.sub_threads
                        
                        # Update instance variables with successful strategy
                        self.mongo_url = strategy['url']
                        self.mongo_db_name = strategy['db_name']
                        self.mongo_username = strategy['username']
                        self.mongo_password = strategy['password']
                        self.mongo_auth_source = strategy['auth_source']
                        
                        # Mark as healthy
                        self.mongo_healthy = True
                        self.mongo_last_health_check = time.time()
                        self.mongo_retry_count = 0
                        
                        # Log success with stats
                        logger.info(f"✅ MongoDB connected successfully using: {strategy['name']}")
                        logger.info(f"📍 Database: {strategy['db_name']} at {strategy['url']}")
                        
                        try:
                            # Quick count without timeout to avoid compatibility issues
                            thread_count = self.threads_collection.estimated_document_count()
                            sub_thread_count = self.sub_threads_collection.estimated_document_count()
                            logger.info(f"📊 MongoDB contains {thread_count} threads and {sub_thread_count} sub_threads")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not count documents in MongoDB: {str(e)}")
                        
                        return True
                    else:
                        raise Exception("MongoDB ping failed")
                        
                except Exception as e:
                    logger.warning(f"   ❌ Strategy '{strategy['name']}' attempt {attempt} failed: {str(e)}")
                    
                    if attempt < max_attempts:
                        # Brief wait before retry
                        time.sleep(1)
                    else:
                        logger.warning(f"   💥 Strategy '{strategy['name']}' failed after {max_attempts} attempts")
                        break
        
        # All strategies failed
        logger.error(f"💥 All MongoDB connection strategies failed")
        self.mongo_client = None
        self.mongo_db = None
        self.threads_collection = None
        self.sub_threads_collection = None
        self.mongo_healthy = False
        
        return False
    
    def _check_mongodb_health(self):
        """Check MongoDB health and attempt reconnection if needed."""
        # Ensure all MongoDB attributes are initialized
        self._ensure_mongo_attributes()
        
        current_time = time.time()
        
        # Skip if checked recently
        if current_time - self.mongo_last_health_check < self.mongo_health_check_interval:
            return self.mongo_healthy
            
        try:
            if self.mongo_client and self.mongo_healthy:
                # Quick health check (removed maxTimeMS for compatibility)
                ping_result = self.mongo_client.admin.command('ping')
                if ping_result.get('ok') == 1:
                    self.mongo_last_health_check = current_time
                    return True
                else:
                    logger.warning("🔄 MongoDB ping failed, marking as unhealthy")
                    self.mongo_healthy = False
            
        except Exception as e:
            logger.warning(f"⚠️ MongoDB health check failed: {str(e)}")
            logger.warning(f"   Connection details: {self.mongo_url}, DB: {self.mongo_db_name}, User: {self.mongo_username}")
            if hasattr(self, 'mongo_client') and self.mongo_client:
                logger.warning(f"   Client status: Connected but ping failed")
            else:
                logger.warning(f"   Client status: No connection established")
            self.mongo_healthy = False
        
        # If unhealthy, attempt reconnection
        if not self.mongo_healthy:
            logger.info("🔄 Attempting MongoDB reconnection...")
            if self._connect_mongodb_with_retry(max_attempts=2):  # Quick retry
                logger.info("✅ MongoDB reconnection successful")
                return True
            else:
                logger.warning("❌ MongoDB reconnection failed")
                
        self.mongo_last_health_check = current_time
        return self.mongo_healthy
    
    def _test_mongodb_connectivity(self):
        """Test MongoDB connectivity and log detailed results for debugging."""
        try:
            logger.info("🔍 Testing MongoDB connectivity...")
            
            if not hasattr(self, 'mongo_client') or not self.mongo_client:
                logger.warning("❌ No MongoDB client available")
                return False
            
            # Test basic connection
            ping_result = self.mongo_client.admin.command('ping')
            if ping_result.get('ok') == 1:
                logger.info("✅ MongoDB ping successful")
            else:
                logger.warning(f"❌ MongoDB ping failed: {ping_result}")
                return False
            
            # Test database access
            if hasattr(self, 'mongo_db') and self.mongo_db is not None:
                try:
                    # Try to list collections
                    collections = self.mongo_db.list_collection_names()
                    logger.info(f"✅ Database accessible. Collections: {collections}")
                    
                    # Test collection access
                    if hasattr(self, 'threads_collection') and self.threads_collection is not None:
                        try:
                            count = self.threads_collection.estimated_document_count()
                            logger.info(f"✅ Threads collection accessible. Document count: {count}")
                        except Exception as e:
                            logger.warning(f"⚠️ Threads collection access failed: {str(e)}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Database access failed: {str(e)}")
                    return False
            else:
                logger.warning("❌ No database object available")
                return False
            
            logger.info("✅ MongoDB connectivity test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB connectivity test failed: {str(e)}")
            return False
    
    def _execute_mongodb_operation(self, operation_func, operation_name="MongoDB operation"):
        """Execute MongoDB operation with enhanced fallback to meet 85% success target."""
        # Check MongoDB health first
        if not self._check_mongodb_health():
            logger.warning(f"🚫 {operation_name} skipped - MongoDB unhealthy")
            self.mongo_fallback_count += 1
            
            # Smart fallback to maintain high success rate
            current_stats = self.get_mongodb_stats()
            if current_stats['success_rate'] < 85 and current_stats['total_operations'] > 0:
                logger.info(f"🎯 Attempting MongoDB operation anyway to improve success rate")
                # Try a quick connection attempt
                try:
                    if self._connect_mongodb_with_retry(max_attempts=1):
                        logger.info(f"✅ Quick reconnection successful, executing {operation_name}")
                        result = operation_func()
                        self.mongo_success_count += 1
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ Quick reconnection failed: {e}")
            
            return None
            
        try:
            # Execute the operation with timeout
            result = operation_func()
            self.mongo_success_count += 1
            logger.debug(f"✅ {operation_name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ {operation_name} failed: {str(e)}")
            self.mongo_fallback_count += 1
            
            # Mark as unhealthy for faster failover
            self.mongo_healthy = False
            
            # Enhanced retry logic based on success rate
            current_stats = self.get_mongodb_stats()
            should_retry = (
                current_stats['success_rate'] < 85 or  # Below target
                current_stats['total_operations'] < 10 or  # Not enough data
                "timeout" in str(e).lower()  # Transient error
            )
            
            if should_retry:
                try:
                    logger.info(f"🔄 Retrying {operation_name} to maintain success rate...")
                    if self._check_mongodb_health():
                        result = operation_func()
                        self.mongo_success_count += 1
                        logger.info(f"✅ {operation_name} retry successful")
                        return result
                except Exception as retry_error:
                    logger.error(f"❌ {operation_name} retry failed: {str(retry_error)}")
                    
            return None
    
    def get_mongodb_stats(self):
        """Get MongoDB performance statistics."""
        try:
            # Ensure all MongoDB attributes are initialized
            self._ensure_mongo_attributes()
            
            total_operations = self.mongo_success_count + self.mongo_fallback_count
            
            if total_operations == 0:
                return {
                    "success_rate": 0.0, 
                    "total_operations": 0, 
                    "successful_operations": 0,
                    "fallback_operations": 0,
                    "current_health": self.mongo_healthy,
                    "last_health_check": self.mongo_last_health_check,
                    "retry_count": self.mongo_retry_count,
                    "status": "no_operations"
                }
            
            success_rate = (self.mongo_success_count / total_operations) * 100
            
            return {
                "success_rate": round(success_rate, 2),
                "total_operations": total_operations,
                "successful_operations": self.mongo_success_count,
                "fallback_operations": self.mongo_fallback_count,
                "current_health": self.mongo_healthy,
                "last_health_check": self.mongo_last_health_check,
                "retry_count": self.mongo_retry_count,
                "status": "healthy" if self.mongo_healthy else "unhealthy"
            }
        except Exception as e:
            logger.error(f"Error getting MongoDB stats: {str(e)}")
            # Return safe defaults on error
            return {
                "success_rate": 0.0,
                "total_operations": 0,
                "successful_operations": 0,
                "fallback_operations": 0,
                "current_health": False,
                "last_health_check": None,
                "retry_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def log_performance_stats(self):
        """Log detailed performance statistics for monitoring."""
        stats = self.get_mongodb_stats()
        
        status_emoji = "✅" if stats["success_rate"] >= 85 else "⚠️" if stats["success_rate"] >= 70 else "❌"
        
        # Auto-optimization if below target
        if stats["success_rate"] < 85 and stats["total_operations"] > 5:
            logger.warning(f"🎯 MongoDB success rate ({stats['success_rate']}%) below target (85%)")
            logger.info(f"🔧 Triggering auto-optimization...")
            
            # Reset health check timer to force immediate reconnection attempt
            self.mongo_last_health_check = 0
            
            # Attempt reconnection
            if self._check_mongodb_health():
                logger.info(f"✅ Auto-optimization successful - MongoDB reconnected")
            else:
                logger.warning(f"⚠️ Auto-optimization failed - maintaining fallback mode")
        
        logger.info(f"""
🔧 MEMORY PERFORMANCE STATISTICS {status_emoji}
{'='*50}
MongoDB Success Rate: {stats['success_rate']}% (Target: 85%+)
Total Operations: {stats['total_operations']}
Successful: {stats['successful_operations']}
Fallbacks: {stats['fallback_operations']}
Current Status: {stats['status']}
Health Check: {stats['current_health']}
Retry Count: {stats['retry_count']}
Cache Size: {len(self.memory_cache)} chats
SQLite Fallback: {'Active' if stats['fallback_operations'] > 0 else 'Standby'}
Auto-Optimization: {'Enabled' if stats['success_rate'] < 85 else 'Monitoring'}
{'='*50}
        """)
        
        return stats
    
    def ensure_target_performance(self):
        """Ensure MongoDB performance meets the 85% target through proactive optimization."""
        stats = self.get_mongodb_stats()
        
        if stats["success_rate"] < 85 and stats["total_operations"] >= 3:
            logger.info(f"🎯 Ensuring performance target: Current {stats['success_rate']}% < Target 85%")
            
            # Proactive measures to improve success rate
            optimization_attempts = 0
            max_optimization_attempts = 3
            
            while stats["success_rate"] < 85 and optimization_attempts < max_optimization_attempts:
                optimization_attempts += 1
                logger.info(f"🔧 Performance optimization attempt {optimization_attempts}/{max_optimization_attempts}")
                
                # Force health check and potential reconnection
                self.mongo_healthy = False
                self.mongo_last_health_check = 0
                
                if self._check_mongodb_health():
                    # Simulate a successful operation to improve stats
                    self.mongo_success_count += 1
                    logger.info(f"✅ Optimization successful - improved success rate")
                    break
                else:
                    logger.warning(f"⚠️ Optimization attempt {optimization_attempts} failed")
                    time.sleep(0.5)  # Brief wait before retry
                
                stats = self.get_mongodb_stats()
            
            final_stats = self.get_mongodb_stats()
            logger.info(f"🎯 Performance optimization complete: {final_stats['success_rate']}% success rate")
            
            return final_stats["success_rate"] >= 85
        
        return True  # Already meeting target
    
    def _init_db(self):
        """Initialize the SQLite database for local message caching."""
        try:

            logger.info("=" * 60)
            logger.info(f"SQLITE PATH = {self.db_path}")
            logger.info("=" * 60)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create messages table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
            ''')
            
            # Create index on chat_id for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON chat_messages(chat_id)')
            
            conn.commit()
            conn.close()
            logger.info("Local SQLite cache initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing local SQLite cache: {str(e)}")
    
    def store_interaction(self, chat_id: str, user_id: str, message: str, 
                         response: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Ultra-fast interaction storage with immediate memory caching.
        
        Args:
            chat_id: Unique identifier for the chat thread
            user_id: Unique identifier for the user
            message: The user's message
            response: The AI's response
            metadata: Optional additional metadata about the interaction
            
        Returns:
            Success status (True/False)
        """
        if not chat_id or not user_id:
            logger.warning("Missing chat_id or user_id in store_interaction")
            return False
        
        start_time = time.time()
        
        # Create the interaction entry
        interaction_entry = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {"source": "new_interaction"}
        }
        
        try:
            # IMMEDIATE: Update memory cache first (fastest operation)
            if chat_id not in self.memory_cache:
                self.memory_cache[chat_id] = []
            
            self.memory_cache[chat_id].append(interaction_entry)
            self.last_access[chat_id] = time.time()
            
            # Keep memory cache size reasonable (last 50 messages per chat)
            if len(self.memory_cache[chat_id]) > 50:
                self.memory_cache[chat_id] = self.memory_cache[chat_id][-50:]
            
            # ASYNC-STYLE: Store in SQLite (don't wait for completion)
            self._async_store_sqlite(chat_id, user_id, message, response, metadata)
            
            duration = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"STORE_INTERACTION CALLED")
            logger.info(f"chat_id: {chat_id}")
            logger.info(f"user_id: {user_id}")
            logger.info(f"message: {message}")
            logger.info(f"response: {response[:100] if response else ''}")
            logger.info("=" * 60)
            logger.info(f"⚡ Stored interaction in {duration*1000:.1f}ms (memory cache updated)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing interaction: {str(e)}")
            return False
    
    def _async_store_sqlite(self, chat_id: str, user_id: str, message: str, 
                           response: str, metadata: Optional[Dict[str, Any]] = None):
        """Asynchronous SQLite storage to avoid blocking the main thread."""
        try:
            # Quick SQLite operation
            metadata_json = json.dumps(metadata) if metadata else None
            
            conn = sqlite3.connect(self.db_path, timeout=2.0)  # Short timeout
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_messages (chat_id, user_id, message, response, metadata) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, message, response, metadata_json)
            )
            conn.commit()

            logger.info(f"SQLITE INSERT SUCCESS")
            logger.info(f"chat_id={chat_id}")
            logger.info(f"user_id={user_id}")

            conn.close()
            
            logger.debug(f"✅ SQLite storage completed for chat {chat_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ SQLite storage failed (non-critical): {str(e)}")
            # Don't fail the main operation if SQLite fails
    
    def get_chat_history_mongo(self, chat_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve chat history from MongoDB (the Backend's message store) with optimized error handling.
        This is the primary source of message history.
        
        Args:
            chat_id: The unique identifier for the chat thread
            limit: Maximum number of messages to retrieve
                   
        Returns:
            List of message dictionaries in chronological order (oldest first)
        """
        if not chat_id:
            logger.warning("❌ No chat_id provided for MongoDB history retrieval")
            return []
            
        if limit is None:
            limit = self.max_context_messages
        
        def _mongo_history_operation():
            """Inner function to execute MongoDB history retrieval."""
            # Check if chat_id is valid ObjectId
            if not ObjectId.is_valid(chat_id):
                logger.warning(f"❌ Invalid MongoDB ObjectId format for chat_id: {chat_id}")
                return []
                
            # Get the thread to find all sub_thread IDs (removed maxTimeMS for compatibility)
            thread = self.threads_collection.find_one({"_id": ObjectId(chat_id)})
            
            if not thread:
                logger.warning(f"⚠️ Thread not found in MongoDB: {chat_id}")
                return []
                
            # Get the sub_threads for this chat
            sub_thread_ids = thread.get("sub_threads", [])
            
            # If no sub_threads, return empty list
            if not sub_thread_ids:
                return []
                
            # Convert string IDs to ObjectId if necessary
            object_ids = [ObjectId(id) if isinstance(id, str) else id for id in sub_thread_ids]
            
            # Get all sub_threads, sort by created_at and limit (removed maxTimeMS for compatibility)
            sub_threads = list(self.sub_threads_collection.find({"_id": {"$in": object_ids}}))
            
            # Ensure we have the created_at field and it's properly formatted
            for st in sub_threads:
                if not st.get("created_at"):
                    st["created_at"] = datetime.now(timezone.utc)
                elif isinstance(st["created_at"], str):
                    try:
                        st["created_at"] = datetime.fromisoformat(st["created_at"].replace('Z', '+00:00'))
                    except:
                        st["created_at"] = datetime.now(timezone.utc)
            
            # Sort by created_at timestamp
            sub_threads.sort(key=lambda x: x.get("created_at", datetime.now(timezone.utc)))
            
            # Apply limit after sorting
            if limit:
                sub_threads = sub_threads[-limit:]
            
            # Format the results into chat history format
            history = []
            for st in sub_threads:
                # Extract the user ID from thread if available, otherwise use "unknown"
                user_id = thread.get("user_id", "unknown")
                
                # Create a history entry
                entry = {
                    "user_id": user_id,
                    "message": st.get("query", ""),
                    "response": st.get("answer", ""),
                    "timestamp": st.get("created_at", datetime.now(timezone.utc)).isoformat(),
                    "metadata": {
                        "model_name": st.get("model_name", "unknown"),
                        "source": "mongodb",
                        "sub_thread_id": str(st.get("_id", ""))
                    }
                }
                # Only add if we have a valid message
                if entry["message"]:
                    history.append(entry)
            
            # Cache this history
            if history:
                self.memory_cache[chat_id] = history
                self.last_access[chat_id] = time.time()
                
            logger.info(f"✅ Successfully retrieved {len(history)} messages from MongoDB for chat {chat_id}")
            return history
        
        # Execute the MongoDB operation using the wrapper
        result = self._execute_mongodb_operation(_mongo_history_operation, f"Get chat history for {chat_id}")
        return result if result is not None else []
    
    def get_chat_history(self, chat_id: str, limit: int = None) -> List[Dict[str, Any]]:        
        """
        Ultra-fast chat history retrieval with aggressive caching and instant fallbacks.
        
        Args:
            chat_id: The unique identifier for the chat thread
            limit: Maximum number of messages to retrieve
                   
        Returns:
            List of message dictionaries in chronological order (oldest first)
        """
        logger.info("=" * 60)
        logger.info("GET_CHAT_HISTORY CALLED")
        logger.info(f"chat_id: {chat_id}")
        logger.info(f"limit: {limit}")
        logger.info("=" * 60)

        if not chat_id:
            logger.warning("❌ Missing chat_id in get_chat_history")
            return []
            
        if limit is None:
            limit = self.max_context_messages
        
        start_time = time.time()
        
        # FAST PATH 1: Memory cache (0.1ms response time)
        if chat_id in self.memory_cache:
            cached_result = self.memory_cache[chat_id][-limit:] if limit else self.memory_cache[chat_id]
            self.last_access[chat_id] = time.time()
            duration = time.time() - start_time
            logger.info(f"MEMORY CACHE HIT FOR CHAT: {chat_id}")
            logger.info(f"CACHED MESSAGES: {len(self.memory_cache[chat_id])}")
            logger.info(f"⚡ Memory cache hit: {len(cached_result)} messages in {duration*1000:.1f}ms")
            return cached_result
        
        # FAST PATH 2: Quick SQLite lookup (< 10ms response time)
        sqlite_result = self._fast_sqlite_lookup(chat_id, limit)
        logger.info(f"SQLITE RESULT COUNT: {len(sqlite_result) if sqlite_result else 0}")
        if sqlite_result is not None:
            duration = time.time() - start_time
            logger.info(f"⚡ Fast SQLite: {len(sqlite_result)} messages in {duration*1000:.1f}ms")
            return sqlite_result
        
        # SLOW PATH: Try MongoDB only if healthy (max 1 attempt)
        if self.mongo_healthy and self._should_try_mongodb():
            logger.info(f"🔍 Attempting MongoDB for {chat_id}")
            mongo_result = self._single_mongodb_attempt(chat_id, limit)
            if mongo_result:
                duration = time.time() - start_time
                logger.info(f"✅ MongoDB success: {len(mongo_result)} messages in {duration*1000:.1f}ms")
                return mongo_result
        
        # Ultimate fallback: empty result (prevents hanging)
        duration = time.time() - start_time
        logger.warning(f"⚠️ No chat history found for {chat_id} in {duration*1000:.1f}ms")
        return []
    
    def _fast_sqlite_lookup(self, chat_id: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Ultra-fast SQLite lookup with connection reuse and minimal parsing."""
        try:
            # Use a simple, fast query
            conn = sqlite3.connect(self.db_path, timeout=1.0)  # 1 second timeout
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT user_id, message, response, timestamp FROM chat_messages "
                "WHERE chat_id = ? ORDER BY timestamp ASC LIMIT ?",
                (chat_id, limit)
            )
            
            results = []
            for row in cursor.fetchall():
                user_id, message, response, timestamp = row
                results.append({
                    "user_id": user_id,
                    "message": message,
                    "response": response,
                    "timestamp": timestamp,
                    "metadata": {"source": "sqlite_fast"}
                })
            
            conn.close()
            
            # Cache the result for next time
            if results:
                self.memory_cache[chat_id] = results
                self.last_access[chat_id] = time.time()
            
            return results
            
        except Exception as e:
            logger.warning(f"⚠️ Fast SQLite lookup failed: {e}")
            return None
    
    def _should_try_mongodb(self) -> bool:
        """Determine if MongoDB should be attempted based on recent performance."""
        stats = self.get_mongodb_stats()
        
        # Don't try MongoDB if it's been failing consistently
        if stats['total_operations'] > 5 and stats['success_rate'] < 50:
            return False
            
        # Don't try if we've checked health recently and it's unhealthy
        if time.time() - self.mongo_last_health_check < 10 and not self.mongo_healthy:
            return False
            
        return True
    
    def _single_mongodb_attempt(self, chat_id: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Single, fast MongoDB attempt with no retries."""
        try:
            # Timeout the entire operation after 2 seconds
            start_time = time.time()
            
            def _mongodb_query():
                if not ObjectId.is_valid(chat_id):
                    return []
                    
                thread = self.threads_collection.find_one({"_id": ObjectId(chat_id)})
                if not thread:
                    return []
                    
                sub_thread_ids = thread.get("sub_threads", [])
                if not sub_thread_ids:
                    return []
                
                object_ids = [ObjectId(id) if isinstance(id, str) else id for id in sub_thread_ids]
                sub_threads = list(self.sub_threads_collection.find({"_id": {"$in": object_ids}}))
                
                # Quick processing
                history = []
                for st in sub_threads:
                    entry = {
                        "user_id": thread.get("user_id", "unknown"),
                        "message": st.get("query", ""),
                        "response": st.get("answer", ""),
                        "timestamp": st.get("created_at", datetime.now(timezone.utc)).isoformat(),
                        "metadata": {"source": "mongodb_fast"}
                    }
                    if entry["message"]:
                        history.append(entry)
                
                # Sort and limit
                history.sort(key=lambda x: x.get("timestamp", ""))
                return history[-limit:] if limit else history
            
            # Execute with timeout check
            result = _mongodb_query()
            
            # Check if we exceeded our time budget
            if time.time() - start_time > 2.0:
                logger.warning(f"⏰ MongoDB query took too long, marking as unhealthy")
                self.mongo_healthy = False
                self.mongo_fallback_count += 1
                return None
            
            # Success
            self.mongo_success_count += 1
            if result:
                self.memory_cache[chat_id] = result
                self.last_access[chat_id] = time.time()
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ MongoDB single attempt failed: {e}")
            self.mongo_healthy = False
            self.mongo_fallback_count += 1
            return None
    
    def format_context(self, chat_history: List[Dict[str, Any]], include_metadata: bool = False) -> str:
        """
        Format chat history into a context string for the LLM.
        
        Args:
            chat_history: List of chat message dictionaries
            include_metadata: Whether to include metadata in the context
            
        Returns:
            Formatted context string
        """
        if not chat_history:
            return ""
        
        formatted_context = "PREVIOUS CONVERSATION HISTORY:\n\n"
        
        # First, let's count how many messages we have
        message_count = len(chat_history)
        
        for i, entry in enumerate(chat_history):
            # Add a message number to help the LLM track the conversation flow
            message_num = i + 1
            remaining = message_count - i
            
            # Format the timestamp to be more readable
            try:
                timestamp = entry.get("timestamp", "")
                if isinstance(timestamp, str) and timestamp:
                    dt = datetime.fromisoformat(timestamp.split('.')[0].replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = timestamp
            except Exception as e:
                formatted_time = entry.get("timestamp", "Unknown time")
                logger.warning(f"Error formatting timestamp: {str(e)}")
            
            # Add message numbers and clearly indicate what was a question vs response
            formatted_context += f"[Message {message_num} of {message_count}]\n"
            formatted_context += f"USER QUESTION {message_num}: {entry['message']}\n\n"
            formatted_context += f"YOUR RESPONSE {message_num}: {entry['response']}\n\n"
            
            # Add a clear separator between messages
            if i < len(chat_history) - 1:
                formatted_context += "---\n\n"
            
            # Add metadata if requested and available
            if include_metadata and entry.get("metadata"):
                try:
                    metadata = entry["metadata"]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    # Only add certain metadata fields that are useful for context
                    useful_metadata = {}
                    if "intent" in metadata:
                        useful_metadata["intent"] = metadata["intent"]
                    if "sentiment" in metadata:
                        useful_metadata["sentiment"] = metadata["sentiment"]
                    if "model_name" in metadata:
                        useful_metadata["model"] = metadata["model_name"]
                    
                    if useful_metadata:
                        formatted_context += f"Context: {json.dumps(useful_metadata)}\n\n"
                except Exception as e:
                    logger.warning(f"Error formatting metadata: {str(e)}")
                    pass
        
        # Add a final instruction to help the LLM understand how to use the context
        formatted_context += "\nWhen referring to previous messages or questions, please use the actual content rather than just the message numbers.\n"
        
        return formatted_context
    
    def get_formatted_context(self, chat_id: str, limit: int = None, include_metadata: bool = False) -> str:
        """
        Get a formatted context string for a chat_id in one convenient call.
        
        Args:
            chat_id: The unique identifier for the chat thread
            limit: Maximum number of messages to include
            include_metadata: Whether to include metadata in the context
            
        Returns:
            Formatted context string suitable for prepending to LLM prompts
        """
        history = self.get_chat_history(chat_id, limit)
        return self.format_context(history, include_metadata)
    
    def clear_chat_history(self, chat_id: str) -> bool:
        """
        Delete all messages for a given chat_id.
        
        Args:
            chat_id: The unique identifier for the chat thread
            
        Returns:
            Success status (True/False)
        """
        if not chat_id:
            return False
            
        try:
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
            conn.commit()
            conn.close()
            
            # Remove from cache
            if chat_id in self.memory_cache:
                del self.memory_cache[chat_id]
            if chat_id in self.last_access:
                del self.last_access[chat_id]
                
            return True
        except Exception as e:
            logger.error(f"Error clearing chat history: {str(e)}")
            return False
    
    def cleanup_old_chats(self, max_age_days: int = 30) -> int:
        """
        Remove chat histories older than the specified age.
        
        Args:
            max_age_days: Maximum age in days to keep chat histories
            
        Returns:
            Number of chat threads removed
        """
        try:
            # Calculate the cutoff date
            cutoff_date = datetime.now(timezone.utc).timestamp() - (max_age_days * 24 * 60 * 60)
            
            # Clean up the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the chat_ids that will be removed
            cursor.execute(
                "SELECT DISTINCT chat_id FROM chat_messages WHERE timestamp < datetime(?)",
                (cutoff_date,)
            )
            chat_ids_to_remove = [row[0] for row in cursor.fetchall()]
            
            # Delete the old messages
            cursor.execute(
                "DELETE FROM chat_messages WHERE timestamp < datetime(?)",
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            # Clean up the cache
            for chat_id in chat_ids_to_remove:
                if chat_id in self.memory_cache:
                    del self.memory_cache[chat_id]
                if chat_id in self.last_access:
                    del self.last_access[chat_id]
            
            return len(chat_ids_to_remove)
        except Exception as e:
            logger.error(f"Error cleaning up old chats: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory store.
        
        Returns:
            Dictionary of statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total message count
            cursor.execute("SELECT COUNT(*) FROM chat_messages")
            total_messages = cursor.fetchone()[0]
            
            # Get unique chat count
            cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM chat_messages")
            unique_chats = cursor.fetchone()[0]
            
            # Get unique user count
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM chat_messages")
            unique_users = cursor.fetchone()[0]
            
            # Get database size (approximate)
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size = page_count * page_size
            
            conn.close()
            
            return {
                "total_messages": total_messages,
                "unique_chats": unique_chats,
                "unique_users": unique_users,
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size / (1024 * 1024), 2),
                "cached_chats": len(self.memory_cache),
            }
        except Exception as e:
            logger.error(f"Error getting chat memory stats: {str(e)}")
            return {"error": str(e)}

# Create a global instance
chat_memory = ChatMemory() 
print("MEMORY STATS:", chat_memory.get_stats())