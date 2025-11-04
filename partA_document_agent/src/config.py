"""
Configuration Loader and Validator

Loads and validates configuration from YAML files.
Provides type-safe access to configuration values.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int
    backoff_seconds: float
    max_backoff_seconds: float
    jitter: float


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int
    failure_window: int
    reset_timeout: int


@dataclass
class ExternalAPIConfig:
    """External API configuration."""
    endpoint: str
    timeout_sec: int
    retry: RetryConfig
    circuit_breaker: CircuitBreakerConfig


@dataclass
class RedactionConfig:
    """Redaction configuration."""
    context_chars: int
    redacted_char: str


@dataclass
class DetectorConfig:
    """Red-flag detector configuration."""
    enabled: Dict[str, bool]
    email_patterns: list
    phone_patterns: list
    keywords: list
    credit_card_pattern: str
    iban_patterns: list
    api_key_patterns: list
    obfuscated_patterns: list
    min_confidence_threshold: str
    redaction: RedactionConfig


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    file_enabled: bool
    format: str
    file_rotation: bool
    max_file_size_mb: int
    backup_count: int
    console_enabled: bool
    verbose: bool


@dataclass
class HumanApprovalConfig:
    """Human approval configuration."""
    mode: str
    timeout_sec: int
    auto_approve_on_timeout: bool


@dataclass
class TokenEstimatorConfig:
    """Token estimator configuration."""
    enabled: bool
    method: str
    chars_per_token: int
    uncertainty_percentage: int


@dataclass
class VCConfig:
    """Value Credit configuration."""
    enabled: bool
    include_performance_metrics: bool
    include_confidence: bool
    log_to_console: bool
    export_format: str


@dataclass
class GeneralConfig:
    """General configuration."""
    output_dir: str
    temp_dir: str
    max_file_size_mb: int
    supported_extensions: list
    url_timeout_sec: int
    default_human_approval: str


@dataclass
class AppConfig:
    """Complete application configuration."""
    human_approval: HumanApprovalConfig
    external_api: ExternalAPIConfig
    detector: DetectorConfig
    logging: LoggingConfig
    vc: VCConfig
    token_estimator: TokenEstimatorConfig
    general: GeneralConfig


class ConfigLoader:
    """Loads and validates configuration from YAML files."""

    @staticmethod
    def load(config_path: Optional[str] = None) -> AppConfig:
        """
        Load configuration from file or use defaults.

        Args:
            config_path: Path to config file. If None, uses default config.yaml.

        Returns:
            Validated AppConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if config_path is None:
            # Use default config.yaml in same directory as this module
            config_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "config.yaml"
            )

        config_path = os.path.abspath(config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return ConfigLoader._validate_and_build(config_data, config_path)

    @staticmethod
    def _validate_and_build(data: Dict[str, Any], config_path: str) -> AppConfig:
        """
        Validate configuration data and build AppConfig object.

        Args:
            data: Raw configuration dictionary
            config_path: Path to config file for error messages

        Returns:
            Validated AppConfig object

        Raises:
            ValueError: If validation fails
        """
        # Validate top-level sections
        required_sections = [
            "human_approval",
            "external_api",
            "detector",
            "logging",
            "vc",
            "token_estimator",
            "general"
        ]

        for section in required_sections:
            if section not in data:
                raise ValueError(
                    f"Missing required configuration section '{section}' in {config_path}"
                )

        # Build configuration objects
        config = AppConfig(
            human_approval=ConfigLoader._build_human_approval_config(
                data["human_approval"]
            ),
            external_api=ConfigLoader._build_external_api_config(
                data["external_api"]
            ),
            detector=ConfigLoader._build_detector_config(
                data["detector"]
            ),
            logging=ConfigLoader._build_logging_config(
                data["logging"]
            ),
            vc=ConfigLoader._build_vc_config(
                data["vc"]
            ),
            token_estimator=ConfigLoader._build_token_estimator_config(
                data["token_estimator"]
            ),
            general=ConfigLoader._build_general_config(
                data["general"]
            )
        )

        return config

    @staticmethod
    def _build_human_approval_config(data: Dict[str, Any]) -> HumanApprovalConfig:
        """Build human approval configuration."""
        return HumanApprovalConfig(
            mode=ConfigLoader._get_str(data, "human_approval", "mode", "cli"),
            timeout_sec=ConfigLoader._get_int(data, "human_approval", "timeout_sec", 300),
            auto_approve_on_timeout=ConfigLoader._get_bool(
                data, "human_approval", "auto_approve_on_timeout", True
            )
        )

    @staticmethod
    def _build_external_api_config(data: Dict[str, Any]) -> ExternalAPIConfig:
        """Build external API configuration."""
        retry_data = data.get("retry", {})
        cb_data = data.get("circuit_breaker", {})

        return ExternalAPIConfig(
            endpoint=ConfigLoader._get_str(data, "external_api", "endpoint",
                                          "https://httpbin.org/post"),
            timeout_sec=ConfigLoader._get_int(data, "external_api", "timeout_sec", 10),
            retry=RetryConfig(
                max_attempts=ConfigLoader._get_int(
                    retry_data, "retry", "max_attempts", 3
                ),
                backoff_seconds=ConfigLoader._get_float(
                    retry_data, "retry", "backoff_seconds", 2.0
                ),
                max_backoff_seconds=ConfigLoader._get_float(
                    retry_data, "retry", "max_backoff_seconds", 60.0
                ),
                jitter=ConfigLoader._get_float(
                    retry_data, "retry", "jitter", 0.1
                )
            ),
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=ConfigLoader._get_int(
                    cb_data, "circuit_breaker", "failure_threshold", 3
                ),
                failure_window=ConfigLoader._get_int(
                    cb_data, "circuit_breaker", "failure_window", 60
                ),
                reset_timeout=ConfigLoader._get_int(
                    cb_data, "circuit_breaker", "reset_timeout", 30
                )
            )
        )

    @staticmethod
    def _build_detector_config(data: Dict[str, Any]) -> DetectorConfig:
        """Build detector configuration."""
        enabled_data = data.get("enabled", {})
        redaction_data = data.get("redaction", {})

        return DetectorConfig(
            enabled={
                "emails": ConfigLoader._get_bool(enabled_data, "enabled", "emails", True),
                "phones": ConfigLoader._get_bool(enabled_data, "enabled", "phones", True),
                "keywords": ConfigLoader._get_bool(enabled_data, "enabled", "keywords", True),
                "credit_cards": ConfigLoader._get_bool(
                    enabled_data, "enabled", "credit_cards", True
                ),
                "ibans": ConfigLoader._get_bool(enabled_data, "enabled", "ibans", True),
                "api_keys": ConfigLoader._get_bool(enabled_data, "enabled", "api_keys", True),
                "obfuscated": ConfigLoader._get_bool(enabled_data, "enabled", "obfuscated", True),
            },
            email_patterns=data.get("email_patterns", []),
            phone_patterns=data.get("phone_patterns", []),
            keywords=data.get("keywords", []),
            credit_card_pattern=data.get("credit_card_pattern", ""),
            iban_patterns=data.get("iban_patterns", []),
            api_key_patterns=data.get("api_key_patterns", []),
            obfuscated_patterns=data.get("obfuscated_patterns", []),
            min_confidence_threshold=data.get(
                "min_confidence_threshold", "low"
            ).lower(),
            redaction=RedactionConfig(
                context_chars=ConfigLoader._get_int(
                    redaction_data, "redaction", "context_chars", 15
                ),
                redacted_char=ConfigLoader._get_str(
                    redaction_data, "redaction", "redacted_char", "*"
                )
            )
        )

    @staticmethod
    def _build_logging_config(data: Dict[str, Any]) -> LoggingConfig:
        """Build logging configuration."""
        return LoggingConfig(
            level=ConfigLoader._get_str(data, "logging", "level", "INFO").upper(),
            file_enabled=ConfigLoader._get_bool(data, "logging", "file_enabled", True),
            format=ConfigLoader._get_str(data, "logging", "format", "json"),
            file_rotation=ConfigLoader._get_bool(data, "logging", "file_rotation", False),
            max_file_size_mb=ConfigLoader._get_int(
                data, "logging", "max_file_size_mb", 10
            ),
            backup_count=ConfigLoader._get_int(data, "logging", "backup_count", 5),
            console_enabled=ConfigLoader._get_bool(
                data, "logging", "console_enabled", True
            ),
            verbose=ConfigLoader._get_bool(data, "logging", "verbose", False)
        )

    @staticmethod
    def _build_vc_config(data: Dict[str, Any]) -> VCConfig:
        """Build VC configuration."""
        return VCConfig(
            enabled=ConfigLoader._get_bool(data, "vc", "enabled", True),
            include_performance_metrics=ConfigLoader._get_bool(
                data, "vc", "include_performance_metrics", True
            ),
            include_confidence=ConfigLoader._get_bool(
                data, "vc", "include_confidence", True
            ),
            log_to_console=ConfigLoader._get_bool(data, "vc", "log_to_console", True),
            export_format=ConfigLoader._get_str(data, "vc", "export_format", "json")
        )

    @staticmethod
    def _build_token_estimator_config(data: Dict[str, Any]) -> TokenEstimatorConfig:
        """Build token estimator configuration."""
        return TokenEstimatorConfig(
            enabled=ConfigLoader._get_bool(
                data, "token_estimator", "enabled", True
            ),
            method=ConfigLoader._get_str(
                data, "token_estimator", "method", "heuristic"
            ),
            chars_per_token=ConfigLoader._get_int(
                data, "token_estimator", "chars_per_token", 4
            ),
            uncertainty_percentage=ConfigLoader._get_int(
                data, "token_estimator", "uncertainty_percentage", 10
            )
        )

    @staticmethod
    def _build_general_config(data: Dict[str, Any]) -> GeneralConfig:
        """Build general configuration."""
        return GeneralConfig(
            output_dir=ConfigLoader._get_str(data, "general", "output_dir", "output"),
            temp_dir=ConfigLoader._get_str(data, "general", "temp_dir", "/tmp"),
            max_file_size_mb=ConfigLoader._get_int(
                data, "general", "max_file_size_mb", 50
            ),
            supported_extensions=data.get("supported_extensions", [".pdf"]),
            url_timeout_sec=ConfigLoader._get_int(
                data, "general", "url_timeout_sec", 30
            ),
            default_human_approval=ConfigLoader._get_str(
                data, "general", "default_human_approval", "cli"
            )
        )

    @staticmethod
    def _get_str(data: Dict, section: str, key: str, default: str) -> str:
        """Get string value with default."""
        return data.get(key, default)

    @staticmethod
    def _get_int(data: Dict, section: str, key: str, default: int) -> int:
        """Get integer value with default."""
        return data.get(key, default)

    @staticmethod
    def _get_float(data: Dict, section: str, key: str, default: float) -> float:
        """Get float value with default."""
        return data.get(key, default)

    @staticmethod
    def _get_bool(data: Dict, section: str, key: str, default: bool) -> bool:
        """Get boolean value with default."""
        return data.get(key, default)


# Global config instance
_global_config: Optional[AppConfig] = None


def get_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Get the global configuration instance.

    Args:
        config_path: Optional path to config file

    Returns:
        AppConfig instance
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader.load(config_path)

    return _global_config


def reload_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Reload configuration from file.

    Args:
        config_path: Optional path to config file

    Returns:
        New AppConfig instance
    """
    global _global_config
    _global_config = ConfigLoader.load(config_path)
    return _global_config
