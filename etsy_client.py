"""
etsy_client.py
--------------
Shared helpers for all Etsy API calls.
"""

import os


def etsy_headers() -> dict:
    """Return the standard Etsy API request headers.

    Raises EnvironmentError if ETSY_API_KEY is not set.
    """
    api_key = os.getenv("ETSY_API_KEY", "")
    if not api_key:
        raise EnvironmentError("ETSY_API_KEY is not set")
    return {"x-api-key": api_key, "Content-Type": "application/json"}
