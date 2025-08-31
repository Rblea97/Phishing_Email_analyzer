"""
Cache Manager Service - Phase 4 Enhancement
Redis-based caching system for performance optimization

Provides intelligent caching for URL reputation analysis, AI results,
and email processing to minimize API calls and improve response times.
"""

import os
import json
import logging
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import asdict

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Redis-based cache manager with fallback to in-memory storage
    Optimized for phishing detection system with intelligent TTL policies
    """
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.default_expire_hours = int(os.getenv('DEFAULT_CACHE_EXPIRE_HOURS', '24'))
        self.key_prefix = os.getenv('CACHE_KEY_PREFIX', 'phishing_detector')
        
        # Fallback in-memory cache
        self._memory_cache = {}
        self._memory_cache_expiry = {}
        
        # Initialize Redis connection
        self.redis_client = None
        self.redis_available = False
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # We handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.redis_available = True
                logger.info("Redis cache initialized successfully")
                
                # Set up cache statistics
                self._init_stats()
                
            except Exception as e:
                logger.warning(f"Redis not available, using memory cache: {e}")
                self.redis_available = False
        else:
            logger.warning("Redis library not available, using memory cache")

    def _init_stats(self):
        """Initialize cache statistics tracking"""
        if self.redis_available:
            stats_key = self._get_key("stats")
            if not self.redis_client.exists(stats_key):
                stats = {
                    'hits': 0,
                    'misses': 0,
                    'sets': 0,
                    'deletes': 0,
                    'last_reset': datetime.now().isoformat()
                }
                self.redis_client.set(stats_key, json.dumps(stats))

    def _get_key(self, key: str) -> str:
        """Generate prefixed cache key"""
        return f"{self.key_prefix}:{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """
        Serialize value for storage, handling dataclasses and complex objects
        """
        try:
            # Handle dataclasses by converting to dict
            if hasattr(value, '__dataclass_fields__'):
                value = asdict(value)
            
            # For other objects, try JSON first (faster), then pickle
            try:
                return json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                return pickle.dumps(value)
                
        except Exception as e:
            logger.error(f"Failed to serialize cache value: {e}")
            raise

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize stored value"""
        try:
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Failed to deserialize cache value: {e}")
            return None

    def _update_stats(self, operation: str):
        """Update cache statistics"""
        if not self.redis_available:
            return
            
        try:
            stats_key = self._get_key("stats")
            stats_data = self.redis_client.get(stats_key)
            
            if stats_data:
                stats = json.loads(stats_data)
                stats[operation] = stats.get(operation, 0) + 1
                self.redis_client.set(stats_key, json.dumps(stats))
        except Exception as e:
            logger.debug(f"Failed to update cache stats: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._get_key(key)
        
        try:
            if self.redis_available:
                data = self.redis_client.get(cache_key)
                if data is not None:
                    value = self._deserialize_value(data)
                    self._update_stats('hits')
                    logger.debug(f"Cache hit: {key}")
                    return value
                else:
                    self._update_stats('misses')
                    logger.debug(f"Cache miss: {key}")
                    return None
            else:
                # Use memory cache
                if cache_key in self._memory_cache:
                    # Check expiry
                    expiry_time = self._memory_cache_expiry.get(cache_key)
                    if expiry_time and datetime.now() < expiry_time:
                        logger.debug(f"Memory cache hit: {key}")
                        return self._memory_cache[cache_key]
                    else:
                        # Expired, remove from cache
                        self._memory_cache.pop(cache_key, None)
                        self._memory_cache_expiry.pop(cache_key, None)
                        logger.debug(f"Memory cache expired: {key}")
                
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, expire_hours: Optional[int] = None) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire_hours: Expiration time in hours (default from config)
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._get_key(key)
        expire_hours = expire_hours or self.default_expire_hours
        
        try:
            serialized_value = self._serialize_value(value)
            
            if self.redis_available:
                # Set with expiration
                expire_seconds = expire_hours * 3600
                result = self.redis_client.setex(cache_key, expire_seconds, serialized_value)
                if result:
                    self._update_stats('sets')
                    logger.debug(f"Cache set: {key} (expires in {expire_hours}h)")
                return result
            else:
                # Use memory cache
                self._memory_cache[cache_key] = value
                self._memory_cache_expiry[cache_key] = datetime.now() + timedelta(hours=expire_hours)
                logger.debug(f"Memory cache set: {key} (expires in {expire_hours}h)")
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False if not found or error
        """
        cache_key = self._get_key(key)
        
        try:
            if self.redis_available:
                result = self.redis_client.delete(cache_key)
                if result:
                    self._update_stats('deletes')
                    logger.debug(f"Cache delete: {key}")
                return bool(result)
            else:
                # Use memory cache
                deleted = cache_key in self._memory_cache
                self._memory_cache.pop(cache_key, None)
                self._memory_cache_expiry.pop(cache_key, None)
                if deleted:
                    logger.debug(f"Memory cache delete: {key}")
                return deleted
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired
        """
        cache_key = self._get_key(key)
        
        try:
            if self.redis_available:
                return bool(self.redis_client.exists(cache_key))
            else:
                # Check memory cache with expiry
                if cache_key in self._memory_cache:
                    expiry_time = self._memory_cache_expiry.get(cache_key)
                    if expiry_time and datetime.now() < expiry_time:
                        return True
                    else:
                        # Expired, clean up
                        self._memory_cache.pop(cache_key, None)
                        self._memory_cache_expiry.pop(cache_key, None)
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern
        
        Args:
            pattern: Pattern to match (e.g., "url_reputation:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if self.redis_available:
                search_pattern = self._get_key(pattern)
                keys = self.redis_client.keys(search_pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
                    logger.info(f"Cleared {count} cache keys matching: {pattern}")
                    return count
                return 0
            else:
                # Memory cache pattern matching
                full_pattern = self._get_key(pattern).replace('*', '')
                count = 0
                keys_to_delete = []
                
                for key in self._memory_cache.keys():
                    if key.startswith(full_pattern):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    self._memory_cache.pop(key, None)
                    self._memory_cache_expiry.pop(key, None)
                    count += 1
                
                logger.info(f"Cleared {count} memory cache keys matching: {pattern}")
                return count
                
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict containing cache performance statistics
        """
        try:
            if self.redis_available:
                stats_key = self._get_key("stats")
                stats_data = self.redis_client.get(stats_key)
                
                if stats_data:
                    stats = json.loads(stats_data)
                    
                    # Add current memory info
                    info = self.redis_client.info('memory')
                    stats['redis_memory_used'] = info.get('used_memory_human', 'Unknown')
                    stats['redis_connected_clients'] = self.redis_client.info('clients')['connected_clients']
                    
                    # Calculate hit rate
                    total_ops = stats['hits'] + stats['misses']
                    hit_rate = (stats['hits'] / total_ops * 100) if total_ops > 0 else 0
                    stats['hit_rate_percent'] = round(hit_rate, 2)
                    
                    return stats
                else:
                    return {'error': 'No stats available'}
            else:
                # Memory cache stats
                return {
                    'cache_type': 'memory',
                    'keys_stored': len(self._memory_cache),
                    'expired_keys_cleaned': 0,
                    'memory_cache_enabled': True,
                    'redis_available': False
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}

    def health_check(self) -> Dict:
        """
        Perform cache health check
        
        Returns:
            Dict containing health status
        """
        try:
            if self.redis_available:
                # Test Redis connectivity
                start_time = datetime.now()
                self.redis_client.ping()
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Get Redis info
                info = self.redis_client.info()
                
                return {
                    'status': 'healthy',
                    'type': 'redis',
                    'response_time_ms': round(response_time, 2),
                    'redis_version': info.get('redis_version', 'Unknown'),
                    'uptime_seconds': info.get('uptime_in_seconds', 0),
                    'connected_clients': info.get('connected_clients', 0)
                }
            else:
                return {
                    'status': 'degraded',
                    'type': 'memory',
                    'message': 'Using fallback memory cache',
                    'keys_stored': len(self._memory_cache)
                }
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'type': 'memory' if not self.redis_available else 'redis'
            }

    def cleanup_expired(self) -> int:
        """
        Manually clean up expired keys (mainly for memory cache)
        
        Returns:
            Number of keys cleaned up
        """
        if self.redis_available:
            # Redis handles expiry automatically
            return 0
        
        # Clean up memory cache
        current_time = datetime.now()
        expired_keys = []
        
        for key, expiry_time in self._memory_cache_expiry.items():
            if current_time >= expiry_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._memory_cache.pop(key, None)
            self._memory_cache_expiry.pop(key, None)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired memory cache keys")
        
        return len(expired_keys)


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """
    Get global cache manager instance
    Implements singleton pattern for efficient resource usage
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def reset_cache_manager():
    """Reset the global cache manager (mainly for testing)"""
    global _cache_manager
    _cache_manager = None