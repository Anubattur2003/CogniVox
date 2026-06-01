"""
Thinking Tracker utility for managing thinking states across the application.
"""
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from collections import defaultdict

# Configure logging
logger = logging.getLogger("cogniVox")

class ThinkingTracker:
    """Centralized tracker for managing thinking states across all agents."""
    
    def __init__(self):
        """Initialize the thinking tracker."""
        self.thinking_states: Dict[str, Dict[str, Any]] = {}
        self.thinking_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.max_history_per_user = 10
    
    def start_thinking(self, user_id: str, process_type: str = "reasoning", description: str = "Processing your request...") -> str:
        """Start a thinking process for a user."""
        session_id = f"{user_id}_{int(time.time() * 1000)}"
        
        thinking_state = {
            "session_id": session_id,
            "user_id": user_id,
            "process_type": process_type,
            "description": description,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "steps": [],
            "current_step": {
                "step_name": "initializing",
                "description": description,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        self.thinking_states[session_id] = thinking_state
        logger.info(f"Started thinking process for user {user_id}: {process_type}")
        
        return session_id
    
    def update_thinking_step(self, session_id: str, step_name: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        """Update the current thinking step."""
        if session_id not in self.thinking_states:
            logger.warning(f"Thinking session {session_id} not found")
            return
        
        state = self.thinking_states[session_id]
        
        # Archive the previous step
        if state["current_step"]:
            state["steps"].append(state["current_step"])
        
        # Update current step
        current_step = {
            "step_name": step_name,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        
        state["current_step"] = current_step
        state["description"] = description
        
        logger.debug(f"Updated thinking step for session {session_id}: {step_name}")
    
    def finish_thinking(self, session_id: str, final_result: Optional[str] = None, success: bool = True):
        """Finish a thinking process."""
        if session_id not in self.thinking_states:
            return
        
        state = self.thinking_states[session_id]
        
        # Archive final step
        if state["current_step"]:
            state["steps"].append(state["current_step"])
        
        # Mark as complete
        state["is_active"] = False
        state["end_time"] = datetime.now(timezone.utc).isoformat()
        state["success"] = success
        state["final_result"] = final_result
        state["current_step"] = {
            "step_name": "completed" if success else "failed",
            "description": "Thinking process completed" if success else "Thinking process failed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add to history
        user_id = state["user_id"]
        self.thinking_history[user_id].append(state.copy())
        
        # Trim history if too long
        if len(self.thinking_history[user_id]) > self.max_history_per_user:
            self.thinking_history[user_id] = self.thinking_history[user_id][-self.max_history_per_user:]
        
        logger.info(f"Finished thinking process for session {session_id}: {'success' if success else 'failure'}")
    
    def get_current_thinking(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the current active thinking state for a user."""
        # Find active thinking sessions for this user
        active_sessions = [
            state for state in self.thinking_states.values()
            if state["user_id"] == user_id and state["is_active"]
        ]
        
        if not active_sessions:
            return None
        
        # Return the most recent active session
        return max(active_sessions, key=lambda x: x["start_time"])
    
    def clear_user_thinking(self, user_id: str):
        """Clear all thinking states and history for a user."""
        # Remove active sessions
        sessions_to_remove = [
            session_id for session_id, state in self.thinking_states.items()
            if state["user_id"] == user_id
        ]
        
        for session_id in sessions_to_remove:
            del self.thinking_states[session_id]
        
        # Clear history
        if user_id in self.thinking_history:
            del self.thinking_history[user_id]
        
        logger.info(f"Cleared thinking data for user {user_id}")

# Global thinking tracker instance
thinking_tracker = ThinkingTracker() 