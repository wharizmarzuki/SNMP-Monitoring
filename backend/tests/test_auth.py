"""
Authentication and Authorization Tests

Tests the auth integration (minimal scope):
- Login flow with valid/invalid credentials
- Protected endpoints reject unauthenticated requests
- Valid tokens grant access
- Invalid tokens are rejected

Does NOT test:
- JWT library internals (python-jose)
- Password hashing internals (passlib/bcrypt)
- Token expiration logic (tested by library)
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test authentication integration - minimal scope"""

    def test_login_with_valid_credentials_returns_token(
        self, client_no_auth, test_user
    ):
        """Test: Valid login returns access token"""
        response = client_no_auth.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_with_invalid_username_fails(self, client_no_auth):
        """Test: Login with non-existent username is rejected"""
        response = client_no_auth.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "testpass"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        # Custom error response structure
        assert "message" in data or "detail" in data

    def test_login_with_invalid_password_fails(self, client_no_auth, test_user):
        """Test: Login with wrong password is rejected"""
        response = client_no_auth.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        # Custom error response structure
        assert "message" in data or "detail" in data

    def test_protected_endpoint_without_token_blocked(self, client_no_auth):
        """Test: Requests without token are rejected"""
        response = client_no_auth.get("/device/")
        # FastAPI HTTPBearer returns 403 when no credentials provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_protected_endpoint_with_valid_token_allowed(
        self, client_no_auth, auth_headers
    ):
        """Test: Valid token grants access to protected endpoints"""
        response = client_no_auth.get("/device/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_protected_endpoint_with_invalid_token_blocked(
        self, client_no_auth
    ):
        """Test: Invalid/malformed token is rejected"""
        response = client_no_auth.get(
            "/device/",
            headers={"Authorization": "Bearer invalid-fake-token-12345"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_malformed_header_blocked(
        self, client_no_auth
    ):
        """Test: Malformed Authorization header is rejected"""
        # Missing "Bearer" prefix
        response = client_no_auth.get(
            "/device/",
            headers={"Authorization": "just-a-token"}
        )
        # FastAPI HTTPBearer returns 403 for malformed headers
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.auth
class TestMultipleProtectedEndpoints:
    """Test that multiple endpoint types require authentication"""

    def test_device_endpoints_require_auth(self, client_no_auth):
        """Test: Device endpoints require authentication"""
        endpoints = [
            ("/device/", "get"),
            ("/device/192.168.1.1", "get"),
            ("/device/192.168.1.1/thresholds", "put"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = client_no_auth.get(endpoint)
            elif method == "put":
                response = client_no_auth.put(endpoint, json={})

            # FastAPI HTTPBearer returns 403 when no token provided
            assert response.status_code == status.HTTP_403_FORBIDDEN, \
                f"{method.upper()} {endpoint} should require auth"

    def test_query_endpoints_require_auth(self, client_no_auth):
        """Test: Query endpoints require authentication"""
        response = client_no_auth.get("/query/network-summary")
        # FastAPI HTTPBearer returns 403 when no token provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_recipient_endpoints_require_auth(self, client_no_auth):
        """Test: Recipient endpoints require authentication"""
        # GET recipients
        response = client_no_auth.get("/recipients/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # POST recipient
        response = client_no_auth.post(
            "/recipients/",
            json={"email": "test@example.com"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.auth
class TestAuthHeaders:
    """Test auth_headers fixture provides working authentication"""

    def test_auth_headers_allow_device_access(
        self, client_no_auth, auth_headers
    ):
        """Test: auth_headers fixture provides valid authentication"""
        response = client_no_auth.get("/device/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_auth_headers_allow_query_access(
        self, client_no_auth, auth_headers
    ):
        """Test: auth_headers work for query endpoints"""
        response = client_no_auth.get(
            "/query/network-summary",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_auth_headers_allow_recipient_access(
        self, client_no_auth, auth_headers
    ):
        """Test: auth_headers work for recipient endpoints"""
        response = client_no_auth.get("/recipients/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
