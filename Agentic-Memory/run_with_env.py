#!/usr/bin/env python
"""
Runner script for Memory service with environment variables set.
"""
import os
import sys
import subprocess
import time
import pymongo
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("memory-starter")

# Set environment variables
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["MONGO_DB_NAME"] = "appdb"
os.environ["MONGO_USERNAME"] = "appuser"
os.environ["MONGO_PASSWORD"] = "apppassword"
os.environ["MONGO_AUTH_SOURCE"] = "appdb"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["DEFAULT_MODEL"] = "llama3.1"

# Print the environment variables (for debugging)
print("Running Memory service with environment:")
print(f"MongoDB URL: {os.environ['MONGO_URL']}")
print(f"MongoDB Name: {os.environ['MONGO_DB_NAME']}")
print(f"MongoDB User: {os.environ['MONGO_USERNAME']}")
print(f"Auth Source: {os.environ['MONGO_AUTH_SOURCE']}")
print(f"Ollama URL: {os.environ['OLLAMA_BASE_URL']}")
print(f"Default Model: {os.environ['DEFAULT_MODEL']}")

def test_mongodb_connection(max_retries=3, delay=2):
    """Test MongoDB connection and retry if needed"""
    mongo_url = os.environ["MONGO_URL"]
    mongo_db_name = os.environ["MONGO_DB_NAME"]
    mongo_username = os.environ["MONGO_USERNAME"]
    mongo_password = os.environ["MONGO_PASSWORD"]
    mongo_auth_source = os.environ["MONGO_AUTH_SOURCE"]
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Testing MongoDB connection (attempt {attempt}/{max_retries})...")
            client = pymongo.MongoClient(
                mongo_url,
                username=mongo_username,
                password=mongo_password,
                authSource=mongo_auth_source,
                serverSelectionTimeoutMS=5000
            )
            
            # Force a connection attempt
            client.admin.command('ping')
            
            # Test collections
            db = client[mongo_db_name]
            threads = db.threads
            sub_threads = db.sub_threads
            
            # Get collection stats
            thread_count = threads.count_documents({})
            subthread_count = sub_threads.count_documents({})
            
            logger.info(f"MongoDB connection successful. Found {thread_count} threads and {subthread_count} sub_threads.")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("All MongoDB connection attempts failed!")
                return False

# Run the main.py script
if __name__ == "__main__":
    # Test MongoDB connection first
    mongodb_ok = test_mongodb_connection()
    
    if mongodb_ok:
        logger.info("MongoDB connection verified, starting Memory service...")
    else:
        logger.warning("Starting Memory service despite MongoDB connection issues...")
        
    # Forward any command line arguments
    args = sys.argv[1:] 
    main_script = os.path.join(os.path.dirname(__file__), "main.py")
    cmd = [sys.executable, main_script] + args
    
    print("\nStarting Memory service...")
    subprocess.run(cmd) 