"""
Red-Flag Detection Module (Phase 2 Enhanced)

Scans text for sensitive information patterns including:
- Email addresses
- Phone numbers
- Sensitive keywords
- Credit card numbers
- IBAN/bank account numbers
- API keys and tokens
- Obfuscated PII (spaced/masked numbers)

Provides detailed findings with confidence scores, line numbers, and context snippets.
Supports configurable detection rules and redaction for logging.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import config


class ConfidenceLevel(Enum):
    """Confidence level for detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RedFlag:
    """Represents a detected red flag with confidence."""
    type: str
    value: str
    line_number: int
    context: str
    confidence: ConfidenceLevel
    pattern: str
    start_pos: int
    end_pos: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "value": self.value,
            "line_number": self.line_number,
            "context": self.context,
            "confidence": self.confidence.value,
            "pattern": self.pattern,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos
        }


def detect_red_flags(
    text: str,
    job_id: str,
    config_override: Optional[config.DetectorConfig] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Scan text for sensitive information patterns (Phase 2 enhanced).

    Args:
        text: Text to scan
        job_id: Job identifier for logging
        config_override: Optional detector configuration (uses global config if None)

    Returns:
        Tuple of (flags_list, requires_human)
    """
    print(f"[INFO] Scanning text for red flags...")

    # Get configuration
    detector_config = config_override or config.get_config().detector

    # Check if detection is enabled
    if not any(detector_config.enabled.values()):
        print(f"[WARN] All detectors are disabled")
        return [], False

    lines = text.split("\n")
    flags: List[RedFlag] = []

    # Detect based on enabled detectors
    if detector_config.enabled.get("emails", True):
        _detect_emails(lines, detector_config, flags)

    if detector_config.enabled.get("phones", True):
        _detect_phones(lines, detector_config, flags)

    if detector_config.enabled.get("keywords", True):
        _detect_keywords(lines, detector_config, flags)

    if detector_config.enabled.get("credit_cards", True):
        _detect_credit_cards(lines, detector_config, flags)

    if detector_config.enabled.get("ibans", True):
        _detect_ibans(lines, detector_config, flags)

    if detector_config.enabled.get("api_keys", True):
        _detect_api_keys(lines, detector_config, flags)

    if detector_config.enabled.get("obfuscated", True):
        _detect_obfuscated(lines, detector_config, flags)

    # Sort flags by type and position
    flags.sort(key=lambda f: (f.type, f.line_number, f.start_pos))

    # Convert to dictionaries for JSON serialization
    flags_dict = [flag.to_dict() for flag in flags]

    # Filter by confidence threshold
    min_confidence = detector_config.min_confidence_threshold
    flags_dict = _filter_by_confidence(flags_dict, min_confidence)

    # Determine if human approval is required
    requires_human = len(flags_dict) > 0

    # Log to console (with redaction)
    print(f"[INFO] Found {len(flags_dict)} red flags")
    if flags_dict:
        print(f"[WARN] Red flags detected:")
        for flag in flags_dict[:5]:  # Show first 5
            redacted_value = _redact_for_logs(flag["value"], detector_config.redaction)
            print(f"  - {flag['type']} ({flag['confidence']}): {redacted_value} "
                  f"(line {flag['line_number']})")
        if len(flags_dict) > 5:
            print(f"  ... and {len(flags_dict) - 5} more")

    # Return results
    return flags_dict, requires_human


def _detect_emails(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect email addresses."""
    for pattern in config.email_patterns:
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                flags.append(RedFlag(
                    type="email",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=ConfidenceLevel.HIGH,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _detect_phones(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect phone numbers."""
    for pattern in config.phone_patterns:
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                flags.append(RedFlag(
                    type="phone",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=ConfidenceLevel.HIGH,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _detect_keywords(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect sensitive keywords."""
    for keyword in config.keywords:
        pattern = re.escape(keyword)
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                # Some keywords have medium confidence (more prone to false positives)
                confidence = ConfidenceLevel.HIGH if len(keyword) > 4 else ConfidenceLevel.MEDIUM

                flags.append(RedFlag(
                    type="keyword",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=confidence,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _detect_credit_cards(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect credit card numbers."""
    pattern = config.credit_card_pattern
    for line_num, line in enumerate(lines, start=1):
        matches = re.finditer(pattern, line)
        for match in matches:
            value = match.group(0)
            context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

            # Quick Luhn-like check (not full validation)
            is_likely_cc = _looks_like_credit_card(value)

            flags.append(RedFlag(
                type="credit_card",
                value=value,
                line_number=line_num,
                context=context,
                confidence=ConfidenceLevel.MEDIUM if is_likely_cc else ConfidenceLevel.LOW,
                pattern=pattern,
                start_pos=match.start(),
                end_pos=match.end()
            ))


def _detect_ibans(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect IBAN/bank account numbers."""
    for pattern in config.iban_patterns:
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                flags.append(RedFlag(
                    type="iban",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=ConfidenceLevel.MEDIUM,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _detect_api_keys(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect API keys and tokens."""
    for pattern in config.api_key_patterns:
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                # Determine confidence based on pattern specificity
                confidence = ConfidenceLevel.HIGH
                if "sk-" in value or "ghp_" in value:
                    confidence = ConfidenceLevel.HIGH
                elif len(value) < 32:
                    confidence = ConfidenceLevel.LOW

                flags.append(RedFlag(
                    type="api_key",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=confidence,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _detect_obfuscated(
    lines: List[str],
    config: config.DetectorConfig,
    flags: List[RedFlag]
) -> None:
    """Detect obfuscated PII (spaced/masked numbers)."""
    for pattern in config.obfuscated_patterns:
        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(0)
                context = _get_context(line, match.start(), match.end(), config.redaction.context_chars)

                flags.append(RedFlag(
                    type="obfuscated",
                    value=value,
                    line_number=line_num,
                    context=context,
                    confidence=ConfidenceLevel.MEDIUM,
                    pattern=pattern,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))


def _get_context(
    line: str,
    start: int,
    end: int,
    context_chars: int
) -> str:
    """
    Get context snippet around a match.

    Args:
        line: The line containing the match
        start: Start position of match
        end: End position of match
        context_chars: Number of characters to include before/after

    Returns:
        Context snippet
    """
    context_start = max(0, start - context_chars)
    context_end = min(len(line), end + context_chars)
    context = line[context_start:context_end].strip()
    return context


def _redact_for_logs(value: str, redaction_config: config.RedactionConfig) -> str:
    """
    Redact sensitive value for logging.

    Args:
        value: The sensitive value
        redaction_config: Redaction configuration

    Returns:
        Redacted value safe for logging
    """
    if len(value) <= 4:
        return value[0] + redaction_config.redacted_char * (len(value) - 1)
    else:
        return value[:4] + redaction_config.redacted_char * (len(value) - 4)


def _looks_like_credit_card(value: str) -> bool:
    """
    Quick heuristic to check if a value looks like a credit card.
    Performs basic checks without full Luhn validation.

    Args:
        value: Value to check

    Returns:
        True if likely a credit card
    """
    # Remove spaces and dashes
    digits_only = re.sub(r'[-\s]', '', value)

    # Check if all digits
    if not digits_only.isdigit():
        return False

    # Check length (13-19 digits typical for credit cards)
    if not (13 <= len(digits_only) <= 19):
        return False

    # Check for common patterns (Visa, MasterCard, Amex, etc.)
    # This is a very basic check - real validation would use Luhn algorithm
    first_digit = digits_only[0]
    if first_digit in ['3', '4', '5', '6']:
        return True

    return False


def _filter_by_confidence(
    flags: List[Dict[str, Any]],
    min_confidence: str
) -> List[Dict[str, Any]]:
    """
    Filter flags by minimum confidence level.

    Args:
        flags: List of flag dictionaries
        min_confidence: Minimum confidence level (low, medium, high)

    Returns:
        Filtered list
    """
    confidence_order = {
        "low": 0,
        "medium": 1,
        "high": 2
    }

    min_level = confidence_order.get(min_confidence, 0)

    filtered = []
    for flag in flags:
        flag_level = confidence_order.get(flag.get("confidence", "low"), 0)
        if flag_level >= min_level:
            filtered.append(flag)

    return filtered


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
        flag_type = flag.get("type", "unknown")
        summary[flag_type] = summary.get(flag_type, 0) + 1

    return summary


def get_confidence_summary(flags: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Get a summary of detected flags by type and confidence.

    Args:
        flags: List of flag dictionaries

    Returns:
        Dictionary with counts by type and confidence
    """
    summary = {}
    for flag in flags:
        flag_type = flag.get("type", "unknown")
        confidence = flag.get("confidence", "low")

        if flag_type not in summary:
            summary[flag_type] = {}

        summary[flag_type][confidence] = summary[flag_type].get(confidence, 0) + 1

    return summary
