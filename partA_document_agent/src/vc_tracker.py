"""
Value Credit Tracker Module

Tracks all processing steps with timestamps, durations, and metadata.
Generates comprehensive JSON summaries for auditability.
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


# Global session storage
_VC_LOG: List[Dict[str, Any]] = []
_SESSION_JOB_ID: Optional[str] = None
_SESSION_START: Optional[str] = None


def init_session(job_id: str) -> None:
    """
    Initialize a new VC tracking session.

    Args:
        job_id: Unique identifier for this job (e.g., DOC-2025-001)
    """
    global _VC_LOG, _SESSION_JOB_ID, _SESSION_START

    _VC_LOG = []
    _SESSION_JOB_ID = job_id
    _SESSION_START = datetime.utcnow().isoformat() + "Z"

    print(f"[VC] Session initialized: {job_id}")


def vc_step(
    name: str,
    count: int = 1,
    duration_ms: Optional[float] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record a Value Credit step.

    Args:
        name: Name of the step (e.g., "text_extracted")
        count: Number of occurrences (default: 1)
        duration_ms: Optional duration in milliseconds
        meta: Optional metadata dictionary

    Returns:
        The recorded step dictionary
    """
    global _VC_LOG, _SESSION_START

    timestamp = datetime.utcnow().isoformat() + "Z"

    step = {
        "name": name,
        "count": count,
        "timestamp": timestamp
    }

    if duration_ms is not None:
        step["duration_ms"] = duration_ms

    if meta is not None:
        step["meta"] = meta

    _VC_LOG.append(step)

    # Log to console
    duration_str = f", duration: {duration_ms:.1f}ms" if duration_ms else ""
    meta_str = f", meta: {meta}" if meta else ""
    print(f"[VC] Step: {name} (count: {count}{duration_str}{meta_str})")

    return step


def get_vc_log() -> List[Dict[str, Any]]:
    """Get the current VC log."""
    return _VC_LOG.copy()


def get_session_job_id() -> Optional[str]:
    """Get the current session job ID."""
    return _SESSION_JOB_ID


def get_session_start() -> Optional[str]:
    """Get the current session start timestamp."""
    return _SESSION_START


def calculate_total_vc_steps() -> int:
    """
    Calculate total VC steps (sum of all counts).

    Returns:
        Total count across all steps
    """
    return sum(step["count"] for step in _VC_LOG)


def save_vc_summary(job_id: str, output_dir: str = "output") -> str:
    """
    Save the complete VC summary to JSON file.

    Args:
        job_id: Job identifier
        output_dir: Directory to save the file

    Returns:
        Path to the saved file
    """
    global _VC_LOG, _SESSION_START

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Build complete summary
    end_time = datetime.utcnow().isoformat() + "Z"

    summary = {
        "job_id": job_id,
        "vc_summary": _VC_LOG,
        "timestamps": {
            "start": _SESSION_START,
            "end": end_time
        },
        "total_vc_steps": calculate_total_vc_steps()
    }

    # Save to file
    output_path = os.path.join(output_dir, f"{job_id}_vc_summary.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[VC] Summary saved to: {output_path}")
    print(f"[VC] Total VC steps: {summary['total_vc_steps']}")

    return output_path


def log_error(job_id: str, step_name: str, error: Exception, output_dir: str = "output") -> str:
    """
    Log an error to a dedicated error file.

    Args:
        job_id: Job identifier
        step_name: Name of the step where error occurred
        error: The exception object
        output_dir: Directory to save the error file

    Returns:
        Path to the saved error file
    """
    os.makedirs(output_dir, exist_ok=True)

    error_data = {
        "job_id": job_id,
        "step": step_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    error_path = os.path.join(output_dir, f"{job_id}_error.json")

    with open(error_path, "w", encoding="utf-8") as f:
        json.dump(error_data, f, indent=2, ensure_ascii=False)

    print(f"[WARN] Error logged to: {error_path}")
    print(f"[WARN] {error_data['error_type']}: {error_data['error_message']}")

    return error_path
