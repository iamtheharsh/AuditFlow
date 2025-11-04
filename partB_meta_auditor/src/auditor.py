#!/usr/bin/env python3
"""
Meta Auditor - Main Entry Point

Automated code auditing tool that detects:
- External API calls
- LLM/AI model usage
- Cloud/compute library usage

Generates comprehensive audit reports with optional VC injection.
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.code_scanner import scan_codebase
from src.injector import inject_vc_decorators
from src.report_builder import build_audit_reports
from src.logger_audit import get_audit_logger
import utils


def main():
    """Main entry point for Meta Auditor."""
    args = parse_arguments()

    # Setup
    target_path = args.target
    output_dir = args.output_dir
    language = args.language
    inject_mode = args.inject
    job_id = args.job_id or f"AUDIT-{utils.safe_filename(os.path.basename(target_path))}"

    print("=" * 80)
    print("Meta Auditor - Code Analysis Tool")
    print("=" * 80)
    print(f"Target: {target_path}")
    print(f"Output: {output_dir}")
    print(f"Language: {language}")
    print(f"Inject Mode: {inject_mode}")
    print(f"Job ID: {job_id}")
    print("=" * 80 + "\n")

    # Validate target
    if not os.path.exists(target_path):
        print(f"[ERROR] Target path does not exist: {target_path}")
        return 1

    # Initialize logger
    logger = get_audit_logger(output_dir=output_dir, job_id=job_id)

    try:
        # Step 1: Scan codebase
        print("Step 1: Scanning Codebase")
        print("-" * 80)
        scan_results = scan_codebase(
            target_dir=target_path,
            language=language,
            output_dir=output_dir,
            logger=logger
        )

        print(f"\nScan complete!")
        print(f"  Files scanned: {scan_results['files_scanned']}")
        print(f"  Lines of code: {scan_results['metadata']['total_code_lines']}")
        print(f"  Detections: {len(scan_results['detections'])}")
        print()

        # Log VC events
        logger.log_vc_event("codebase_scanned", count=1, metadata={
            "files_scanned": scan_results['files_scanned'],
            "lines_of_code": scan_results['metadata']['total_code_lines']
        })

        for detection in scan_results['detections']:
            detection_type = detection.get('type', 'unknown')
            logger.log_vc_event(f"{detection_type}_detected", count=1)

        # Step 2: Inject VC decorators (optional)
        injection_results = None
        if inject_mode:
            print("Step 2: Injecting VC Decorators")
            print("-" * 80)

            injection_results = inject_vc_decorators(
                scan_results=scan_results,
                output_dir=output_dir,
                logger=logger
            )

            print(f"\nInjection complete!")
            print(f"  Files patched: {injection_results['summary']['files_patched']}")
            print(f"  Total injections: {injection_results['summary']['total_injections']}")
            print()
        else:
            print("Step 2: Skipping VC Injection (use --inject to enable)")
            print()

        # Step 3: Generate reports
        print("Step 3: Generating Reports")
        print("-" * 80)

        report_paths = build_audit_reports(
            scan_results=scan_results,
            output_dir=output_dir,
            injection_results=injection_results,
            logger=logger
        )

        print(f"\nReports generated:")
        for format_type, path in report_paths.items():
            print(f"  {format_type.upper()}: {path}")
        print()

        # Final summary
        print("=" * 80)
        print("Audit Complete")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Target: {target_path}")
        print(f"  Files scanned: {scan_results['files_scanned']}")
        print(f"  Findings: {len(scan_results['detections'])}")
        print(f"  Duration: {utils.format_duration(scan_results['statistics']['scan_duration'])}")
        print(f"\nOutput files:")
        for format_type, path in report_paths.items():
            print(f"  - {path}")
        print(f"  - {os.path.join(output_dir, f'{job_id}_audit_log.jsonl')}")
        if injection_results:
            print(f"  - {injection_results['summary']['patched_dir']}/")
        print("\n" + "=" * 80)

        return 0

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        if logger:
            logger.log_error(
                error_message=str(e),
                module="main",
                context={
                    "target": target_path,
                    "language": language
                }
            )

        return 1


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Meta Auditor - Automated Code Auditing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan Part A codebase
  python auditor.py --target ../partA_document_agent/src/

  # Scan with injection
  python auditor.py --target ../partA_document_agent/src/ --inject

  # Scan JavaScript project
  python auditor.py --target ./frontend/src --language js

  # Custom output directory
  python auditor.py --target ./codebase --output ./audit_results
        """
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Path to directory or file to audit"
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for reports (default: output)"
    )

    parser.add_argument(
        "--language",
        choices=["python", "js"],
        default="python",
        help="Target programming language (default: python)"
    )

    parser.add_argument(
        "--inject",
        action="store_true",
        help="Inject VC decorators into patched code"
    )

    parser.add_argument(
        "--job-id",
        help="Optional job identifier for this audit"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
