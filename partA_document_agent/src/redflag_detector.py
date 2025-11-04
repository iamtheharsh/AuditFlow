"""
Red-Flag Detection Module

Scans text for sensitive information patterns including:
- Email addresses
- Phone numbers
- Sensitive keywords (password, ssn, confidential, api_key, token)

Provides detailed findings with line numbers and context snippets.
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class RedFlag:
    """Represents a detected red flag."""
    type: str
    value: str
    line_number: int
    context: str


def detect_red_flags(text: str, job_id: str) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Scan text for sensitive information patterns.

    Args:
        text: Text to scan
        job_id: Job identifier for logging

    Returns:
        Tuple of (flags_list, requires_human)
    """
    print(f"[INFO] Scanning text for red flags...")

    lines = text.split("\n")
    flags: List[RedFlag] = []

    # Detect emails
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    _find_pattern_in_text(lines, email_pattern, "email", flags)

    # Detect phone numbers (US format)
    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    _find_pattern_in_text(lines, phone_pattern, "phone", flags)

    # Detect sensitive keywords
    keywords = ["password", "ssn", "confidential", "api_key", "api key", "token", "secret"]
    for keyword in keywords:
        keyword_pattern = re.escape(keyword)
        _find_pattern_in_text(lines, keyword_pattern, "keyword", flags, case_sensitive=False)

    # Convert to dictionaries for JSON serialization
    flags_dict = []
    for flag in flags:
        flags_dict.append({
            "type": flag.type,
            "value": flag.value,
            "line_number": flag.line_number,
            "context": flag.context
        })

    # Determine if human approval is required
    requires_human = len(flags) > 0

    # Log to VC
    print(f"[INFO] Found {len(flags)} red flags")
    if flags:
        print(f"[WARN] Red flags detected:")
        for flag in flags:
            print(f"  - {flag.type}: {flag.value} (line {flag.line_number})")

    # Return results
    return flags_dict, requires_human


def _find_pattern_in_text(
    lines: List[str],
    pattern: str,
    flag_type: str,
    flags: List[RedFlag],
    case_sensitive: bool = True
) -> None:
    """
    Find a regex pattern in text lines and add to flags list.

    Args:
        lines: List of text lines
        pattern: Regex pattern to match
        flag_type: Type of flag (email, phone, keyword)
        flags: List to append findings to
        case_sensitive: Whether pattern is case-sensitive
    """
    regex_flags = 0 if case_sensitive else re.IGNORECASE

    for line_num, line in enumerate(lines, start=1):
        matches = re.finditer(pattern, line, regex_flags)

        for match in matches:
            # Get the matched value
            value = match.group(0)

            # Get context (snippet around the match)
            start = max(0, match.start() - 20)
            end = min(len(line), match.end() + 20)
            context = line[start:end].strip()

            flags.append(RedFlag(
                type=flag_type,
                value=value,
                line_number=line_num,
                context=context
            ))


def get_detection_summary(flags: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get a summary of detected flags by type.

    Args:
        flags: List of flag dictionaries

    Returns:
        Dictionary with counts by type
    """
    summary = {}
    for flag in flags:
        flag_type = flag["type"]
        summary[flag_type] = summary.get(flag_type, 0) + 1

    return summary
