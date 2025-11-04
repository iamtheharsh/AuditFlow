"""
Report Builder Module

Generates human-readable and machine-readable audit reports.
Supports JSON and text formats with detailed findings and recommendations.
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

import utils


class ReportBuilder:
    """Builds audit reports in multiple formats."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize report builder.

        Args:
            output_dir: Output directory
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def build_reports(
        self,
        scan_results: Dict[str, Any],
        injection_results: Optional[Dict[str, Any]] = None,
        logger: Any = None
    ) -> Dict[str, str]:
        """
        Build all report formats.

        Args:
            scan_results: Results from code scanner
            injection_results: Results from VC injection
            logger: Audit logger

        Returns:
            Dictionary of report paths
        """
        report_paths = {}

        # Build JSON report
        json_path = self._build_json_report(scan_results, injection_results, logger)
        report_paths["json"] = json_path

        # Build text report
        text_path = self._build_text_report(scan_results, injection_results, logger)
        report_paths["text"] = text_path

        return report_paths

    def _build_json_report(
        self,
        scan_results: Dict[str, Any],
        injection_results: Optional[Dict[str, Any]],
        logger: Any
    ) -> str:
        """
        Build JSON report.

        Args:
            scan_results: Scan results
            injection_results: Injection results
            logger: Audit logger

        Returns:
            Path to JSON report
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        report_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Prepare report data
        report = {
            "report_metadata": {
                "report_id": report_id,
                "timestamp": timestamp,
                "version": "3.0",
                "tool": "Meta Auditor - Value Credits Agent"
            },
            "summary": self._build_summary(scan_results, injection_results),
            "findings": self._build_findings(scan_results),
            "recommendations": self._build_recommendations(scan_results, injection_results),
            "file_structure": scan_results.get("metadata", {}),
            "execution_details": {
                "target_directory": scan_results.get("target_dir"),
                "language": scan_results.get("language"),
                "scan_duration_seconds": scan_results.get("statistics", {}).get("scan_duration"),
                "files_scanned": scan_results.get("files_scanned")
            }
        }

        # Write report
        report_path = os.path.join(self.output_dir, f"{report_id}_audit_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Log report generation
        if logger:
            logger.log_report_generation(
                report_path=report_path,
                report_type="JSON",
                findings_count=len(report["findings"])
            )
            logger.log_vc_event(
                event_name="audit_report_generated",
                count=1,
                metadata={
                    "format": "json",
                    "findings_count": len(report["findings"]),
                    "report_id": report_id
                }
            )

        return report_path

    def _build_text_report(
        self,
        scan_results: Dict[str, Any],
        injection_results: Optional[Dict[str, Any]],
        logger: Any
    ) -> str:
        """
        Build human-readable text report.

        Args:
            scan_results: Scan results
            injection_results: Injection results
            logger: Audit logger

        Returns:
            Path to text report
        """
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        report_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        lines = []
        lines.append("=" * 80)
        lines.append("META AUDITOR - CODEBASE SCAN REPORT")
        lines.append("=" * 80)
        lines.append(f"Report ID: {report_id}")
        lines.append(f"Timestamp: {timestamp}")
        lines.append(f"Tool: Meta Auditor v3.0")
        lines.append("")

        # Summary
        lines.append("-" * 80)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        summary = self._build_summary(scan_results, injection_results)
        lines.append(f"Files Scanned: {summary['files_scanned']}")
        lines.append(f"Lines of Code: {summary['code_lines']}")
        lines.append("")
        lines.append("External API Calls:")
        lines.append(f"  Total: {summary['external_api_calls']['total']}")
        lines.append(f"  External: {summary['external_api_calls']['external']}")
        lines.append(f"  Internal: {summary['external_api_calls']['internal']}")
        lines.append("")
        lines.append("LLM Usage:")
        lines.append(f"  Total detections: {summary['llm_usage']['total']}")
        if summary['llm_usage']['total_estimated_tokens'] > 0:
            lines.append(f"  Estimated tokens: {summary['llm_usage']['total_estimated_tokens']}")
        lines.append("")
        lines.append("Cloud/Compute Libraries:")
        if summary['cloud_usage']['cloud_services']:
            lines.append(f"  Cloud services: {', '.join(summary['cloud_usage']['cloud_services'])}")
        if summary['cloud_usage']['compute_frameworks']:
            lines.append(f"  Compute frameworks: {', '.join(summary['cloud_usage']['compute_frameworks'])}")
        lines.append("")

        # Findings
        lines.append("-" * 80)
        lines.append("FINDINGS")
        lines.append("-" * 80)
        findings = self._build_findings(scan_results)

        if not findings:
            lines.append("No significant findings detected.")
        else:
            for i, finding in enumerate(findings, 1):
                lines.append(f"\n{i}. {finding['type'].upper().replace('_', ' ')}")
                lines.append(f"   File: {finding['file']}")
                lines.append(f"   Line: {finding['line']}")
                lines.append(f"   Pattern: {finding['pattern']}")

                if finding.get('endpoint'):
                    lines.append(f"   Endpoint: {finding['endpoint']}")
                if finding.get('model'):
                    lines.append(f"   Model: {finding['model']}")
                if finding.get('library'):
                    lines.append(f"   Library: {finding['library']}")
                if finding.get('estimated_tokens'):
                    lines.append(f"   Estimated tokens: {finding['estimated_tokens']}")

        # Recommendations
        lines.append("")
        lines.append("-" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        recommendations = self._build_recommendations(scan_results, injection_results)

        if not recommendations:
            lines.append("No recommendations at this time.")
        else:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"\n{i}. {rec['type'].upper()}")
                lines.append(f"   File: {rec['file']}")
                lines.append(f"   Line: {rec['line']}")
                lines.append(f"   Action: {rec['action']}")

        # VC Metrics
        lines.append("")
        lines.append("-" * 80)
        lines.append("SUGGESTED VALUE METRICS")
        lines.append("-" * 80)
        suggested_metrics = self._get_suggested_metrics(scan_results)
        for metric in suggested_metrics:
            lines.append(f"  - {metric}")

        # Injections
        if injection_results and injection_results.get("summary", {}).get("total_injections", 0) > 0:
            lines.append("")
            lines.append("-" * 80)
            lines.append("VC INJECTIONS")
            lines.append("-" * 80)
            summary = injection_results["summary"]
            lines.append(f"Files patched: {summary['files_patched']}")
            lines.append(f"Total injections: {summary['total_injections']}")
            lines.append(f"Patched directory: {summary['patched_dir']}")

        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        # Write report
        report_path = os.path.join(self.output_dir, f"{report_id}_audit_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        # Log report generation
        if logger:
            logger.log_report_generation(
                report_path=report_path,
                report_type="text",
                findings_count=len(findings)
            )

        return report_path

    def _build_summary(
        self,
        scan_results: Dict[str, Any],
        injection_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build summary section."""
        stats = scan_results.get("statistics", {})

        return {
            "files_scanned": scan_results.get("files_scanned", 0),
            "code_lines": scan_results.get("metadata", {}).get("total_code_lines", 0),
            "external_api_calls": stats.get("http_apis", {}),
            "llm_usage": stats.get("llm_usage", {}),
            "cloud_usage": stats.get("cloud_usage", {}),
            "injections_made": injection_results.get("summary", {}).get("total_injections", 0) if injection_results else 0
        }

    def _build_findings(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build findings section."""
        return scan_results.get("detections", [])

    def _build_recommendations(
        self,
        scan_results: Dict[str, Any],
        injection_results: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build recommendations section."""
        recommendations = []
        detections = scan_results.get("detections", [])

        for detection in detections:
            vm_label = detection.get("vm_label", "unknown_metric")
            file_path = detection.get("file", "")
            line = detection.get("line", 0)

            if detection.get("type") == "external_api":
                action = f"Add @vc_tracker('{vm_label}') decorator to track external API calls"
            elif detection.get("type") == "llm_usage":
                action = f"Add @vc_tracker('{vm_label}') with token estimation for LLM usage"
            elif detection.get("type") == "cloud_library":
                action = f"Add @vc_tracker('{vm_label}') decorator to track cloud/compute usage"
            else:
                action = f"Add @vc_tracker('{vm_label}') decorator"

            recommendations.append({
                "type": detection.get("type", "unknown"),
                "file": file_path,
                "line": line,
                "action": action,
                "vm_label": vm_label
            })

        return recommendations

    def _get_suggested_metrics(self, scan_results: Dict[str, Any]) -> List[str]:
        """Get list of suggested VC metrics."""
        metrics = set()
        detections = scan_results.get("detections", [])

        for detection in detections:
            vm_label = detection.get("vm_label")
            if vm_label:
                metrics.add(vm_label)

        return sorted(list(metrics))


def build_audit_reports(
    scan_results: Dict[str, Any],
    output_dir: str = "output",
    injection_results: Optional[Dict[str, Any]] = None,
    logger: Any = None
) -> Dict[str, str]:
    """
    Build audit reports.

    Args:
        scan_results: Scan results
        output_dir: Output directory
        injection_results: Injection results
        logger: Audit logger

    Returns:
        Dictionary of report paths
    """
    builder = ReportBuilder(output_dir)
    return builder.build_reports(scan_results, injection_results, logger)
