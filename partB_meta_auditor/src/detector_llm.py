"""
LLM/AI Model Detector Module

Detects LLM and AI model usage in code.
Supports OpenAI, Anthropic, Hugging Face Transformers, and other AI libraries.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import utils


class LLMDetector:
    """Detects LLM and AI model usage in source code."""

    def __init__(self):
        """Initialize detector with patterns."""
        # LLM patterns
        self.llm_patterns = {
            "openai": [
                r"openai\.(ChatCompletion|Completion|Chat)\.create\(",
                r"openai\.chat\.(completions|chat)\.create\(",
                r"openai\.(ChatClient|Client)\(",
                r"client\.chat\.completions\.create\(",
                r"client\.completions\.create\(",
            ],
            "anthropic": [
                r"anthropic\.(Anthropic|Client)\(",
                r"client\.messages\.create\(",
            ],
            "huggingface": [
                r"from transformers import",
                r"import transformers",
                r"pipeline\s*\(",
                r"AutoModelForCausalLM\.from_pretrained\(",
                r"AutoTokenizer\.from_pretrained\(",
                r"model\.generate\(",
                r"model\.forward\(",
            ],
            "langchain": [
                r"from langchain",
                r"import langchain",
                r"LLMChain\(",
                r"ChatOpenAI\(",
                r"ChatAnthropic\(",
            ],
            "pytorch": [
                r"torch\.(load|save)",
                r"model\.to\(",
                r"model\.eval\(",
                r"model\.train\(",
            ],
            "tensorflow": [
                r"import tensorflow",
                r"from tensorflow",
                r"tf\.(compile|fit|predict)",
            ],
            "tiktoken": [
                r"tiktoken\.get_encoding\(",
                r"tiktoken\.encode\(",
            ],
        }

        # Token-related patterns
        self.token_patterns = [
            r'max_tokens\s*=\s*(\d+)',
            r'max_completion_tokens\s*=\s*(\d+)',
            r'token_limit\s*=\s*(\d+)',
            r'context_length\s*=\s*(\d+)',
        ]

    def detect_in_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Detect LLM usage in a file.

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
        Detect LLM usage in Python code.

        Args:
            content: Python code
            file_path: File path

        Returns:
            List of detections
        """
        detections = []

        for library, patterns in self.llm_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1

                    # Extract details
                    model = self._extract_model_parameter(content, match.start())
                    tokens = self._extract_token_estimate(content, match.start())
                    usage_type = self._determine_usage_type(library, match.group(0))

                    detection = {
                        "type": "llm_usage",
                        "file": file_path,
                        "line": line_number,
                        "library": library,
                        "pattern": match.group(0).strip(),
                        "model": model,
                        "estimated_tokens": tokens,
                        "usage_type": usage_type,
                        "vm_label": "llm_token_usage"
                    }

                    detections.append(detection)

        return detections

    def _extract_model_parameter(self, content: str, match_start: int) -> Optional[str]:
        """
        Extract model parameter value.

        Args:
            content: Full file content
            match_start: Start position of match

        Returns:
            Model name or None
        """
        # Look in the function call for model parameter
        end_pos = min(match_start + 1000, len(content))
        context = content[match_start:end_pos]

        # Common model parameter patterns
        model_patterns = [
            r'model\s*=\s*["\']([^"\']+)["\']',
            r'model_name\s*=\s*["\']([^"\']+)["\']',
            r'engine\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)

        return None

    def _extract_token_estimate(self, content: str, match_start: int) -> Optional[int]:
        """
        Extract token-related parameters for estimation.

        Args:
            content: Full file content
            match_start: Start position of match

        Returns:
            Estimated token count or None
        """
        end_pos = min(match_start + 1000, len(content))
        context = content[match_start:end_pos]

        max_tokens = None
        for pattern in self.token_patterns:
            match = re.search(pattern, context)
            if match:
                try:
                    max_tokens = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue

        # Estimate total tokens (prompt + completion)
        if max_tokens:
            # Assume 50/50 split between input and output
            return max_tokens * 2

        return None

    def _determine_usage_type(self, library: str, pattern: str) -> str:
        """
        Determine the type of usage.

        Args:
            library: Library name
            pattern: Matched pattern

        Returns:
            Usage type string
        """
        if "create" in pattern or "generate" in pattern:
            return "inference"
        elif "from_pretrained" in pattern or "load" in pattern:
            return "model_loading"
        elif "encode" in pattern:
            return "tokenization"
        elif library in ["torch", "tensorflow"]:
            return "local_inference"
        else:
            return "api_call"

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
                "libraries": {},
                "usage_types": {},
                "with_models": 0,
                "with_token_estimates": 0
            }

        # Count by library
        libraries = {}
        for d in detections:
            lib = d.get("library", "unknown")
            libraries[lib] = libraries.get(lib, 0) + 1

        # Count by usage type
        usage_types = {}
        for d in detections:
            usage = d.get("usage_type", "unknown")
            usage_types[usage] = usage_types.get(usage, 0) + 1

        # Count with model information
        with_models = sum(1 for d in detections if d.get("model"))

        # Count with token estimates
        with_token_estimates = sum(1 for d in detections if d.get("estimated_tokens"))

        # Total estimated tokens
        total_tokens = sum(
            d.get("estimated_tokens", 0)
            for d in detections
            if d.get("estimated_tokens")
        )

        return {
            "total": len(detections),
            "libraries": libraries,
            "usage_types": usage_types,
            "with_models": with_models,
            "with_token_estimates": with_token_estimates,
            "total_estimated_tokens": total_tokens
        }


def detect_llm_usage(
    file_path: str,
    content: str,
    logger: Any
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detect LLM usage in a file with logging.

    Args:
        file_path: Path to file
        content: File content
        logger: Audit logger instance

    Returns:
        Tuple of (detections, statistics)
    """
    detector = LLMDetector()
    detections = detector.detect_in_file(file_path, content)

    # Log each detection
    for detection in detections:
        logger.log_llm_detection(
            file_path=detection["file"],
            line_number=detection["line"],
            library=detection["library"],
            model=detection.get("model"),
            tokens=detection.get("estimated_tokens")
        )

    stats = detector.get_statistics(detections)

    return detections, stats
