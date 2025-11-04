"""
Cloud/Compute Library Detector Module

Detects cloud service usage and compute library imports.
Supports AWS (boto3), Google Cloud, Azure, and ML frameworks.
"""

import re
from typing import List, Dict, Any, Tuple
from pathlib import Path

import utils


class CloudDetector:
    """Detects cloud and compute library usage in source code."""

    def __init__(self):
        """Initialize detector with patterns."""
        # Cloud service patterns
        self.cloud_patterns = {
            "aws": [
                r"import boto3",
                r"from boto3 import",
                r"boto3\.client\(",
                r"boto3\.resource\(",
            ],
            "google_cloud": [
                r"from google\.cloud import",
                r"import google\.cloud",
                r"google\.cloud\.(storage|bigquery|pubsub)",
            ],
            "azure": [
                r"from azure",
                r"import azure",
                r"azure\.storage",
                r"azure\.cosmosdb",
            ],
            "aws_s3": [
                r"s3\.Bucket\(",
                r"s3\.Object\(",
                r"s3\.upload_file\(",
            ],
            "aws_dynamodb": [
                r"dynamodb\.Table\(",
                r"dynamodb\.batch_write_item\(",
            ],
        }

        # Compute/ML framework patterns
        self.compute_patterns = {
            "pytorch": [
                r"import torch",
                r"from torch import",
                r"torch\.",
            ],
            "tensorflow": [
                r"import tensorflow",
                r"from tensorflow import",
                r"tf\.",
            ],
            "sklearn": [
                r"import sklearn",
                r"from sklearn import",
            ],
            "numpy": [
                r"import numpy",
                r"from numpy import",
                r"np\.",
            ],
            "pandas": [
                r"import pandas",
                r"from pandas import",
                r"pd\.",
            ],
            "scipy": [
                r"import scipy",
                r"from scipy import",
            ],
            "onnx": [
                r"import onnx",
                r"import onnxruntime",
            ],
            "huggingface": [
                r"from transformers import",
                r"import transformers",
            ],
        }

    def detect_in_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Detect cloud/compute usage in a file.

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

        return detections

    def _detect_python(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect cloud/compute usage in Python code.

        Args:
            content: Python code
            file_path: File path

        Returns:
            List of detections
        """
        detections = []

        # Check cloud patterns
        for library, patterns in self.cloud_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    detection = {
                        "type": "cloud_library",
                        "file": file_path,
                        "line": line_number,
                        "library": library,
                        "category": "cloud_service",
                        "pattern": match.group(0).strip(),
                        "usage_type": self._determine_usage_type(library),
                        "vm_label": "cloud_compute_usage"
                    }

                    detections.append(detection)

        # Check compute patterns
        for library, patterns in self.compute_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    # Only flag as compute if it's a substantial usage
                    if self._is_substantial_usage(content, match.start()):
                        detection = {
                            "type": "cloud_library",
                            "file": file_path,
                            "line": line_number,
                            "library": library,
                            "category": "compute_framework",
                            "pattern": match.group(0).strip(),
                            "usage_type": self._determine_usage_type(library),
                            "vm_label": "cloud_compute_usage"
                        }

                        detections.append(detection)

        return detections

    def _is_substantial_usage(self, content: str, match_start: int) -> bool:
        """
        Check if usage is substantial (not just import).

        Args:
            content: File content
            match_start: Start position of match

        Returns:
            True if substantial usage
        """
        # Look ahead to see if there's actual usage beyond import
        end_pos = min(match_start + 200, len(content))
        context = content[match_start:end_pos]

        # If it's just an import statement, check if there's more usage
        if re.match(r'^\s*(import|from)', context.strip()):
            # Check if the line has more than just import
            first_line = context.split('\n')[0]
            if not re.search(r'import.*\s+as\s+\w+', first_line):
                # Not a substantial import, might be just importing
                return False

        return True

    def _determine_usage_type(self, library: str) -> str:
        """
        Determine the type of cloud/compute usage.

        Args:
            library: Library name

        Returns:
            Usage type string
        """
        cloud_types = ["aws", "google_cloud", "azure", "aws_s3", "aws_dynamodb"]
        compute_types = ["pytorch", "tensorflow", "onnx", "huggingface"]

        if library in cloud_types:
            return "cloud_service"
        elif library in compute_types:
            return "local_compute"
        else:
            return "data_processing"

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
                "cloud_services": [],
                "compute_frameworks": []
            }

        # Group by category
        cloud_services = []
        compute_frameworks = []

        for d in detections:
            if d.get("category") == "cloud_service":
                cloud_services.append(d.get("library"))
            else:
                compute_frameworks.append(d.get("library"))

        # Remove duplicates and count
        cloud_services = list(set(cloud_services))
        compute_frameworks = list(set(compute_frameworks))

        return {
            "total": len(detections),
            "cloud_services": cloud_services,
            "compute_frameworks": compute_frameworks,
            "cloud_service_count": len(cloud_services),
            "compute_framework_count": len(compute_frameworks)
        }


def detect_cloud_usage(
    file_path: str,
    content: str,
    logger: Any
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detect cloud/compute usage in a file with logging.

    Args:
        file_path: Path to file
        content: File content
        logger: Audit logger instance

    Returns:
        Tuple of (detections, statistics)
    """
    detector = CloudDetector()
    detections = detector.detect_in_file(file_path, content)

    # Log each detection
    for detection in detections:
        logger.log_cloud_detection(
            file_path=detection["file"],
            line_number=detection["line"],
            library=detection["library"],
            usage_type=detection["usage_type"]
        )

    stats = detector.get_statistics(detections)

    return detections, stats
