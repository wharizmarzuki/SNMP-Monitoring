"""
Unit tests for Cache Service

Tests Redis caching functionality with mocked Redis client.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.core.cache import CacheService, cached


@pytest.mark.unit
class TestCacheServiceInitialization:
    """Test cache service initialization"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_initialization_success(self, mock_settings, mock_redis):
        """Test: Cache initializes successfully with Redis available"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()

        # Assert
        assert cache.available is True
        assert cache.redis_client is not None
        mock_redis_client.ping.assert_called_once()

    @patch('app.core.cache.settings')
    def test_cache_initialization_disabled(self, mock_settings):
        """Test: Cache gracefully handles CACHE_ENABLED=False"""
        # Setup
        mock_settings.cache_enabled = False

        # Execute
        cache = CacheService()

        # Assert
        assert cache.available is False
        assert cache.redis_client is None

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_initialization_connection_failure(self, mock_settings, mock_redis):
        """Test: Cache handles Redis connection failure gracefully"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis.side_effect = ConnectionError("Connection refused")

        # Execute
        cache = CacheService()

        # Assert
        assert cache.available is False
        assert cache.redis_client is None

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_initialization_custom_host_port(self, mock_settings, mock_redis):
        """Test: Cache accepts custom host and port"""
        # Setup
        mock_settings.cache_enabled = True

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService(host="redis.example.com", port=6380, db=2)

        # Assert
        mock_redis.assert_called_once()
        call_kwargs = mock_redis.call_args[1]
        assert call_kwargs['host'] == "redis.example.com"
        assert call_kwargs['port'] == 6380
        assert call_kwargs['db'] == 2


@pytest.mark.unit
class TestCacheServiceGet:
    """Test cache GET operations"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_get_hit(self, mock_settings, mock_redis):
        """Test: Cache GET returns cached value on hit"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        cached_data = {"devices": 10, "up": 8}
        mock_redis_client.get.return_value = json.dumps(cached_data)
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        result = cache.get("network_summary")

        # Assert
        assert result == cached_data
        mock_redis_client.get.assert_called_once_with("network_summary")

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_get_miss(self, mock_settings, mock_redis):
        """Test: Cache GET returns None on miss"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = None  # Cache miss
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        result = cache.get("nonexistent_key")

        # Assert
        assert result is None

    @patch('app.core.cache.settings')
    def test_cache_get_when_unavailable(self, mock_settings):
        """Test: Cache GET returns None when cache unavailable"""
        # Setup
        mock_settings.cache_enabled = False

        # Execute
        cache = CacheService()
        result = cache.get("any_key")

        # Assert
        assert result is None

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_get_json_decode_error(self, mock_settings, mock_redis):
        """Test: Cache GET handles JSON decode error gracefully"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = "invalid json {"  # Malformed JSON
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        result = cache.get("corrupted_key")

        # Assert
        assert result is None  # Graceful failure


@pytest.mark.unit
class TestCacheServiceSet:
    """Test cache SET operations"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_set_success(self, mock_settings, mock_redis):
        """Test: Cache SET stores value with TTL"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        data = {"devices": 10}
        cache.set("network_summary", data, ttl=30)

        # Assert
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[0] == "network_summary"
        assert call_args[1] == 30  # TTL
        assert json.loads(call_args[2]) == data

    @patch('app.core.cache.settings')
    def test_cache_set_when_unavailable(self, mock_settings):
        """Test: Cache SET does nothing when cache unavailable"""
        # Setup
        mock_settings.cache_enabled = False

        # Execute
        cache = CacheService()
        cache.set("any_key", {"data": "value"})

        # Assert - should not raise exception
        assert cache.available is False

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_set_default_ttl(self, mock_settings, mock_redis):
        """Test: Cache SET uses default TTL when not specified"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.set("test_key", {"value": "test"})  # No TTL specified

        # Assert
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[1] == 60  # Default TTL

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_set_complex_data(self, mock_settings, mock_redis):
        """Test: Cache SET handles complex nested data structures"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        complex_data = {
            "devices": [
                {"ip": "192.168.1.1", "status": "up"},
                {"ip": "192.168.1.2", "status": "down"}
            ],
            "summary": {"total": 2, "up": 1}
        }
        cache.set("complex_key", complex_data)

        # Assert
        call_args = mock_redis_client.setex.call_args[0]
        assert json.loads(call_args[2]) == complex_data


@pytest.mark.unit
class TestCacheServiceDelete:
    """Test cache DELETE operations"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_delete_success(self, mock_settings, mock_redis):
        """Test: Cache DELETE removes key"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.delete("test_key")

        # Assert
        mock_redis_client.delete.assert_called_once_with("test_key")

    @patch('app.core.cache.settings')
    def test_cache_delete_when_unavailable(self, mock_settings):
        """Test: Cache DELETE does nothing when cache unavailable"""
        # Setup
        mock_settings.cache_enabled = False

        # Execute
        cache = CacheService()
        cache.delete("any_key")

        # Assert - should not raise exception
        assert cache.available is False


@pytest.mark.unit
class TestCacheServicePatternDelete:
    """Test cache pattern-based DELETE operations"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_delete_pattern_success(self, mock_settings, mock_redis):
        """Test: Cache DELETE PATTERN removes matching keys"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.scan_iter.return_value = ["device:1", "device:2", "device:3"]
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.delete_pattern("device:*")

        # Assert
        mock_redis_client.scan_iter.assert_called_once_with(match="device:*")
        assert mock_redis_client.delete.call_count == 3


@pytest.mark.unit
class TestCacheServiceClearAll:
    """Test cache clear all operations"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_clear_all_success(self, mock_settings, mock_redis):
        """Test: Cache CLEAR ALL flushes database"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.clear_all()

        # Assert
        mock_redis_client.flushdb.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestCachedDecorator:
    """Test @cached decorator functionality"""

    @patch('app.core.cache.cache')
    async def test_cached_decorator_cache_miss(self, mock_cache):
        """Test: @cached decorator executes function on cache miss"""
        # Setup
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set = Mock()

        @cached(ttl=30, key_prefix="test")
        async def expensive_function():
            return {"result": "computed"}

        # Execute
        result = await expensive_function()

        # Assert
        assert result == {"result": "computed"}
        mock_cache.set.assert_called_once()

    @patch('app.core.cache.cache')
    async def test_cached_decorator_cache_hit(self, mock_cache):
        """Test: @cached decorator returns cached value on cache hit"""
        # Setup
        cached_value = {"result": "from_cache"}
        mock_cache.get.return_value = cached_value

        @cached(ttl=30, key_prefix="test")
        async def expensive_function():
            return {"result": "computed"}  # Should not be called

        # Execute
        result = await expensive_function()

        # Assert
        assert result == cached_value

    @patch('app.core.cache.cache')
    async def test_cached_decorator_custom_ttl(self, mock_cache):
        """Test: @cached decorator uses custom TTL"""
        # Setup
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        @cached(ttl=120, key_prefix="test")
        async def expensive_function():
            return {"result": "computed"}

        # Execute
        await expensive_function()

        # Assert
        call_args = mock_cache.set.call_args[0]
        assert call_args[2] == 120  # TTL


@pytest.mark.unit
class TestCacheServiceEdgeCases:
    """Test cache service edge cases"""

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_handles_none_value(self, mock_settings, mock_redis):
        """Test: Cache handles None as a valid cached value"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.set("null_value", None)

        # Assert
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[2] == "null"  # JSON serialized None

    @patch('app.core.cache.redis.Redis')
    @patch('app.core.cache.settings')
    def test_cache_handles_empty_string_key(self, mock_settings, mock_redis):
        """Test: Cache handles empty string as key"""
        # Setup
        mock_settings.cache_enabled = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_db = 0

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        # Execute
        cache = CacheService()
        cache.set("", {"value": "test"})

        # Assert - should handle gracefully
        mock_redis_client.setex.assert_called_once()
