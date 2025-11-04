"""
VC Injection Module

Safely injects VC decorators and comments into code.
Creates patched copies without modifying original files.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import utils


class VCInjector:
    """Injects VC tracking into code."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize injector.

        Args:
            output_dir: Directory for patched files
        """
        self.output_dir = output_dir
        self.patched_dir = os.path.join(output_dir, "patched")
        os.makedirs(self.patched_dir, exist_ok=True)

    def inject_vc_tracking(
        self,
        file_path: str,
        detections: List[Dict[str, Any]],
        logger: Any = None
    ) -> Optional[str]:
        """
        Inject VC tracking into a file.

        Args:
            file_path: Path to source file
            detections: List of detections for this file
            logger: Audit logger

        Returns:
            Path to patched file or None
        """
        # Load source
        content = utils.load_file_content(file_path)
        if not content:
            return None

        # Get file extension
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".py":
            return self._inject_python(file_path, content, detections, logger)
        elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            return self._inject_javascript(file_path, content, detections, logger)

        return None

    def _inject_python(
        self,
        file_path: str,
        content: str,
        detections: List[Dict[str, Any]],
        logger: Any
    ) -> str:
        """
        Inject VC tracking into Python code.

        Args:
            file_path: Original file path
            content: Source content
            detections: List of detections
            logger: Audit logger

        Returns:
            Path to patched file
        """
        patched_lines = content.split('\n')
        injections_made = 0
        line_offset = 0

        # Sort detections by line number (descending to maintain offsets)
        detections_sorted = sorted(detections, key=lambda d: d.get("line", 0), reverse=True)

        for detection in detections_sorted:
            line_number = detection.get("line", 0)
            vm_label = detection.get("vm_label", "unknown_metric")
            detection_type = detection.get("type", "unknown")

            # Adjust for line offsets from previous injections
            actual_line = line_number + line_offset

            if actual_line <= 0 or actual_line > len(patched_lines):
                continue

            # Generate injection
            if detection_type == "external_api":
                injection = self._generate_api_injection(vm_label, detection)
            elif detection_type == "llm_usage":
                injection = self._generate_llm_injection(vm_label, detection)
            elif detection_type == "cloud_library":
                injection = self._generate_cloud_injection(vm_label, detection)
            else:
                injection = f"# [VC_INJECT] {vm_label}\n"

            # Insert injection
            patched_lines.insert(actual_line - 1, injection)
            line_offset += 1
            injections_made += 1

            # Log injection
            if logger:
                logger.log_injection_proposal(
                    file_path=file_path,
                    line_number=line_number,
                    injection_type=detection_type,
                    suggestion=injection.strip()
                )

        # Write patched file
        relative_path = os.path.relpath(file_path, self.output_dir)
        patched_file_path = os.path.join(self.patched_dir, relative_path)

        # Create directory if needed
        os.makedirs(os.path.dirname(patched_file_path), exist_ok=True)

        with open(patched_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(patched_lines))

        # Log successful injection
        if logger and injections_made > 0:
            logger.log_injection_success(
                original_file=file_path,
                patched_file=patched_file_path,
                injections_count=injections_made
            )

        return patched_file_path

    def _inject_javascript(
        self,
        file_path: str,
        content: str,
        detections: List[Dict[str, Any]],
        logger: Any
    ) -> str:
        """
        Inject VC tracking into JavaScript code.

        Args:
            file_path: Original file path
            content: Source content
            detections: List of detections
            logger: Audit logger

        Returns:
            Path to patched file
        """
        # JavaScript injection (comments only for now)
        patched_lines = content.split('\n')
        injections_made = 0
        line_offset = 0

        detections_sorted = sorted(detections, key=lambda d: d.get("line", 0), reverse=True)

        for detection in detections_sorted:
            line_number = detection.get("line", 0)
            vm_label = detection.get("vm_label", "unknown_metric")

            actual_line = line_number + line_offset

            if actual_line <= 0 or actual_line > len(patched_lines):
                continue

            # Generate comment injection
            injection = f"// [VC_INJECT] {vm_label}\n"

            patched_lines.insert(actual_line - 1, injection)
            line_offset += 1
            injections_made += 1

            if logger:
                logger.log_injection_proposal(
                    file_path=file_path,
                    line_number=line_number,
                    injection_type=detection.get("type", "unknown"),
                    suggestion=injection.strip()
                )

        # Write patched file
        relative_path = os.path.relpath(file_path, self.output_dir)
        patched_file_path = os.path.join(self.patched_dir, relative_path)

        os.makedirs(os.path.dirname(patched_file_path), exist_ok=True)

        with open(patched_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(patched_lines))

        if logger and injections_made > 0:
            logger.log_injection_success(
                original_file=file_path,
                patched_file=patched_file_path,
                injections_count=injections_made
            )

        return patched_file_path

    def _generate_api_injection(
        self,
        vm_label: str,
        detection: Dict[str, Any]
    ) -> str:
        """Generate API injection comment."""
        endpoint = detection.get("endpoint", "unknown")
        method = detection.get("method", "UNKNOWN")

        return (
            f"# [VC] {vm_label} detected here - {method} {endpoint}\n"
            f"# Suggested: Add @vc_tracker('{vm_label}') decorator or vc_step() call\n"
        )

    def _generate_llm_injection(
        self,
        vm_label: str,
        detection: Dict[str, Any]
    ) -> str:
        """Generate LLM injection comment."""
        library = detection.get("library", "unknown")
        model = detection.get("model", "unknown")

        token_info = ""
        if detection.get("estimated_tokens"):
            token_info = f", est. {detection['estimated_tokens']} tokens"

        return (
            f"# [VC] {vm_label} detected here - {library} model={model}{token_info}\n"
            f"# Suggested: Add @vc_tracker('{vm_label}') with token tracking\n"
        )

    def _generate_cloud_injection(
        self,
        vm_label: str,
        detection: Dict[str, Any]
    ) -> str:
        """Generate cloud injection comment."""
        library = detection.get("library", "unknown")
        usage_type = detection.get("usage_type", "unknown")

        return (
            f"# [VC] {vm_label} detected here - {library} ({usage_type})\n"
            f"# Suggested: Add @vc_tracker('{vm_label}') decorator\n"
        )

    def get_injection_summary(self, patched_files: List[str]) -> Dict[str, Any]:
        """
        Get summary of injections made.

        Args:
            patched_files: List of patched file paths

        Returns:
            Summary dictionary
        """
        if not patched_files:
            return {
                "files_patched": 0,
                "total_injections": 0,
                "patched_dir": self.patched_dir
            }

        total_injections = 0
        for file_path in patched_files:
            if not os.path.exists(file_path):
                continue

            # Count injections in file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                injections = content.count('[VC_INJECT]')
                total_injections += injections

        return {
            "files_patched": len(patched_files),
            "total_injections": total_injections,
            "patched_dir": self.patched_dir
        }


def inject_vc_decorators(
    scan_results: Dict[str, Any],
    output_dir: str = "output",
    logger: Any = None
) -> Dict[str, Any]:
    """
    Inject VC decorators into codebase.

    Args:
        scan_results: Results from code scanner
        output_dir: Output directory
        logger: Audit logger

    Returns:
        Injection results
    """
    injector = VCInjector(output_dir=output_dir)
    patched_files = []

    # Group detections by file
    detections_by_file = {}
    for detection in scan_results.get("detections", []):
        file_path = detection["file"]
        if file_path not in detections_by_file:
            detections_by_file[file_path] = []
        detections_by_file[file_path].append(detection)

    # Inject into each file
    for file_path, detections in detections_by_file.items():
        patched_file = injector.inject_vc_tracking(file_path, detections, logger)
        if patched_file:
            patched_files.append(patched_file)

    # Get summary
    summary = injector.get_injection_summary(patched_files)

    if logger:
        logger.log_vc_event(
            event_name="vc_injections_created",
            count=summary["total_injections"],
            metadata=summary
        )

    return {
        "patched_files": patched_files,
        "summary": summary
    }
