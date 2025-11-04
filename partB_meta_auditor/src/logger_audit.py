"""
Structured Audit Logging Module

Provides structured logging for audit events in JSONL format.
Supports correlation via job IDs and module tagging.
"""

import sys
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from ..partA_document_agent.src import vc_tracker
except ImportError:
    # Fallback if Part A is not available
    vc_tracker = None


class AuditLogger:
    """Structured logger for audit events."""

    def __init__(
        self,
        output_dir: str = "output",
        job_id: Optional[str] = None
    ):
        """
        Initialize audit logger.

        Args:
            output_dir: Directory for log files
            job_id: Optional job identifier
        """
        self.output_dir = output_dir
        self.job_id = job_id or f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.log_file_path = os.path.join(output_dir, f"{self.job_id}_audit_log.jsonl")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _log_event(
        self,
        event_type: str,
        message: str,
        module: str = "meta_auditor",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            message: Event message
            module: Module name
            metadata: Optional metadata

        Returns:
            Log entry dictionary
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "job_id": self.job_id,
            "event_type": event_type,
            "module": module,
            "message": message,
            "metadata": metadata or {}
        }

        # Write to JSONL file
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[WARN] Failed to write to audit log: {e}", file=sys.stderr)

        # Log to console
        print(f"[AUDIT] {event_type}: {message}")

        return log_entry

    def log_scan_start(self, target_path: str, language: str) -> None:
        """Log scan start event."""
        self._log_event(
            "SCAN_START",
            f"Starting audit scan of {target_path}",
            metadata={
                "target_path": target_path,
                "language": language
            }
        )

    def log_scan_complete(
        self,
        files_scanned: int,
        duration_seconds: float
    ) -> None:
        """Log scan completion event."""
        self._log_event(
            "SCAN_COMPLETE",
            f"Scan complete: {files_scanned} files in {duration_seconds:.2f}s",
            metadata={
                "files_scanned": files_scanned,
                "duration_seconds": duration_seconds
            }
        )

    def log_file_processed(
        self,
        file_path: str,
        file_type: str,
        lines_of_code: int
    ) -> None:
        """Log file processing event."""
        self._log_event(
            "FILE_PROCESSED",
            f"Processed {file_type} file: {Path(file_path).name}",
            module="code_scanner",
            metadata={
                "file_path": file_path,
                "file_type": file_type,
                "lines_of_code": lines_of_code
            }
        )

    def log_detection(
        self,
        detection_type: str,
        file_path: str,
        line_number: int,
        pattern: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a detection event."""
        self._log_event(
            f"DETECTION_{detection_type.upper()}",
            f"Found {detection_type} in {Path(file_path).name}:{line_number}",
            module=detection_type,
            metadata={
                "file_path": file_path,
                "line_number": line_number,
                "pattern": pattern,
                **(metadata or {})
            }
        )

    def log_external_api_detection(
        self,
        file_path: str,
        line_number: int,
        endpoint: str,
        method: str,
        is_external: bool
    ) -> None:
        """Log external API detection."""
        self._log_event(
            "EXTERNAL_API_DETECTED",
            f"External API call: {method} {endpoint}",
            module="detector_http",
            metadata={
                "file_path": file_path,
                "line_number": line_number,
                "endpoint": endpoint,
                "method": method,
                "is_external": is_external,
                "vm_label": "external_api_call"
            }
        )

    def log_llm_detection(
        self,
        file_path: str,
        line_number: int,
        library: str,
        model: Optional[str] = None,
        tokens: Optional[int] = None
    ) -> None:
        """Log LLM usage detection."""
        self._log_event(
            "LLM_USAGE_DETECTED",
            f"LLM usage: {library}",
            module="detector_llm",
            metadata={
                "file_path": file_path,
                "line_number": line_number,
                "library": library,
                "model": model,
                "estimated_tokens": tokens,
                "vm_label": "llm_token_usage"
            }
        )

    def log_cloud_detection(
        self,
        file_path: str,
        line_number: int,
        library: str,
        usage_type: str
    ) -> None:
        """Log cloud/compute library detection."""
        self._log_event(
            "CLOUD_LIBRARY_DETECTED",
            f"Cloud library: {library}",
            module="detector_cloud",
            metadata={
                "file_path": file_path,
                "line_number": line_number,
                "library": library,
                "usage_type": usage_type,
                "vm_label": "cloud_compute_usage"
            }
        )

    def log_injection_proposal(
        self,
        file_path: str,
        line_number: int,
        injection_type: str,
        suggestion: str
    ) -> None:
        """Log VC injection proposal."""
        self._log_event(
            "INJECTION_PROPOSAL",
            f"Injection suggested: {injection_type}",
            module="injector",
            metadata={
                "file_path": file_path,
                "line_number": line_number,
                "injection_type": injection_type,
                "suggestion": suggestion
            }
        )

    def log_injection_success(
        self,
        original_file: str,
        patched_file: str,
        injections_count: int
    ) -> None:
        """Log successful injection."""
        self._log_event(
            "INJECTION_SUCCESS",
            f"Created patched file with {injections_count} injections",
            module="injector",
            metadata={
                "original_file": original_file,
                "patched_file": patched_file,
                "injections_count": injections_count
            }
        )

    def log_report_generation(
        self,
        report_path: str,
        report_type: str,
        findings_count: int
    ) -> None:
        """Log report generation."""
        self._log_event(
            "REPORT_GENERATED",
            f"Generated {report_type} report",
            module="report_builder",
            metadata={
                "report_path": report_path,
                "report_type": report_type,
                "findings_count": findings_count
            }
        )

    def log_vc_event(
        self,
        event_name: str,
        count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a Value Credit event."""
        self._log_event(
            "VC_EVENT",
            f"VC: {event_name}",
            module="vc_tracker",
            metadata={
                "event_name": event_name,
                "count": count,
                **(metadata or {})
            }
        )

        # Also log to VC tracker if available
        if vc_tracker:
            try:
                vc_tracker.vc_step(
                    name=event_name,
                    count=count,
                    meta=metadata
                )
            except Exception:
                pass  # Silently fail if VC tracker not properly initialized

    def log_error(
        self,
        error_message: str,
        module: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error."""
        self._log_event(
            "ERROR",
            f"Error in {module}: {error_message}",
            module=module,
            metadata={
                "error_type": "audit_error",
                **(context or {})
            }
        )

    def get_log_entries(self) -> list:
        """
        Read all log entries from file.

        Returns:
            List of log entry dictionaries
        """
        entries = []
        if not os.path.exists(self.log_file_path):
            return entries

        with open(self.log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries

    def filter_by_event_type(self, event_type: str) -> list:
        """
        Filter log entries by event type.

        Args:
            event_type: Event type to filter

        Returns:
            Filtered list of entries
        """
        return [
            entry for entry in self.get_log_entries()
            if entry.get("event_type") == event_type
        ]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get audit log summary.

        Returns:
            Summary dictionary
        """
        entries = self.get_log_entries()

        return {
            "job_id": self.job_id,
            "total_events": len(entries),
            "event_types": list(set(entry.get("event_type", "UNKNOWN") for entry in entries)),
            "log_file": self.log_file_path
        }


def get_audit_logger(
    output_dir: str = "output",
    job_id: Optional[str] = None
) -> AuditLogger:
    """
    Get an audit logger instance.

    Args:
        output_dir: Output directory
        job_id: Optional job ID

    Returns:
        AuditLogger instance
    """
    return AuditLogger(output_dir=output_dir, job_id=job_id)
