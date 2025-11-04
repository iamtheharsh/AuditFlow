"""
Code Scanner Module

Recursively scans and analyzes source code files.
Combines AST parsing and pattern matching for comprehensive analysis.
"""

import os
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path

import utils
from detector_http import detect_http_apis
from detector_llm import detect_llm_usage
from detector_cloud import detect_cloud_usage


class CodeScanner:
    """Scans and analyzes source code files."""

    def __init__(
        self,
        target_dir: str,
        language: str = "python",
        logger: Any = None
    ):
        """
        Initialize scanner.

        Args:
            target_dir: Directory to scan
            language: Target language (python or js)
            logger: Audit logger instance
        """
        self.target_dir = os.path.abspath(target_dir)
        self.language = language.lower()
        self.logger = logger

        # Get source files
        extensions = [".py"] if self.language == "python" else [".js", ".jsx", ".ts", ".tsx"]
        self.source_files = utils.get_source_files(
            self.target_dir,
            extensions=extensions
        )

        # Statistics
        self.file_stats = {
            "total_files": len(self.source_files),
            "total_lines": 0,
            "total_code_lines": 0,
            "processed_files": 0
        }

    def scan(self) -> Dict[str, Any]:
        """
        Scan all source files.

        Returns:
            Scan results dictionary
        """
        if self.logger:
            self.logger.log_scan_start(self.target_dir, self.language)

        all_detections = []
        all_stats = {
            "http_apis": [],
            "llm_usage": [],
            "cloud_usage": []
        }

        # Process each file
        for file_path in self.source_files:
            file_result = self._scan_file(file_path)
            all_detections.extend(file_result["detections"])
            all_stats["http_apis"].append(file_result["stats"]["http"])
            all_stats["llm_usage"].append(file_result["stats"]["llm"])
            all_stats["cloud_usage"].append(file_result["stats"]["cloud"])

        # Aggregate statistics
        aggregated_stats = self._aggregate_stats(all_stats)

        if self.logger:
            self.logger.log_scan_complete(
                files_scanned=self.file_stats["processed_files"],
                duration_seconds=aggregated_stats["scan_duration"]
            )

        return {
            "target_dir": self.target_dir,
            "language": self.language,
            "files_scanned": self.file_stats["processed_files"],
            "detections": all_detections,
            "statistics": aggregated_stats,
            "metadata": {
                "total_files": self.file_stats["total_files"],
                "total_lines": self.file_stats["total_lines"],
                "total_code_lines": self.file_stats["total_code_lines"],
                "vc_label": "codebase_scanned"
            }
        }

    def _scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with scan results
        """
        # Load file content
        content = utils.load_file_content(file_path)
        if not content:
            return {"detections": [], "stats": {"http": {}, "llm": {}, "cloud": {}}}

        # Update file statistics
        total_lines, code_lines = utils.count_lines(file_path)
        self.file_stats["total_lines"] += total_lines
        self.file_stats["total_code_lines"] += code_lines
        self.file_stats["processed_files"] += 1

        if self.logger:
            self.logger.log_file_processed(
                file_path=file_path,
                file_type=Path(file_path).suffix[1:],
                lines_of_code=code_lines
            )

        # Run detectors
        http_detections, http_stats = detect_http_apis(file_path, content, self.logger)
        llm_detections, llm_stats = detect_llm_usage(file_path, content, self.logger)
        cloud_detections, cloud_stats = detect_cloud_usage(file_path, content, self.logger)

        # Combine all detections
        all_detections = http_detections + llm_detections + cloud_detections

        return {
            "file": file_path,
            "detections": all_detections,
            "stats": {
                "http": http_stats,
                "llm": llm_stats,
                "cloud": cloud_stats
            }
        }

    def _aggregate_stats(self, all_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate statistics from all files.

        Args:
            all_stats: Statistics from all files

        Returns:
            Aggregated statistics
        """
        # Aggregate HTTP stats
        http_total = sum(s.get("total", 0) for s in all_stats["http_apis"])
        http_external = sum(s.get("external", 0) for s in all_stats["http_apis"])

        # Aggregate LLM stats
        llm_total = sum(s.get("total", 0) for s in all_stats["llm_usage"])
        llm_total_tokens = sum(s.get("total_estimated_tokens", 0) for s in all_stats["llm_usage"])

        # Aggregate cloud stats
        cloud_total = sum(s.get("total", 0) for s in all_stats["cloud_usage"])
        cloud_services = set()
        compute_frameworks = set()
        for s in all_stats["cloud_usage"]:
            cloud_services.update(s.get("cloud_services", []))
            compute_frameworks.update(s.get("compute_frameworks", []))

        return {
            "scan_duration": 0,  # Will be set by caller
            "http_apis": {
                "total": http_total,
                "external": http_external,
                "internal": http_total - http_external
            },
            "llm_usage": {
                "total": llm_total,
                "total_estimated_tokens": llm_total_tokens
            },
            "cloud_usage": {
                "total": cloud_total,
                "cloud_services": list(cloud_services),
                "compute_frameworks": list(compute_frameworks)
            }
        }

    def get_file_structure(self) -> List[Dict[str, Any]]:
        """
        Get file structure information.

        Returns:
            List of file metadata
        """
        file_structure = []

        for file_path in self.source_files:
            metadata = utils.get_file_metadata(file_path)
            file_structure.append(metadata)

        return file_structure


def scan_codebase(
    target_dir: str,
    language: str = "python",
    output_dir: str = "output",
    logger: Any = None
) -> Dict[str, Any]:
    """
    Scan a codebase with timing.

    Args:
        target_dir: Directory to scan
        language: Target language
        output_dir: Output directory
        logger: Audit logger

    Returns:
        Scan results
    """
    with utils.Timer() as timer:
        scanner = CodeScanner(target_dir, language, logger)
        results = scanner.scan()

    # Add scan duration
    results["statistics"]["scan_duration"] = timer.seconds

    return results
