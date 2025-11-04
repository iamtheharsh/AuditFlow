"""
Token Estimator Module (Phase 2)

Estimates token counts for LLM usage.
Heuristic-based estimation (chars/token ratio) with uncertainty ranges.
No actual API calls - instrumentation only.

This module prepares for future LLM integration by providing:
- Token estimation for text
- Prompt component token estimation with ranges
- Cost projection (when model rates are available)
"""

import re
from typing import List, Dict, Any, Optional
import math

import config


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using heuristic method.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count (minimum 1)
    """
    if not text:
        return 0

    # Get configuration
    estimator_config = config.get_config().token_estimator

    # Heuristic: chars / chars_per_token
    chars_per_token = estimator_config.chars_per_token
    estimated = max(1, round(len(text) / chars_per_token))

    return estimated


def estimate_tokens_for_prompt(prompt_parts: List[str]) -> Dict[str, int]:
    """
    Estimate tokens for a prompt composed of multiple parts.

    Args:
        prompt_parts: List of prompt components

    Returns:
        Dictionary with min, likely, and max estimates
    """
    if not prompt_parts:
        return {
            "min": 0,
            "likely": 0,
            "max": 0,
            "parts": []
        }

    # Get configuration
    estimator_config = config.get_config().token_estimator
    uncertainty_pct = estimator_config.uncertainty_percentage / 100.0

    # Estimate for each part
    part_estimates = []
    for part in prompt_parts:
        estimated = estimate_tokens(part)
        part_estimates.append(estimated)

    # Calculate total
    total = sum(part_estimates)

    # Calculate range with uncertainty
    uncertainty = int(total * uncertainty_pct)
    min_estimate = max(0, total - uncertainty)
    max_estimate = total + uncertainty

    return {
        "min": min_estimate,
        "likely": total,
        "max": max_estimate,
        "parts": part_estimates,
        "total_parts": len(prompt_parts)
    }


def estimate_tokens_with_context(
    text: str,
    context: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Estimate tokens with additional context.

    Args:
        text: Text to estimate
        context: Optional context (system prompt, user prompt, etc.)

    Returns:
        Detailed token estimation
    """
    # Base estimation
    base_estimate = estimate_tokens(text)

    # Add context if provided
    context_estimates = {}
    total_with_context = base_estimate

    if context:
        for ctx_name, ctx_text in context.items():
            ctx_estimate = estimate_tokens(ctx_text)
            context_estimates[ctx_name] = ctx_estimate
            total_with_context += ctx_estimate

    # Get configuration for uncertainty
    estimator_config = config.get_config().token_estimator
    uncertainty_pct = estimator_config.uncertainty_percentage / 100.0
    uncertainty = int(total_with_context * uncertainty_pct)

    return {
        "base_text_tokens": base_estimate,
        "context_tokens": context_estimates,
        "total_tokens": {
            "min": max(0, total_with_context - uncertainty),
            "likely": total_with_context,
            "max": total_with_context + uncertainty
        },
        "method": "heuristic",
        "chars_per_token": estimator_config.chars_per_token,
        "uncertainty_percentage": estimator_config.uncertainty_percentage
    }


def estimate_llm_cost(
    token_count: int,
    model_name: str = "gpt-3.5-turbo",
    operation: str = "completion"
) -> Optional[Dict[str, Any]]:
    """
    Estimate cost for LLM usage (when model rates are available).

    Args:
        token_count: Number of tokens
        model_name: Model name
        operation: Operation type (completion, chat, embedding)

    Returns:
        Cost estimation or None if rates not available
    """
    # This is a placeholder for future cost estimation
    # In a real implementation, this would use a pricing table

    # Mock pricing for demonstration (prices per 1K tokens)
    mock_pricing = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015}
    }

    if model_name not in mock_pricing:
        return None

    # Assume 50/50 split between input and output
    input_tokens = token_count // 2
    output_tokens = token_count - input_tokens

    rates = mock_pricing[model_name]
    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model_name,
        "operation": operation,
        "token_count": token_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "costs": {
            "input": round(input_cost, 6),
            "output": round(output_cost, 6),
            "total": round(total_cost, 6)
        },
        "currency": "USD"
    }


def calculate_token_efficiency(
    actual_tokens: int,
    character_count: int
) -> Dict[str, float]:
    """
    Calculate tokenization efficiency metrics.

    Args:
        actual_tokens: Actual token count (if available)
        character_count: Character count

    Returns:
        Efficiency metrics
    """
    if actual_tokens <= 0:
        return {"chars_per_token": float(character_count)}

    chars_per_token = character_count / actual_tokens

    return {
        "chars_per_token": round(chars_per_token, 2),
        "tokens_per_char": round(actual_tokens / character_count, 4) if character_count > 0 else 0
    }


def detect_potential_token_bloat(text: str) -> Dict[str, Any]:
    """
    Detect patterns that might cause high token usage.

    Args:
        text: Text to analyze

    Returns:
        Analysis of potential token bloat
    """
    warnings = []

    # Check for repetitive patterns
    if re.search(r'(.)\1{10,}', text):
        warnings.append("Contains repetitive characters")

    # Check for long words (might be token-inefficient)
    long_words = re.findall(r'\b\w{20,}\b', text)
    if long_words:
        warnings.append(f"Contains {len(long_words)} very long words")

    # Check for very long lines
    long_lines = [line for line in text.split('\n') if len(line) > 500]
    if long_lines:
        warnings.append(f"Contains {len(long_lines)} very long lines")

    # Check for JSON/structured data (usually token-heavy)
    if text.strip().startswith(('{', '[')):
        warnings.append("Contains structured data (JSON-like)")

    # Check for code blocks
    code_blocks = text.count('```')
    if code_blocks > 0:
        warnings.append(f"Contains {code_blocks // 2} code blocks")

    estimated = estimate_tokens(text)

    return {
        "estimated_tokens": estimated,
        "warnings": warnings,
        "has_potential_bloat": len(warnings) > 0,
        "severity": "high" if len(warnings) > 2 else "medium" if len(warnings) > 0 else "low"
    }
