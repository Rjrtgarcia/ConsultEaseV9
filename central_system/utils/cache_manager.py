"""
Cache manager for ConsultEase system.
Provides intelligent caching for frequently accessed data to improve performance.
"""

import time
import threading
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry with expiration and metadata."""
    
    def __init__(self, value: Any, ttl: int = 300):
        """
        Initialize cache entry.
        
        Args:
            value: The cached value
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> Any:
        """Access the cached value and update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class CacheManager:
    """
    Thread-safe cache manager with TTL support and intelligent eviction.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time to live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self._stats['evictions'],
                'expired': self._stats['expired']
            }
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest last_accessed time
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_accessed)
        
        del self._cache[lru_key]
        self._stats['evictions'] += 1
    
    def _cleanup_worker(self) -> None:
        """Background worker to clean up expired entries."""
        while True:
            try:
                time.sleep(60)  # Run cleanup every minute
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Error in cache cleanup worker: {e}")
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['expired'] += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return _cache_manager


def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key (uses function name and args by default)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = _cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_faculty_list_key(filter_available=None, search_term=None):
    """Generate cache key for faculty list queries."""
    key_parts = ["faculty_list"]
    if filter_available is not None:
        key_parts.append(f"available={filter_available}")
    if search_term:
        key_parts.append(f"search={search_term}")
    return ":".join(key_parts)


def invalidate_faculty_cache():
    """Invalidate all faculty-related cache entries."""
    cache = get_cache_manager()
    # Get all keys that start with 'faculty'
    with cache._lock:
        faculty_keys = [key for key in cache._cache.keys() if key.startswith('faculty')]
        for key in faculty_keys:
            cache.delete(key)
    
    logger.debug(f"Invalidated {len(faculty_keys)} faculty cache entries")


def invalidate_consultation_cache(student_id: Optional[int] = None):
    """Invalidate consultation-related cache entries."""
    cache = get_cache_manager()
    with cache._lock:
        consultation_keys = [key for key in cache._cache.keys() if key.startswith('consultation')]
        if student_id:
            # Only invalidate for specific student
            consultation_keys = [key for key in consultation_keys if f"student_id={student_id}" in key]
        
        for key in consultation_keys:
            cache.delete(key)
    
    logger.debug(f"Invalidated {len(consultation_keys)} consultation cache entries")
