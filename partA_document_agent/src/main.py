#!/usr/bin/env python3
"""
Document Review Agent - Main Entry Point

CLI tool for processing documents with:
- Text extraction (PDF/URL)
- Red-flag detection (PII scanning)
- External API integration
- Human approval workflow
- Value Credit tracking

Usage:
    python main.py --input <path_or_url> --job-id DOC-2025-001
    python main.py --input sample.pdf --job-id DOC-2025-001 --human-approval cli
    python main.py --input https://example.com --job-id DOC-2025-002 --external-api httpbin
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Import project modules
import vc_tracker
import extractor
import redflag_detector
import api_client
import human_approval


def main():
    """Main entry point for the Document Review Agent."""
    args = parse_arguments()

    job_id = args.job_id
    input_path = args.input
    human_approval_mode = args.human_approval
    external_api_type = args.external_api
    output_dir = args.output_dir

    print("=" * 70)
    print("Document Review Agent - Phase 1")
    print("=" * 70)
    print(f"Job ID: {job_id}")
    print(f"Input: {input_path}")
    print(f"Human Approval: {human_approval_mode}")
    print(f"External API: {external_api_type}")
    print(f"Output Directory: {output_dir}")
    print("=" * 70 + "\n")

    # Initialize VC tracking
    vc_tracker.init_session(job_id)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Log start
    start_time = time.time()
    print(f"[INFO] Starting job {job_id} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Step 1: Extract text
        print(f"Step 1: Text Extraction")
        print("-" * 70)
        text, input_type = extractor.extract_text(input_path, job_id, output_dir)
        print()

        # Step 2: Red-flag detection
        print(f"Step 2: Red-Flag Detection")
        print("-" * 70)
        flags, requires_human = redflag_detector.detect_red_flags(text, job_id)

        # Log red flags in VC
        if flags:
            vc_tracker.vc_step(
                "red_flags_found",
                count=len(flags),
                meta={"details": flags, "summary": redflag_detector.get_detection_summary(flags)}
            )
        else:
            vc_tracker.vc_step("red_flags_found", count=0, meta={"details": []})
        print()

        # Step 3: External API call
        print(f"Step 3: External API Call")
        print("-" * 70)
        api_result = api_client.call_external_api(
            job_id=job_id,
            flag_count=len(flags),
            input_length=len(text),
            api_type=external_api_type
        )
        print()

        # Step 4: Human approval (if required)
        if requires_human and human_approval_mode != "none":
            print(f"Step 4: Human Approval")
            print("-" * 70)
            approved = human_approval.request_human_approval(flags, human_approval_mode)
            print()

            if not approved:
                print(f"[WARN] Processing stopped due to human rejection")
                # Save partial VC summary
                vc_tracker.save_vc_summary(job_id, output_dir)
                return 1
        else:
            print(f"Step 4: Human Approval")
            print("-" * 70)
            print(f"[INFO] No human approval required")
            if not requires_human:
                print(f"  - No red flags detected")
            if human_approval_mode == "none":
                print(f"  - Approval mode: none")
            print()

        # Step 5: Save VC summary
        print(f"Step 5: Finalizing")
        print("-" * 70)

        # Calculate total runtime
        end_time = time.time()
        total_runtime = (end_time - start_time) * 1000

        print(f"Job completed successfully")
        print(f"Total runtime: {total_runtime:.1f}ms")
        print(f"Total VC steps: {vc_tracker.calculate_total_vc_steps()}")

        # Save VC summary
        summary_path = vc_tracker.save_vc_summary(job_id, output_dir)
        print(f"VC Summary: {summary_path}")

        # Save log file
        log_path = os.path.join(output_dir, f"{job_id}_log.txt")
        _save_log_file(job_id, log_path, args, flags, api_result, total_runtime)

        print()
        print("=" * 70)
        print("Job Complete")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        # Log error
        error_path = vc_tracker.log_error(
            job_id=job_id,
            step_name="main_execution",
            error=e,
            output_dir=output_dir
        )

        # Try to save partial VC summary
        try:
            vc_tracker.save_vc_summary(job_id, output_dir)
        except Exception as save_error:
            print(f"[WARN] Failed to save VC summary: {save_error}")

        return 1


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Document Review Agent - Process documents with VC tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a PDF file with CLI approval
  python main.py --input test_docs/sample_clean.pdf --job-id DOC-2025-001

  # Process a URL with auto-approval
  python main.py --input https://example.com --job-id DOC-2025-002 --human-approval auto

  # Process a sensitive PDF
  python main.py --input test_docs/sample_sensitive.pdf --job-id DOC-2025-003 --human-approval cli

  # Process without human approval
  python main.py --input test_docs/sample_clean.pdf --job-id DOC-2025-004 --human-approval none
        """
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to PDF file or URL to process"
    )

    parser.add_argument(
        "--job-id",
        required=True,
        help="Unique job identifier (format: DOC-YYYY-NNN)"
    )

    parser.add_argument(
        "--human-approval",
        choices=["auto", "cli", "none"],
        default="cli",
        help="Human approval mode (default: cli)"
    )

    parser.add_argument(
        "--external-api",
        choices=["httpbin", "openai"],
        default="httpbin",
        help="External API to call (default: httpbin)"
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )

    return parser.parse_args()


def _save_log_file(
    job_id: str,
    log_path: str,
    args: argparse.Namespace,
    flags: list,
    api_result: dict,
    total_runtime: float
) -> None:
    """Save a human-readable log file."""
    lines = [
        f"Document Review Agent - Job Log",
        f"Job ID: {job_id}",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"",
        f"Arguments:",
        f"  Input: {args.input}",
        f"  Job ID: {args.job_id}",
        f"  Human Approval: {args.human_approval}",
        f"  External API: {args.external_api}",
        f"  Output Directory: {args.output_dir}",
        f"",
        f"Results:",
        f"  Red Flags Found: {len(flags)}",
        f"  API Call Success: {api_result.get('success', False)}",
        f"  Total Runtime: {total_runtime:.1f}ms",
        f"  Total VC Steps: {vc_tracker.calculate_total_vc_steps()}",
        f"",
        f"VC Steps:",
    ]

    for step in vc_tracker.get_vc_log():
        lines.append(f"  - {step['name']}: {step['count']}")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Log file: {log_path}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
