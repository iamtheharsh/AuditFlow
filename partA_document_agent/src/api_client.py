"""
External API Client Module

Makes HTTP requests to external APIs.
Currently supports:
- httpbin.org/post (for demonstration)

Handles timeouts, retries, and comprehensive logging.
"""

import time
from typing import Dict, Any, Optional
import json

import requests

import vc_tracker


def call_external_api(
    job_id: str,
    flag_count: int,
    input_length: int,
    api_type: str = "httpbin"
) -> Dict[str, Any]:
    """
    Make an external API call with job metadata.

    Args:
        job_id: Job identifier
        flag_count: Number of red flags detected
        input_length: Length of input text
        api_type: API type (httpbin or openai)

    Returns:
        Dictionary with API response and metadata
    """
    start_time = time.time()

    if api_type == "httpbin":
        return _call_httpbin(job_id, flag_count, input_length)
    elif api_type == "openai":
        # For future implementation
        raise NotImplementedError("OpenAI API integration not yet implemented")
    else:
        raise ValueError(f"Unknown API type: {api_type}")


def _call_httpbin(job_id: str, flag_count: int, input_length: int) -> Dict[str, Any]:
    """
    Call httpbin.org/post API as a demo.

    Args:
        job_id: Job identifier
        flag_count: Number of red flags
        input_length: Text input length

    Returns:
        Response dictionary
    """
    print(f"[INFO] Calling httpbin.org/post API...")

    endpoint = "https://httpbin.org/post"

    # Prepare payload
    payload = {
        "job_id": job_id,
        "flag_count": flag_count,
        "input_length": input_length,
        "timestamp": time.time()
    }

    try:
        # Make the request
        response = requests.post(
            endpoint,
            json=payload,
            timeout=30
        )

        # Calculate latency
        latency_ms = (time.time() - time.time()) * 1000

        # Check response
        response.raise_for_status()

        # Parse response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"text": response.text}

        # Prepare result
        result = {
            "success": True,
            "endpoint": endpoint,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "response": response_data,
            "payload": payload
        }

        # Log to VC
        vc_tracker.vc_step(
            "external_api_called",
            count=1,
            duration_ms=latency_ms,
            meta={
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": True
            }
        )

        print(f"[INFO] API call successful: {response.status_code} in {latency_ms:.1f}ms")

        return result

    except requests.exceptions.Timeout:
        print(f"[WARN] API call timeout after 30 seconds")

        # Log failed call
        result = {
            "success": False,
            "endpoint": endpoint,
            "error": "timeout",
            "payload": payload
        }

        vc_tracker.vc_step(
            "external_api_called",
            count=1,
            meta={
                "endpoint": endpoint,
                "success": False,
                "error": "timeout"
            }
        )

        return result

    except requests.exceptions.RequestException as e:
        print(f"[WARN] API call failed: {e}")

        # Log failed call
        result = {
            "success": False,
            "endpoint": endpoint,
            "error": str(e),
            "payload": payload
        }

        vc_tracker.vc_step(
            "external_api_called",
            count=1,
            meta={
                "endpoint": endpoint,
                "success": False,
                "error": str(e)
            }
        )

        return result
