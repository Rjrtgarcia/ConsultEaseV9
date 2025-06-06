"""
Query caching utilities for ConsultEase system.
Provides efficient caching for database queries to improve performance.
"""

import time
import logging
import hashlib
from typing import Any, Optional, Dict, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class QueryCache:
    """
    Simple in-memory cache for database query results.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize the query cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, dict] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
        
        logger.info(f"Query cache initialized with {default_ttl}s default TTL")
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a cache key from function name and arguments.
        
        Args:
            func_name: Name of the function
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            str: Cache key
        """
        # Create a string representation of the arguments
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        
        # Hash the key data for consistent length
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check if entry has expired
        if current_time > entry['expires']:
            del self.cache[key]
            self.stats['misses'] += 1
            self.stats['evictions'] += 1
            return None
        
        self.stats['hits'] += 1
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        expires = time.time() + ttl
        self.cache[key] = {
            'value': value,
            'expires': expires,
            'created': time.time()
        }
        
        self.stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was found and deleted
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        count = len(self.cache)
        self.cache.clear()
        self.stats['evictions'] += count
        logger.info(f"Cleared {count} entries from query cache")
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired entries.
        
        Returns:
            int: Number of entries cleaned up
        """
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time > entry['expires']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.stats['evictions'] += len(expired_keys)
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'hit_rate': hit_rate,
            **self.stats
        }


# Global query cache instance
_query_cache = None


def get_query_cache() -> QueryCache:
    """
    Get the global query cache instance.
    
    Returns:
        QueryCache: Global query cache
    """
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def cached_query(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching database query results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Optional function to generate custom cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_query_cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing query")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods to the function
        wrapper.cache_clear = lambda: get_query_cache().clear()
        wrapper.cache_stats = lambda: get_query_cache().get_stats()
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Pattern to match (simple string matching)
        
    Returns:
        int: Number of entries invalidated
    """
    cache = get_query_cache()
    keys_to_delete = []
    
    for key in cache.cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache.delete(key)
    
    if keys_to_delete:
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")
    
    return len(keys_to_delete)


class PaginatedQuery:
    """
    Helper class for paginated database queries.
    """
    
    def __init__(self, query, page_size: int = 50):
        """
        Initialize paginated query.
        
        Args:
            query: SQLAlchemy query object
            page_size: Number of items per page
        """
        self.query = query
        self.page_size = page_size
        self._total_count = None
    
    def get_page(self, page: int = 1) -> dict:
        """
        Get a specific page of results.
        
        Args:
            page: Page number (1-based)
            
        Returns:
            dict: Page data with items, pagination info
        """
        offset = (page - 1) * self.page_size
        
        # Get items for this page
        items = self.query.offset(offset).limit(self.page_size).all()
        
        # Get total count (cached)
        total_count = self.get_total_count()
        
        # Calculate pagination info
        total_pages = (total_count + self.page_size - 1) // self.page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            'items': items,
            'page': page,
            'page_size': self.page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        }
    
    def get_total_count(self) -> int:
        """
        Get total count of items (cached).
        
        Returns:
            int: Total number of items
        """
        if self._total_count is None:
            self._total_count = self.query.count()
        return self._total_count
    
    def get_all_pages(self) -> list:
        """
        Get all items across all pages (use with caution).
        
        Returns:
            list: All items
        """
        return self.query.all()


def paginate_query(query, page: int = 1, page_size: int = 50) -> dict:
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        dict: Paginated results
    """
    paginated = PaginatedQuery(query, page_size)
    return paginated.get_page(page)
