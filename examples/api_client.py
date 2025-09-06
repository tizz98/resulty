"""
Real-world API client example using resulty for robust error handling.

This example shows how to handle various API failure scenarios:
- Network connectivity issues
- HTTP error responses (4xx, 5xx)
- Invalid JSON responses
- Rate limiting
- Timeout handling
"""

import json
import os
import sys
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import resulty


# Define specific error types for different failure modes
class NetworkError(resulty.ResultyException):
    """Network connectivity or DNS resolution failed"""

    pass


class HTTPStatusError(resulty.ResultyException):
    """HTTP request returned error status code"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class InvalidJSONError(resulty.ResultyException):
    """Response body is not valid JSON"""

    pass


class RateLimitError(resulty.ResultyException):
    """API rate limit exceeded"""

    pass


class APIClient:
    """Example API client with robust error handling using resulty"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @resulty.resulty
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Fetch user data from JSONPlaceholder API"""
        url = f"{self.base_url}/users/{user_id}"
        return self._make_request(url)

    @resulty.resulty
    def get_posts(
        self, user_id: Optional[int] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Fetch posts, optionally filtered by user"""
        url = f"{self.base_url}/posts"
        params = {}
        if user_id:
            params["userId"] = user_id
        if limit:
            params["_limit"] = limit

        if params:
            url += f"?{urlencode(params)}"

        return self._make_request(url)

    @resulty.resulty
    def search_posts(self, query: str) -> Dict[str, Any]:
        """Search posts by title (simulated endpoint)"""
        if not query.strip():
            raise InvalidJSONError("Search query cannot be empty")

        # Simulate different error conditions for demonstration
        if query.lower() == "error":
            raise HTTPStatusError(500, "Internal server error")
        elif query.lower() == "notfound":
            raise HTTPStatusError(404, "Posts not found")
        elif query.lower() == "ratelimit":
            raise RateLimitError("API rate limit exceeded. Try again later.")
        elif query.lower() == "network":
            raise NetworkError("Failed to connect to API server")

        # In real implementation, this would make an actual search request
        return {
            "query": query,
            "results": [
                {"id": 1, "title": f"Post about {query}", "body": "Sample content"}
            ],
        }

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make HTTP request and handle common error scenarios"""
        try:
            with urlopen(url, timeout=self.timeout) as response:
                # Check for HTTP error status codes
                if response.status >= 400:
                    if response.status == 429:
                        raise RateLimitError("Rate limit exceeded")
                    elif response.status >= 500:
                        raise HTTPStatusError(response.status, "Server error")
                    elif response.status >= 400:
                        raise HTTPStatusError(response.status, "Client error")

                # Read and parse JSON response
                body = response.read().decode("utf-8")
                try:
                    return json.loads(body)
                except json.JSONDecodeError as e:
                    raise InvalidJSONError(f"Invalid JSON response: {e}")

        except HTTPError as e:
            # Handle HTTP errors from urllib
            if e.code == 429:
                raise RateLimitError("Rate limit exceeded")
            else:
                raise HTTPStatusError(e.code, str(e))
        except URLError as e:
            # Handle network-level errors
            raise NetworkError(f"Network error: {e}")
        except Exception as e:
            # Handle unexpected errors
            raise NetworkError(f"Unexpected error: {e}")


def demonstrate_api_usage():
    """Show various error handling scenarios"""
    client = APIClient("https://jsonplaceholder.typicode.com")

    print("=== API Client Error Handling Examples ===\n")

    # Successful request
    print("1. Successful user fetch:")
    result = client.get_user(1)
    match result:
        case resulty.Ok(user_data):
            print(f"   Success: User {user_data['name']} ({user_data['email']})")
        case resulty.Err(error):
            print(f"   Error: {error}")

    print()

    # Non-existent user (404 error)
    print("2. Non-existent user (404):")
    result = client.get_user(999)
    match result:
        case resulty.Ok(user_data):
            print(f"   Success: {user_data}")
        case resulty.Err(error):
            print(f"   Error: {error}")
            if isinstance(error, HTTPStatusError):
                print(f"   Status code: {error.status_code}")

    print()

    # Successful posts fetch
    print("3. Fetch user posts:")
    result = client.get_posts(user_id=1, limit=3)
    match result:
        case resulty.Ok(posts):
            print(f"   Success: Retrieved {len(posts)} posts")
            for post in posts[:2]:
                print(f"   - {post['title'][:50]}...")
        case resulty.Err(error):
            print(f"   Error: {error}")

    print()

    # Demonstrate different error scenarios
    error_scenarios = [
        ("empty query", ""),
        ("server error", "error"),
        ("not found", "notfound"),
        ("rate limit", "ratelimit"),
        ("network error", "network"),
        ("successful search", "python"),
    ]

    print("4. Search error handling scenarios:")
    for description, query in error_scenarios:
        result = client.search_posts(query)
        match result:
            case resulty.Ok(search_results):
                print(
                    f"   {description}: Found {len(search_results['results'])} results"
                )
            case resulty.Err(error):
                error_type = type(error).__name__
                print(f"   {description}: {error_type} - {error}")

    print()


if __name__ == "__main__":
    demonstrate_api_usage()
