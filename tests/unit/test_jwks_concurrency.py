"""Unit tests for JWKS concurrency safety in authentication middleware.

Tests the concurrent JWKS fetching mechanism to ensure thread safety
and prevent duplicate requests for the same JWKS URL.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from libs.auth.middleware import ClerkTokenValidator, JWKSCache


class TestJWKSConcurrency:
    """Test class for JWKS concurrency safety."""

    @pytest.fixture
    def validator(self):
        """Create a ClerkTokenValidator instance for testing."""
        return ClerkTokenValidator()

    @pytest.fixture
    def mock_jwks_response(self):
        """Mock JWKS response data."""
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "test-key-id",
                    "n": "test-modulus",
                    "e": "AQAB"
                }
            ]
        }

    @pytest.fixture
    def jwks_url(self):
        """Test JWKS URL."""
        return "https://test.clerk.accounts.dev/.well-known/jwks.json"

    @pytest.mark.asyncio
    async def test_single_jwks_fetch(self, validator, mock_jwks_response, jwks_url):
        """Test single JWKS fetch works correctly."""
        # Setup
        with patch.object(validator.http_client, "get") as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(return_value=mock_jwks_response)
            mock_response.status_code = 200
            mock_get = AsyncMock(return_value=mock_response)

            # Execute
            result = await validator._fetch_jwks(jwks_url)

            # Assert
            assert result == mock_jwks_response
            mock_get.assert_called_once_with(jwks_url, timeout=30)

            # Verify cache was updated
            assert jwks_url in validator.jwks_cache.cache
            cached_entry = validator.jwks_cache.cache[jwks_url]
            assert cached_entry.jwks == mock_jwks_response

    @pytest.mark.asyncio
    async def test_concurrent_jwks_fetch_same_url(self, validator, mock_jwks_response, jwks_url):
        """Test concurrent JWKS fetches for the same URL only make one HTTP request."""
        # Setup
        call_count = 0

        async def mock_http_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate network delay
            await asyncio.sleep(0.1)
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(return_value=mock_jwks_response)
            mock_response.status_code = 200
            return mock_response

        with patch.object(validator.http_client, "get", new=mock_http_get):

            # Execute multiple concurrent requests
            tasks = [validator._fetch_jwks(jwks_url) for _ in range(5)]
            results = await asyncio.gather(*tasks)

            # Assert
            # All results should be the same
            for result in results:
                assert result == mock_jwks_response

            # Only one HTTP request should have been made
            assert call_count == 1

            # Verify cache was updated
            assert jwks_url in validator.jwks_cache.cache

    @pytest.mark.asyncio
    async def test_concurrent_jwks_fetch_different_urls(self, validator, mock_jwks_response):
        """Test concurrent JWKS fetches for different URLs make separate requests."""
        # Setup
        urls = [
            "https://test1.clerk.accounts.dev/.well-known/jwks.json",
            "https://test2.clerk.accounts.dev/.well-known/jwks.json",
            "https://test3.clerk.accounts.dev/.well-known/jwks.json"
        ]

        call_count = 0

        async def mock_http_get(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(return_value=mock_jwks_response)
            mock_response.status_code = 200
            return mock_response

        with patch.object(validator.http_client, "get", new=mock_http_get):

            # Execute concurrent requests for different URLs
            tasks = [validator._fetch_jwks(url) for url in urls]
            results = await asyncio.gather(*tasks)

            # Assert
            # All results should be the same
            for result in results:
                assert result == mock_jwks_response

            # Three HTTP requests should have been made (one per URL)
            assert call_count == 3

            # Verify all URLs are cached
            for url in urls:
                assert url in validator.jwks_cache.cache

    @pytest.mark.asyncio
    async def test_jwks_cache_expiry(self, validator, mock_jwks_response, jwks_url):
        """Test JWKS cache expiry and refresh."""
        # Setup - manually add expired cache entry
        expired_time = datetime.utcnow() - timedelta(hours=2)
        validator.jwks_cache.cache[jwks_url] = JWKSCache(
            jwks={"keys": []},
            expires_at=expired_time
        )

        with patch.object(validator.http_client, "get") as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(return_value=mock_jwks_response)
            mock_response.status_code = 200
            mock_get = AsyncMock(return_value=mock_response)

            # Execute
            result = await validator._fetch_jwks(jwks_url)

            # Assert
            assert result == mock_jwks_response
            mock_get.assert_called_once()  # Should fetch due to expiry

            # Verify cache was updated with new data
            cached_entry = validator.jwks_cache.cache[jwks_url]
            assert cached_entry.jwks == mock_jwks_response
            assert cached_entry.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_jwks_fetch_http_error(self, validator, jwks_url):
        """Test JWKS fetch handles HTTP errors correctly."""
        # Setup
        with patch.object(validator.http_client, "get") as mock_get:
            mock_get = AsyncMock(side_effect=Exception("HTTP 404 Not Found"))

            # Execute & Assert
            with pytest.raises(Exception) as exc_info:
                await validator._fetch_jwks(jwks_url)

            assert "HTTP 404 Not Found" in str(exc_info.value)

            # Verify no cache entry was created
            assert jwks_url not in validator.jwks_cache.cache

    @pytest.mark.asyncio
    async def test_jwks_fetch_json_error(self, validator, jwks_url):
        """Test JWKS fetch handles JSON parsing errors correctly."""
        # Setup
        with patch.object(validator.http_client, "get") as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(side_effect=ValueError("Invalid JSON"))
            mock_response.status_code = 200
            mock_get = AsyncMock(return_value=mock_response)

            # Execute & Assert
            with pytest.raises(ValueError) as exc_info:
                await validator._fetch_jwks(jwks_url)

            assert "Invalid JSON" in str(exc_info.value)

            # Verify no cache entry was created
            assert jwks_url not in validator.jwks_cache.cache

    @pytest.mark.asyncio
    async def test_concurrent_fetch_with_error_recovery(self, validator, mock_jwks_response, jwks_url):
        """Test that failed concurrent requests don't block subsequent successful ones."""
        # Setup
        call_count = 0

        async def mock_http_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)

            if call_count == 1:
                # First call fails
                raise Exception("Network error")
            else:
                # Subsequent calls succeed
                mock_response = MagicMock(spec=Response)
                mock_response.json = MagicMock(return_value=mock_jwks_response)
                mock_response.status_code = 200
                return mock_response

        with patch.object(validator.http_client, "get", new=mock_http_get):

            # Execute first request (should fail)
            with pytest.raises(Exception):
                await validator._fetch_jwks(jwks_url)

            # Execute second request (should succeed)
            result = await validator._fetch_jwks(jwks_url)

            # Assert
            assert result == mock_jwks_response
            assert call_count == 2

            # Verify cache was updated after successful request
            assert jwks_url in validator.jwks_cache.cache

    @pytest.mark.asyncio
    async def test_validator_cleanup(self, validator, jwks_url):
        """Test validator cleanup cancels pending requests and clears locks."""
        # Setup - create some pending requests
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(1)  # Long delay
            mock_response = MagicMock(spec=Response)
            mock_response.json = MagicMock(return_value={"keys": []})
            mock_response.status_code = 200
            return mock_response

        with patch.object(validator.http_client, "get", new=slow_fetch):

            # Start some concurrent requests
            tasks = [asyncio.create_task(validator._fetch_jwks(jwks_url)) for _ in range(3)]

            # Give tasks time to start
            await asyncio.sleep(0.1)

            # Verify pending requests exist
            assert jwks_url in validator._pending_requests
            assert jwks_url in validator._jwks_locks

            # Execute cleanup
            await validator.close()

            # Assert
            # Pending requests should be cleared
            assert len(validator._pending_requests) == 0
            assert len(validator._jwks_locks) == 0

            # Tasks should be cancelled
            for task in tasks:
                assert task.cancelled() or task.done()

    def test_jwks_cache_initialization(self):
        """Test JWKSCache initialization and properties."""
        # Setup
        jwks_data = {"keys": [{"kid": "test"}]}
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Execute
        cache_entry = JWKSCache(jwks=jwks_data, expires_at=expires_at)

        # Assert
        assert cache_entry.jwks == jwks_data
        assert cache_entry.expires_at == expires_at
        assert not cache_entry.is_expired()

        # Test expiry
        expired_entry = JWKSCache(
            jwks=jwks_data,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert expired_entry.is_expired()

    @pytest.mark.asyncio
    async def test_lock_per_url_isolation(self, validator):
        """Test that locks are isolated per URL."""
        # Setup
        url1 = "https://test1.clerk.accounts.dev/.well-known/jwks.json"
        url2 = "https://test2.clerk.accounts.dev/.well-known/jwks.json"

        # Execute - get locks for different URLs
        lock1 = validator._jwks_locks[url1]
        lock2 = validator._jwks_locks[url2]

        # Assert
        assert lock1 is not lock2
        assert isinstance(lock1, asyncio.Lock)
        assert isinstance(lock2, asyncio.Lock)

        # Test that same URL returns same lock
        lock1_again = validator._jwks_locks[url1]
        assert lock1 is lock1_again
