"""
Performance Monitoring and GPU Acceleration Utilities
Provides comprehensive latency tracking and GPU optimization for RTX 3050
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass
from collections import defaultdict, deque
import os
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    gpu_used: bool = False
    parallel: bool = False
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system with GPU acceleration tracking.
    Designed for RTX 3050 optimization.
    """
    
    def __init__(self):
        self._metrics: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self._active_operations: Dict[str, float] = {}
        self._operation_stats: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._gpu_enabled = os.getenv("ENABLE_GPUS", "FALSE").upper() == "TRUE"
        
        # Performance thresholds (in milliseconds)
        self.thresholds = {
            "memory_retrieval": 50,     # < 50ms for memory operations
            "context_preparation": 100,  # < 100ms for context fetching
            "agent_processing": 5000,    # < 5s for agent responses
            "gpu_operation": 20,         # < 20ms for GPU operations
            "total_response": 15000      # < 15s total response time
        }
        
        logger.info(f"🔧 Performance Monitor initialized (GPU: {'Enabled' if self._gpu_enabled else 'Disabled'})")
    
    @contextmanager
    def measure_operation(self, operation_name: str, user_id: Optional[str] = None, 
                         gpu_used: bool = False, parallel: bool = False, 
                         metadata: Optional[Dict[str, Any]] = None):
        """Context manager for measuring operation performance"""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}_{threading.get_ident()}"
        
        start_time = time.time()
        with self._lock:
            self._active_operations[operation_id] = start_time
        
        try:
            yield operation_id
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Create metric
            metric = PerformanceMetric(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                gpu_used=gpu_used,
                parallel=parallel,
                user_id=user_id,
                metadata=metadata
            )
            
            with self._lock:
                self._metrics.append(metric)
                self._operation_stats[operation_name].append(duration_ms)
                # Keep only last 100 measurements per operation
                if len(self._operation_stats[operation_name]) > 100:
                    self._operation_stats[operation_name] = self._operation_stats[operation_name][-100:]
                
                # Remove from active operations
                self._active_operations.pop(operation_id, None)
            
            # Performance logging
            status = self._get_performance_status(operation_name, duration_ms)
            emoji = "⚡" if status == "excellent" else "✅" if status == "good" else "⚠️" if status == "slow" else "❌"
            gpu_indicator = " 🚀" if gpu_used else ""
            parallel_indicator = " ⚡⚡" if parallel else ""
            
            logger.info(f"{emoji} {operation_name}: {duration_ms:.1f}ms{gpu_indicator}{parallel_indicator}")
            
            # Alert on performance issues
            if status == "critical":
                logger.warning(f"🚨 PERFORMANCE ALERT: {operation_name} took {duration_ms:.1f}ms (threshold: {self.thresholds.get(operation_name, 1000)}ms)")
    
    def _get_performance_status(self, operation_name: str, duration_ms: float) -> str:
        """Determine performance status based on thresholds"""
        threshold = self.thresholds.get(operation_name, 1000)
        
        if duration_ms <= threshold * 0.5:
            return "excellent"
        elif duration_ms <= threshold:
            return "good"
        elif duration_ms <= threshold * 2:
            return "slow"
        else:
            return "critical"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self._lock:
            stats = {}
            
            for operation_name, durations in self._operation_stats.items():
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                    p95_duration = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 5 else max_duration
                    
                    stats[operation_name] = {
                        "count": len(durations),
                        "avg_ms": round(avg_duration, 1),
                        "min_ms": round(min_duration, 1),
                        "max_ms": round(max_duration, 1),
                        "p95_ms": round(p95_duration, 1),
                        "threshold_ms": self.thresholds.get(operation_name, 1000),
                        "performance_score": self._calculate_performance_score(operation_name, avg_duration)
                    }
            
            # Overall system performance
            total_metrics = len(self._metrics)
            gpu_accelerated = sum(1 for m in self._metrics if m.gpu_used)
            parallel_operations = sum(1 for m in self._metrics if m.parallel)
            
            stats["system_overview"] = {
                "total_operations": total_metrics,
                "gpu_accelerated_operations": gpu_accelerated,
                "parallel_operations": parallel_operations,
                "gpu_usage_percentage": round((gpu_accelerated / total_metrics * 100) if total_metrics > 0 else 0, 1),
                "parallel_usage_percentage": round((parallel_operations / total_metrics * 100) if total_metrics > 0 else 0, 1),
                "gpu_enabled": self._gpu_enabled,
                "active_operations": len(self._active_operations)
            }
            
            return stats
    
    def _calculate_performance_score(self, operation_name: str, avg_duration: float) -> str:
        """Calculate performance score (A-F scale)"""
        threshold = self.thresholds.get(operation_name, 1000)
        ratio = avg_duration / threshold
        
        if ratio <= 0.3:
            return "A+"
        elif ratio <= 0.5:
            return "A"
        elif ratio <= 0.7:
            return "B"
        elif ratio <= 1.0:
            return "C"
        elif ratio <= 1.5:
            return "D"
        else:
            return "F"
    
    def get_recent_metrics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent performance metrics"""
        with self._lock:
            recent = list(self._metrics)[-limit:]
            return [
                {
                    "operation": m.operation_name,
                    "duration_ms": round(m.duration_ms, 1),
                    "timestamp": m.start_time,
                    "gpu_used": m.gpu_used,
                    "parallel": m.parallel,
                    "user_id": m.user_id,
                    "metadata": m.metadata
                }
                for m in recent
            ]
    
    def clear_metrics(self):
        """Clear all stored metrics"""
        with self._lock:
            self._metrics.clear()
            self._operation_stats.clear()
            logger.info("📊 Performance metrics cleared")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def measure_performance(operation_name: str, gpu_used: bool = False, 
                       parallel: bool = False, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for measuring function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id if available
            user_id = kwargs.get('user_id') or (args[0] if args and hasattr(args[0], 'user_id') else None)
            
            with performance_monitor.measure_operation(
                operation_name=operation_name,
                user_id=str(user_id) if user_id else None,
                gpu_used=gpu_used,
                parallel=parallel,
                metadata=metadata
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator

class GPUAccelerator:
    """
    GPU acceleration utilities optimized for RTX 3050.
    Provides CUDA-accelerated text processing and embeddings.
    """
    
    def __init__(self):
        self.device = None
        self.enabled = False
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU acceleration if available"""
        try:
            import torch
            
            if torch.cuda.is_available() and os.getenv("ENABLE_GPUS", "FALSE").upper() == "TRUE":
                device_id = int(os.getenv("CUDA_VISIBLE_DEVICES", "0"))
                self.device = torch.device(f"cuda:{device_id}")
                
                # Check RTX 3050 specific optimizations
                gpu_name = torch.cuda.get_device_name(device_id)
                self.enabled = True
                
                # RTX 3050 has 4GB VRAM - optimize accordingly
                torch.cuda.empty_cache()
                
                logger.info(f"🚀 GPU Acceleration enabled: {gpu_name} (Device {device_id})")
                logger.info(f"🚀 GPU Memory: {torch.cuda.get_device_properties(device_id).total_memory / 1024**3:.1f}GB")
                
            else:
                logger.info("💻 GPU acceleration disabled, using CPU")
                
        except ImportError:
            logger.warning("⚠️ PyTorch not available, GPU acceleration disabled")
        except Exception as e:
            logger.warning(f"⚠️ GPU initialization failed: {e}")
    
    @measure_performance("gpu_text_embedding", gpu_used=True)
    def accelerate_text_embedding(self, texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
        """GPU-accelerated text embedding generation"""
        if not self.enabled:
            return self._cpu_fallback_embedding(texts, model_name)
        
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Load model on GPU with RTX 3050 optimizations
            model = SentenceTransformer(model_name, device=self.device)
            
            # Process in batches to fit RTX 3050 VRAM (4GB)
            batch_size = 32  # Optimized for RTX 3050
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                with torch.no_grad():
                    batch_embeddings = model.encode(batch, convert_to_tensor=True)
                    embeddings.extend(batch_embeddings.cpu().numpy().tolist())
            
            return embeddings
            
        except Exception as e:
            logger.warning(f"⚠️ GPU text embedding failed: {e}, falling back to CPU")
            return self._cpu_fallback_embedding(texts, model_name)
    
    def _cpu_fallback_embedding(self, texts: List[str], model_name: str) -> List[List[float]]:
        """CPU fallback for text embedding"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            return model.encode(texts).tolist()
        except Exception as e:
            logger.error(f"❌ CPU embedding fallback failed: {e}")
            # Return dummy embeddings to prevent system failure
            return [[0.0] * 384 for _ in texts]
    
    @measure_performance("gpu_similarity_search", gpu_used=True)
    def accelerate_similarity_search(self, query_embedding: List[float], 
                                   candidate_embeddings: List[List[float]], 
                                   top_k: int = 5) -> List[int]:
        """GPU-accelerated similarity search"""
        if not self.enabled:
            return self._cpu_similarity_search(query_embedding, candidate_embeddings, top_k)
        
        try:
            import torch
            import torch.nn.functional as F
            
            # Convert to tensors on GPU
            query_tensor = torch.tensor(query_embedding, device=self.device).unsqueeze(0)
            candidate_tensor = torch.tensor(candidate_embeddings, device=self.device)
            
            # Calculate cosine similarity
            with torch.no_grad():
                similarities = F.cosine_similarity(query_tensor, candidate_tensor)
                top_indices = torch.topk(similarities, min(top_k, len(candidate_embeddings))).indices
                
            return top_indices.cpu().numpy().tolist()
            
        except Exception as e:
            logger.warning(f"⚠️ GPU similarity search failed: {e}, falling back to CPU")
            return self._cpu_similarity_search(query_embedding, candidate_embeddings, top_k)
    
    def _cpu_similarity_search(self, query_embedding: List[float], 
                              candidate_embeddings: List[List[float]], 
                              top_k: int = 5) -> List[int]:
        """CPU fallback for similarity search"""
        try:
            import numpy as np
            
            query_np = np.array(query_embedding)
            candidates_np = np.array(candidate_embeddings)
            
            # Calculate cosine similarity
            similarities = np.dot(candidates_np, query_np) / (
                np.linalg.norm(candidates_np, axis=1) * np.linalg.norm(query_np)
            )
            
            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return top_indices.tolist()
            
        except Exception as e:
            logger.error(f"❌ CPU similarity search failed: {e}")
            return list(range(min(top_k, len(candidate_embeddings))))

# Global GPU accelerator instance
gpu_accelerator = GPUAccelerator()
