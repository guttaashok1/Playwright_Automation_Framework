"""
Base API Client.
Wraps httpx/requests with logging, retries, and response validation.
Used for direct REST API testing and for test setup/teardown calls.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from configs.config import config


class APIResponse:
    """Thin wrapper around httpx.Response with helper assertions."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> dict:
        return dict(self._response.headers)

    @property
    def body(self) -> dict | list | str:
        try:
            return self._response.json()
        except Exception:
            return self._response.text

    @property
    def text(self) -> str:
        return self._response.text

    def assert_status(self, expected: int) -> "APIResponse":
        assert self.status_code == expected, (
            f"Expected status {expected}, got {self.status_code}.\nBody: {self.text}"
        )
        return self

    def assert_ok(self) -> "APIResponse":
        assert 200 <= self.status_code < 300, (
            f"Expected 2xx status, got {self.status_code}.\nBody: {self.text}"
        )
        return self

    def assert_json_key(self, key: str, expected_value: Any = None) -> "APIResponse":
        body = self.body
        assert isinstance(body, dict), f"Response body is not a JSON object: {body}"
        assert key in body, f"Key '{key}' not found in response. Keys: {list(body.keys())}"
        if expected_value is not None:
            assert body[key] == expected_value, (
                f"Key '{key}': expected {expected_value!r}, got {body[key]!r}"
            )
        return self

    def get_json_value(self, key: str) -> Any:
        body = self.body
        assert isinstance(body, dict), f"Response body is not a JSON object"
        return body[key]


class APIClient:
    """
    Reusable HTTP client for API testing.
    Features:
    - Automatic base URL prefixing
    - Session-level auth header management
    - Request/response logging
    - Configurable retries on transient failures
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[dict] = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or config.app.API_BASE_URL).rstrip("/")
        self.default_headers: dict = {"Content-Type": "application/json", **(headers or {})}
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self.default_headers,
            timeout=self.timeout,
            follow_redirects=True,
        )

    def set_auth_token(self, token: str, scheme: str = "Bearer") -> None:
        """Set authorization header for all subsequent requests."""
        self._client.headers.update({"Authorization": f"{scheme} {token}"})

    def clear_auth(self) -> None:
        self._client.headers.pop("Authorization", None)

    # ------------------------------------------------------------------ #
    # Core HTTP methods
    # ------------------------------------------------------------------ #

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        url = f"/{endpoint.lstrip('/')}"
        logger.info(f"[API] {method.upper()} {self.base_url}{url}")
        if "json" in kwargs:
            logger.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")

        response = self._client.request(method, url, **kwargs)

        logger.info(f"[API] Response: {response.status_code} ({len(response.content)} bytes)")
        logger.debug(f"Response body: {response.text[:500]}")
        return APIResponse(response)

    def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> APIResponse:
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> APIResponse:
        return self._request("POST", endpoint, json=json, **kwargs)

    def put(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> APIResponse:
        return self._request("PUT", endpoint, json=json, **kwargs)

    def patch(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> APIResponse:
        return self._request("PATCH", endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        return self._request("DELETE", endpoint, **kwargs)

    # ------------------------------------------------------------------ #
    # Authentication helpers
    # ------------------------------------------------------------------ #

    def login(self, email: str, password: str, login_endpoint: str = "/auth/login") -> str:
        """Login via API and store the returned JWT token. Returns the token."""
        response = self.post(login_endpoint, json={"email": email, "password": password})
        response.assert_ok()
        token = response.get_json_value("token")
        self.set_auth_token(token)
        logger.info(f"[API] Authenticated as {email}")
        return token

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
