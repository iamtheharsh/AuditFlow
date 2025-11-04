"""
Structured Logging Module (Phase 2)

Provides structured logging with JSON lines output.
Supports both console and file logging with rotation.
Mirrors logs to output/<JOB_ID>_log.jsonl for programmatic consumption.
"""

import sys
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import config


class StructuredLogger:
    """Structured logger with JSON output and redaction support."""

    def __init__(
        self,
        job_id: str,
        level: str = "INFO",
        output_dir: str = "output"
    ):
        """
        Initialize structured logger.

        Args:
            job_id: Job identifier for log correlation
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_dir: Output directory for log files
        """
        self.job_id = job_id
        self.level = level.upper()
        self.output_dir = output_dir
        self.log_file_path = None
        self.console_enabled = True

        # Get logging configuration
        logging_config = config.get_config().logging

        self.console_enabled = logging_config.console_enabled
        self.verbose = logging_config.verbose

        if logging_config.verbose:
            self.level = "DEBUG"

        # Set up file logging if enabled
        if logging_config.file_enabled:
            os.makedirs(output_dir, exist_ok=True)
            self.log_file_path = os.path.join(output_dir, f"{job_id}_log.jsonl")

    def _should_log(self, level: str) -> bool:
        """Check if message should be logged based on level."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_index = levels.index(level)
        min_level_index = levels.index(self.level)
        return level_index >= min_level_index

    def _log(
        self,
        level: str,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Internal log method.

        Args:
            level: Log level
            message: Log message
            module: Module name
            metadata: Optional metadata
        """
        if not self._should_log(level):
            return

        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "job_id": self.job_id,
            "module": module,
            "message": message
        }

        # Add metadata if provided
        if metadata:
            log_entry["metadata"] = metadata

        # Write to JSONL file
        if self.log_file_path:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                # Fallback to stderr if file write fails
                print(f"[WARN] Failed to write to log file: {e}", file=sys.stderr)

        # Write to console
        if self.console_enabled:
            self._write_console_log(level, message, module, metadata)

    def debug(
        self,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log DEBUG message."""
        self._log("DEBUG", message, module, metadata)

    def info(
        self,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log INFO message."""
        self._log("INFO", message, module, metadata)

    def warning(
        self,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log WARNING message."""
        self._log("WARNING", message, module, metadata)

    def error(
        self,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log ERROR message."""
        self._log("ERROR", message, module, metadata)

    def critical(
        self,
        message: str,
        module: str = "root",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log CRITICAL message."""
        self._log("CRITICAL", message, module, metadata)

    def _write_console_log(
        self,
        level: str,
        message: str,
        module: str,
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """
        Write log to console with formatting.

        Args:
            level: Log level
            message: Log message
            module: Module name
            metadata: Optional metadata
        """
        # Get logging config for format
        logging_config = config.get_config().logging
        format_type = logging_config.format.lower()

        if format_type == "json":
            # JSON format for console
            log_entry = {
                "level": level,
                "module": module,
                "message": message
            }
            if metadata:
                log_entry["metadata"] = metadata

            print(f"[{json.dumps(log_entry)}]", file=sys.stdout)
        else:
            # Text format for console
            prefix = f"[{level}] [{module}]" if module != "root" else f"[{level}]"

            if metadata:
                metadata_str = f" {json.dumps(metadata)}"
            else:
                metadata_str = ""

            print(f"{prefix} {message}{metadata_str}", file=sys.stdout)

    def add_metric(
        self,
        name: str,
        value: Any,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Log a metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags
        """
        self.info(
            f"Metric: {name}={value}",
            module="metrics",
            metadata={
                "metric_name": name,
                "metric_value": value,
                "tags": tags or {}
            }
        )

    def add_vc_event(
        self,
        event_name: str,
        count: int,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a Value Credit event.

        Args:
            event_name: VC event name
            count: Event count
            duration_ms: Optional duration
            metadata: Optional metadata
        """
        self.info(
            f"VC Event: {event_name} (count: {count})",
            module="vc",
            metadata={
                "event_name": event_name,
                "count": count,
                "duration_ms": duration_ms,
                **(metadata or {})
            }
        )

    def log_red_flag(
        self,
        flag_type: str,
        value: str,
        confidence: str,
        line_number: int,
        context: str,
        redacted: bool = False
    ) -> None:
        """
        Log a red flag detection.

        Args:
            flag_type: Type of flag
            value: Flag value
            confidence: Confidence level
            line_number: Line number
            context: Context snippet
            redacted: Whether value is redacted
        """
        self.warning(
            f"Red Flag: {flag_type} (confidence: {confidence})",
            module="detector",
            metadata={
                "flag_type": flag_type,
                "value": value if not redacted else "REDACTED",
                "redacted": redacted,
                "confidence": confidence,
                "line_number": line_number,
                "context": context
            }
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: Optional[int],
        latency_ms: float,
        success: bool,
        attempts: int,
        error: Optional[str] = None
    ) -> None:
        """
        Log an API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            latency_ms: Latency in milliseconds
            success: Whether call succeeded
            attempts: Number of attempts made
            error: Optional error message
        """
        level = "INFO" if success else "WARNING"
        log_level_fn = self.info if success else self.warning

        log_level_fn(
            f"API Call: {method} {endpoint} - {status_code or 'N/A'} "
            f"({latency_ms:.1f}ms, {attempts} attempts)",
            module="api",
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "success": success,
                "attempts": attempts,
                "error": error
            }
        )

    def log_error_with_context(
        self,
        error: Exception,
        module: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Log an error with context.

        Args:
            error: Exception object
            module: Module name
            context: Context dictionary
        """
        self.error(
            f"Error in {module}: {type(error).__name__}: {error}",
            module=module,
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
        )


def get_logger(
    job_id: str,
    module: str = "root",
    level: Optional[str] = None
) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        job_id: Job identifier
        module: Module name
        level: Optional log level override

    Returns:
        StructuredLogger instance
    """
    logging_config = config.get_config().logging
    log_level = level or logging_config.level
    output_dir = config.get_config().general.output_dir

    return StructuredLogger(
        job_id=job_id,
        level=log_level,
        output_dir=output_dir
    )


def read_log_file(log_file_path: str) -> list:
    """
    Read a JSONL log file.

    Args:
        log_file_path: Path to log file

    Returns:
        List of log entries
    """
    logs = []
    if not os.path.exists(log_file_path):
        return logs

    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                continue

    return logs


def filter_logs_by_level(logs: list, min_level: str) -> list:
    """
    Filter logs by minimum level.

    Args:
        logs: List of log entries
        min_level: Minimum level to include

    Returns:
        Filtered list
    """
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    min_level_index = levels.index(min_level)

    return [
        log for log in logs
        if log.get("level") and levels.index(log["level"]) >= min_level_index
    ]
