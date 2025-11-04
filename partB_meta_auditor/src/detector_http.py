"""
HTTP/API Detector Module

Detects external API calls in code using pattern matching and AST analysis.
Supports Python (requests, httpx, urllib) and JavaScript (fetch, axios).
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import utils


class HTTPAPIDetector:
    """Detects HTTP/API calls in source code."""

    def __init__(self):
        """Initialize detector with patterns."""
        # Python patterns
        self.python_patterns = {
            "requests": [
                r"requests\.(get|post|put|patch|delete|head|options)\(",
                r"requests\.Session\(\)\.(get|post|put|patch|delete|head|options)\(",
            ],
            "httpx": [
                r"httpx\.(get|post|put|patch|delete|head|options)\(",
                r"httpx\.Client\(\)\.(get|post|put|patch|delete|head|options)\(",
            ],
            "urllib": [
                r"urllib\.request\.(urlopen|urlretrieve)\(",
                r"urllib\.parse\.(urlopen|urlretrieve)\(",
            ],
            "aiohttp": [
                r"aiohttp\.(ClientSession|get|post|put|patch|delete)\(",
            ],
        }

        # JavaScript patterns
        self.js_patterns = {
            "fetch": [
                r"fetch\s*\(",
                r"window\.fetch\s*\(",
            ],
            "axios": [
                r"axios\.(get|post|put|patch|delete|head|options)\(",
                r"axios\.request\s*\(",
            ],
            "node_fetch": [
                r"node-fetch\s*\(",
                r"require\s*\(\s*['\"]node-fetch['\"]",
            ],
        }

    def detect_in_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Detect HTTP/API calls in a file.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of detection results
        """
        detections = []
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".py":
            detections = self._detect_python(content, file_path)
        elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            detections = self._detect_javascript(content, file_path)

        return detections

    def _detect_python(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect HTTP calls in Python code.

        Args:
            content: Python code
            file_path: File path

        Returns:
            List of detections
        """
        detections = []

        # Check each pattern
        for library, patterns in self.python_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    # Extract details
                    method = self._extract_method(match.group(0))
                    endpoint = self._extract_endpoint(content, match.start())

                    # Determine if external
                    is_external = endpoint and utils.is_external_url(endpoint)

                    detection = {
                        "type": "external_api",
                        "file": file_path,
                        "line": line_number,
                        "library": library,
                        "pattern": match.group(0).strip(),
                        "method": method,
                        "endpoint": endpoint,
                        "is_external": is_external,
                        "vm_label": "external_api_call"
                    }

                    detections.append(detection)

        return detections

    def _detect_javascript(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect HTTP calls in JavaScript code.

        Args:
            content: JavaScript code
            file_path: File path

        Returns:
            List of detections
        """
        detections = []

        # Check each pattern
        for library, patterns in self.js_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    # Extract details
                    method = self._extract_method(match.group(0))
                    endpoint = self._extract_endpoint(content, match.start())

                    # Determine if external
                    is_external = endpoint and utils.is_external_url(endpoint)

                    detection = {
                        "type": "external_api",
                        "file": file_path,
                        "line": line_number,
                        "library": library,
                        "pattern": match.group(0).strip(),
                        "method": method,
                        "endpoint": endpoint,
                        "is_external": is_external,
                        "vm_label": "external_api_call"
                    }

                    detections.append(detection)

        return detections

    def _extract_method(self, match_text: str) -> Optional[str]:
        """
        Extract HTTP method from match.

        Args:
            match_text: Matched text

        Returns:
            HTTP method or None
        """
        method_patterns = {
            r'\.(get|post|put|patch|delete|head|options)\(': r'\.(get|post|put|patch|delete|head|options)',
            r'fetch\s*\(': 'fetch',
        }

        for pattern, method_group in method_patterns.items():
            match = re.search(pattern, match_text)
            if match:
                method_match = re.search(method_group, match.group(0))
                if method_match:
                    return method_match.group(0).lstrip('.').upper()

        return None

    def _extract_endpoint(self, content: str, match_start: int) -> Optional[str]:
        """
        Extract endpoint URL from code context.

        Args:
            content: Full file content
            match_start: Start position of match

        Returns:
            Extracted URL or None
        """
        # Look for string literals in the next few lines
        end_pos = min(match_start + 500, len(content))  # Look ahead max 500 chars
        context = content[match_start:end_pos]

        # Find URL in the context
        urls = utils.find_url_patterns(context)

        if urls:
            return urls[0]

        # Try to extract from string literals using AST
        try:
            # Find the line
            line_start = content.rfind('\n', 0, match_start) + 1
            line_end = content.find('\n', match_start)
            if line_end == -1:
                line_end = len(content)

            line_content = content[line_start:line_end]

            # Look for quoted strings
            string_matches = re.findall(r'["\']([^"\']+)["\']', line_content)

            for string_val in string_matches:
                if utils.is_external_url(string_val):
                    return string_val

        except Exception:
            pass

        return None

    def get_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics from detections.

        Args:
            detections: List of detections

        Returns:
            Statistics dictionary
        """
        if not detections:
            return {
                "total": 0,
                "external": 0,
                "internal": 0,
                "libraries": {},
                "methods": {}
            }

        external_count = sum(1 for d in detections if d.get("is_external", False))
        internal_count = len(detections) - external_count

        # Count by library
        libraries = {}
        for d in detections:
            lib = d.get("library", "unknown")
            libraries[lib] = libraries.get(lib, 0) + 1

        # Count by method
        methods = {}
        for d in detections:
            method = d.get("method", "UNKNOWN")
            methods[method] = methods.get(method, 0) + 1

        return {
            "total": len(detections),
            "external": external_count,
            "internal": internal_count,
            "libraries": libraries,
            "methods": methods
        }


def detect_http_apis(
    file_path: str,
    content: str,
    logger: Any
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detect HTTP/API calls in a file with logging.

    Args:
        file_path: Path to file
        content: File content
        logger: Audit logger instance

    Returns:
        Tuple of (detections, statistics)
    """
    detector = HTTPAPIDetector()
    detections = detector.detect_in_file(file_path, content)

    # Log each detection
    for detection in detections:
        if detection.get("is_external", False):
            logger.log_external_api_detection(
                file_path=detection["file"],
                line_number=detection["line"],
                endpoint=detection.get("endpoint", ""),
                method=detection.get("method", "UNKNOWN"),
                is_external=detection["is_external"]
            )

    stats = detector.get_statistics(detections)

    return detections, stats
