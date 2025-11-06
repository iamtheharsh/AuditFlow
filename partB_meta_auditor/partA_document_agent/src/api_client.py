"""
External API Client Module (Phase 2 Enhanced)

Makes HTTP requests to external APIs with resilience features:
- Retry with exponential backoff
- Circuit breaker pattern
- Comprehensive metrics and observability
- Configurable via config.yaml

Currently supports:
- httpbin.org/post (for demonstration)
- OpenAI API (token estimation - instrumentation only)

Handles timeouts, retries, and detailed logging.
"""

import time
import random
from typing import Dict, Any, Optional
import json

import requests

import vc_tracker
import config


# Global circuit breaker state
_circuit_state: Dict[str, Dict[str, Any]] = {}


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open (too many failures)."""
    pass


def call_external_api(
    job_id: str,
    flag_count: int,
    input_length: int,
    api_type: str = "httpbin",
    config_override: Optional[config.ExternalAPIConfig] = None
) -> Dict[str, Any]:
    """
    Make an external API call with job metadata and resilience.

    Args:
        job_id: Job identifier
        flag_count: Number of red flags detected
        input_length: Length of input text
        api_type: API type (httpbin or openai)
        config_override: Optional API configuration

    Returns:
        Dictionary with API response and metadata
    """
    # Get configuration
    api_config = config_override or config.get_config().external_api

    start_time = time.time()

    if api_type == "httpbin":
        return _call_httpbin_with_retry(
            job_id=job_id,
            flag_count=flag_count,
            input_length=input_length,
            config=api_config
        )
    elif api_type == "openai":
        # For future implementation - instrumentation only
        return _call_openai_instrumentation(
            job_id=job_id,
            flag_count=flag_count,
            input_length=input_length,
            config=api_config
        )
    else:
        raise ValueError(f"Unknown API type: {api_type}")


def _call_httpbin_with_retry(
    job_id: str,
    flag_count: int,
    input_length: int,
    config: config.ExternalAPIConfig
) -> Dict[str, Any]:
    """
    Call httpbin.org/post API with retry logic and circuit breaker.

    Args:
        job_id: Job identifier
        flag_count: Number of red flags
        input_length: Text input length
        config: API configuration

    Returns:
        Response dictionary
    """
    endpoint = config.endpoint
    retry_config = config.retry
    cb_config = config.circuit_breaker

    # Check circuit breaker
    if _is_circuit_open(endpoint, cb_config):
        print(f"[WARN] Circuit breaker is open for {endpoint}")
        return _log_api_failure(
            job_id, endpoint, "circuit_breaker_open", 0, retry_config
        )

    # Prepare payload
    payload = {
        "job_id": job_id,
        "flag_count": flag_count,
        "input_length": input_length,
        "timestamp": time.time()
    }

    print(f"[INFO] Calling {endpoint} with up to {retry_config.max_attempts} attempts...")

    last_error = None
    total_attempts = 0

    # Retry loop
    for attempt in range(1, retry_config.max_attempts + 1):
        total_attempts = attempt
        attempt_start = time.time()

        try:
            # Make the request
# [VC] external_api_call detected here - POST response.raise
# Suggested: Add @vc_tracker('external_api_call') decorator or vc_step() call

            response = requests.post(
                endpoint,
                json=payload,
                timeout=config.timeout_sec
            )

            # Check if circuit breaker should be updated
            _update_circuit_breaker(endpoint, True, cb_config)

            # Calculate latency
            attempt_latency_ms = (time.time() - attempt_start) * 1000
            total_latency_ms = (time.time() - time.time()) * 1000  # Will be recalculated

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
                "latency_ms": attempt_latency_ms,
                "total_attempts": total_attempts,
                "response": response_data,
                "payload": payload
            }

            # Log to VC
            meta = {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": True,
                "attempts": total_attempts,
                "retry_used": total_attempts > 1
            }

            # Add retry information if applicable
            if total_attempts > 1:
                meta["first_attempt_error"] = str(last_error) if last_error else None

            vc_tracker.vc_step(
                "external_api_called",
                count=1,
                duration_ms=attempt_latency_ms,
                meta=meta
            )

            print(f"[INFO] API call successful: {response.status_code} "
                  f"in {attempt_latency_ms:.1f}ms (attempts: {total_attempts})")

            return result

        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            last_error = e
            print(f"[WARN] Attempt {attempt} failed: {e}")

            # Check if this was the last attempt
            if attempt < retry_config.max_attempts:
                # Calculate backoff delay
                delay = _calculate_backoff(attempt, retry_config)
                print(f"[INFO] Retrying in {delay:.1f} seconds...")
                time.sleep(delay)

    # All attempts failed
    _update_circuit_breaker(endpoint, False, cb_config)

    # Log failed call
    return _log_api_failure(
        job_id, endpoint, str(last_error), total_attempts, retry_config
    )


def _call_openai_instrumentation(
    job_id: str,
    flag_count: int,
    input_length: int,
    config: config.ExternalAPIConfig
) -> Dict[str, Any]:
    """
    OpenAI API instrumentation (Phase 2 feature - no actual API call).

    This is a placeholder for future OpenAI integration.
    It logs that an LLM call was attempted and provides token estimation.

    Args:
        job_id: Job identifier
        flag_count: Number of red flags
        input_length: Text input length
        config: API configuration

    Returns:
        Response dictionary with instrumentation data
    """
    print(f"[INFO] OpenAI API instrumentation mode (no actual API call)")

    # This would be where we estimate tokens for an LLM call
    # For now, just log that we would have made a call
    result = {
        "success": True,
        "endpoint": "openai_instrumentation",
        "status_code": 200,
        "latency_ms": 0,
        "total_attempts": 0,
        "response": {
            "message": "OpenAI API call simulated (instrumentation only)",
            "would_have_sent": {
                "job_id": job_id,
                "flag_count": flag_count,
                "input_length": input_length
            }
        },
        "payload": {
            "job_id": job_id,
            "flag_count": flag_count,
            "input_length": input_length
        },
        "instrumentation": True
    }

    # Log to VC
    vc_tracker.vc_step(
        "external_api_called",
        count=1,
        meta={
            "endpoint": "openai_instrumentation",
            "success": True,
            "attempts": 0,
            "instrumentation": True
        }
    )

    # Also log LLM token usage if configured
    try:
        # Import here to avoid circular dependency
        import token_estimator

        # Estimate tokens based on input length
        estimated_tokens = token_estimator.estimate_tokens("x" * input_length)

        vc_tracker.vc_step(
            "llm_token_usage",
            count=1,
            meta={
                "estimated_tokens": estimated_tokens,
                "method": "heuristic"
            }
        )

        print(f"[INFO] Token estimation: {estimated_tokens} tokens")
        result["estimated_tokens"] = estimated_tokens

    except ImportError:
        pass

    return result


def _calculate_backoff(
    attempt: int,
    retry_config: config.RetryConfig
) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current attempt number (1-based)
        retry_config: Retry configuration

    Returns:
        Delay in seconds
    """
    # Exponential backoff
    delay = retry_config.backoff_seconds * (2 ** (attempt - 1))

    # Cap at maximum
    delay = min(delay, retry_config.max_backoff_seconds)

    # Add jitter
    if retry_config.jitter > 0:
        jitter_range = delay * retry_config.jitter
        delay = delay + random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def _is_circuit_open(
    endpoint: str,
    cb_config: config.CircuitBreakerConfig
) -> bool:
    """
    Check if circuit breaker is open for an endpoint.

    Args:
        endpoint: API endpoint
        cb_config: Circuit breaker configuration

    Returns:
        True if circuit is open
    """
    now = time.time()
    state = _circuit_state.get(endpoint)

    if state is None:
        return False

    # Check if we're in cooldown period
    if state.get("state") == "open":
        # Check if cooldown has expired
        if now >= state.get("next_attempt_time", 0):
            # Half-open state - allow one trial
            state["state"] = "half_open"
            state["last_failure_time"] = now
            return False
        return True

    return False


def _update_circuit_breaker(
    endpoint: str,
    success: bool,
    cb_config: config.CircuitBreakerConfig
) -> None:
    """
    Update circuit breaker state.

    Args:
        endpoint: API endpoint
        success: Whether the call succeeded
        cb_config: Circuit breaker configuration
    """
    now = time.time()

    if endpoint not in _circuit_state:
        _circuit_state[endpoint] = {
            "state": "closed",
            "failure_count": 0,
            "failure_window_start": now,
            "last_failure_time": None,
            "next_attempt_time": None
        }

    state = _circuit_state[endpoint]

    if success:
        # Reset on success
        state["state"] = "closed"
        state["failure_count"] = 0
        state["failure_window_start"] = now
    else:
        # Increment failure count
        state["failure_count"] += 1
        state["last_failure_time"] = now

        # Check if we should open the circuit
        if state["state"] == "closed":
            # Check if we exceed threshold
            if state["failure_count"] >= cb_config.failure_threshold:
                state["state"] = "open"
                state["next_attempt_time"] = now + cb_config.reset_timeout
        elif state["state"] == "half_open":
            # Failure in half-open state opens circuit again
            state["state"] = "open"
            state["next_attempt_time"] = now + cb_config.reset_timeout


def _log_api_failure(
    job_id: str,
    endpoint: str,
    error: str,
    attempts: int,
    retry_config: config.RetryConfig
) -> Dict[str, Any]:
    """
    Log API call failure with retry information.

    Args:
        job_id: Job identifier
        endpoint: API endpoint
        error: Error message
        attempts: Number of attempts made
        retry_config: Retry configuration

    Returns:
        Failure result dictionary
    """
    print(f"[ERROR] API call failed after {attempts} attempts: {error}")

    # Log to VC
    vc_tracker.vc_step(
        "external_api_called",
        count=1,
        meta={
            "endpoint": endpoint,
            "success": False,
            "attempts": attempts,
            "max_attempts": retry_config.max_attempts,
            "error": error
        }
    )

    # Return failure result
    return {
        "success": False,
        "endpoint": endpoint,
        "error": error,
        "attempts": attempts,
        "max_attempts": retry_config.max_attempts,
        "payload": {
            "job_id": job_id
        }
    }


def get_circuit_breaker_state(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Get circuit breaker state for an endpoint.

    Args:
        endpoint: API endpoint

    Returns:
        State dictionary or None
    """
    return _circuit_state.get(endpoint)


def reset_circuit_breaker(endpoint: str) -> bool:
    """
    Reset circuit breaker for an endpoint.

    Args:
        endpoint: API endpoint

    Returns:
        True if state was reset
    """
    if endpoint in _circuit_state:
        _circuit_state[endpoint]["state"] = "closed"
        _circuit_state[endpoint]["failure_count"] = 0
        return True
    return False


def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """
    Get circuit breaker states for all endpoints.

    Returns:
        Dictionary of endpoint -> state
    """
    return _circuit_state.copy()
