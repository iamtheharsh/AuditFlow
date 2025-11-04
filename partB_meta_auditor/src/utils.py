"""
Utility Functions for Meta Auditor

Provides helper functions for file operations, regex matching, and timing.
"""

import os
import re
import ast
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


def is_file_excluded(file_path: str, exclude_patterns: List[str]) -> bool:
    """
    Check if a file should be excluded based on patterns.

    Args:
        file_path: Path to check
        exclude_patterns: List of patterns (e.g., ['__pycache__', 'node_modules'])

    Returns:
        True if file should be excluded
    """
    path = Path(file_path)
    path_str = str(path)

    for pattern in exclude_patterns:
        if pattern in path_str or path.name.startswith('.'):
            return True

    return False


def get_source_files(
    target_dir: str,
    extensions: List[str] = None,
    exclude_patterns: List[str] = None
) -> List[str]:
    """
    Recursively find source files in a directory.

    Args:
        target_dir: Directory to scan
        extensions: File extensions to include (e.g., ['.py', '.js'])
        exclude_patterns: Patterns to exclude

    Returns:
        List of file paths
    """
    if extensions is None:
        extensions = ['.py', '.js']

    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            '.venv',
            '.idea',
            '.vscode',
            '.tox',
            'build',
            'dist',
            '.pytest_cache'
        ]

    source_files = []

    for root, dirs, files in os.walk(target_dir):
        # Remove excluded directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if not is_file_excluded(os.path.join(root, d), exclude_patterns)]

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                if not is_file_excluded(file_path, exclude_patterns):
                    source_files.append(file_path)

    return source_files


def count_lines(file_path: str) -> Tuple[int, int]:
    """
    Count total lines and code lines in a file.

    Args:
        file_path: Path to file

    Returns:
        Tuple of (total_lines, code_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))

        return total_lines, code_lines
    except Exception:
        return 0, 0


def extract_string_literals(code: str) -> List[str]:
    """
    Extract string literals from code using AST.

    Args:
        code: Source code string

    Returns:
        List of string literals found
    """
    strings = []

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
            elif isinstance(node, ast.Str):  # Python < 3.8
                strings.append(node.s)
    except SyntaxError:
        # Fall back to regex if AST fails
        strings = re.findall(r'"([^"\\]|\\.)*"', code)

    return strings


def find_url_patterns(text: str) -> List[str]:
    """
    Find URL patterns in text.

    Args:
        text: Text to search

    Returns:
        List of URLs found
    """
    # Common URL patterns
    url_patterns = [
        r'https?://[^\s\'"<>]+',
        r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',
    ]

    urls = []
    for pattern in url_patterns:
        matches = re.findall(pattern, text)
        urls.extend(matches)

    return list(set(urls))  # Remove duplicates


def is_external_url(url: str) -> bool:
    """
    Check if a URL is external (not localhost or relative).

    Args:
        url: URL to check

    Returns:
        True if external URL
    """
    url_lower = url.lower()

    # Local URLs
    if url_lower.startswith(('http://localhost', 'http://127.0.0.1', 'https://localhost')):
        return False

    # Relative URLs
    if url_lower.startswith(('/', './', '../')):
        return False

    # Known external patterns
    external_domains = [
        'http://', 'https://', 'www.'
    ]

    return any(url_lower.startswith(domain) for domain in external_domains)


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return safe[:255]  # Limit length


def load_file_content(file_path: str) -> Optional[str]:
    """
    Safely load file content with multiple encodings.

    Args:
        file_path: Path to file

    Returns:
        File content or None if failed
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception:
            continue

    return None


def extract_function_calls(code: str) -> List[Dict[str, Any]]:
    """
    Extract function calls from code using AST.

    Args:
        code: Source code

    Returns:
        List of function call info dictionaries
    """
    function_calls = []

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Handle method calls like requests.get
                    if isinstance(node.func.value, ast.Name):
                        func_name = f"{node.func.value.id}.{node.func.attr}"

                # Extract arguments
                args = []
                for arg in node.args:
                    if isinstance(arg, ast.Constant):
                        args.append(arg.value)

                function_calls.append({
                    'name': func_name,
                    'line': node.lineno,
                    'args': args
                })
    except SyntaxError:
        pass

    return function_calls


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get metadata for a file.

    Args:
        file_path: Path to file

    Returns:
        Dictionary of file metadata
    """
    try:
        stat = os.stat(file_path)
        total_lines, code_lines = count_lines(file_path)

        return {
            'path': file_path,
            'size_bytes': stat.st_size,
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': total_lines - code_lines,
            'extension': Path(file_path).suffix
        }
    except Exception as e:
        return {
            'path': file_path,
            'error': str(e)
        }


def estimate_tokens_from_text(text: str, chars_per_token: int = 4) -> int:
    """
    Estimate token count from text using heuristic.

    Args:
        text: Text to estimate
        chars_per_token: Average characters per token

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return max(1, len(text) // chars_per_token)


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    @property
    def seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration or 0.0
