"""
Human Approval Module

Handles human-in-the-loop approval workflow.
Supports three modes:
- cli: Interactive CLI prompt
- auto: Automatic approval
- none: Skip approval entirely

Records all approval decisions in VC log.
"""

from typing import List, Dict, Any
import sys

import vc_tracker


def request_human_approval(
    flags: List[Dict[str, Any]],
    mode: str = "cli"
) -> bool:
    """
    Request human approval if sensitive data is detected.

    Args:
        flags: List of detected red flags
        mode: Approval mode (cli, auto, none)

    Returns:
        True if approved, False if rejected

    Raises:
        ValueError: If invalid mode is specified
    """
    if mode == "none":
        print(f"[INFO] Human approval skipped (mode: none)")
        return True

    if mode == "auto":
        print(f"[INFO] Auto-approving processing (mode: auto)")
        vc_tracker.vc_step(
            "human_approval_requested",
            count=1,
            meta={"mode": "auto", "auto_approved": True}
        )
        vc_tracker.vc_step("human_approved", count=1)
        return True

    if mode == "cli":
        return _cli_approval_prompt(flags)

    raise ValueError(f"Invalid approval mode: {mode}. Must be 'cli', 'auto', or 'none'.")


def _cli_approval_prompt(flags: List[Dict[str, Any]]) -> bool:
    """
    Interactive CLI prompt for human approval.

    Args:
        flags: List of detected red flags

    Returns:
        True if approved, False if rejected
    """
    # Log that approval was requested
    vc_tracker.vc_step("human_approval_requested", count=1)

    # Display detected flags
    print("\n" + "=" * 70)
    print("⚠️  SENSITIVE DATA DETECTED")
    print("=" * 70)

    # Group flags by type
    flag_summary = {}
    for flag in flags:
        flag_type = flag["type"]
        if flag_type not in flag_summary:
            flag_summary[flag_type] = []
        flag_summary[flag_type].append(flag["value"])

    # Display summary
    for flag_type, values in flag_summary.items():
        count = len(values)
        print(f"\n{flag_type.capitalize()}s found: {count}")
        for value in values[:3]:  # Show first 3
            print(f"  - {value}")
        if count > 3:
            print(f"  ... and {count - 3} more")

    print("\n" + "-" * 70)
    print("Do you want to approve processing of this document?")
    print("  [y] Yes, approve")
    print("  [n] No, reject")
    print("  [a] Approve with annotation")
    print("-" * 70)

    while True:
        try:
            response = input("\nYour choice [y/n/a]: ").strip().lower()

            if response == "y":
                vc_tracker.vc_step("human_approved", count=1)
                print("\n✅ Processing approved")
                return True

            elif response == "n":
                vc_tracker.vc_step("human_rejected", count=1)
                print("\n❌ Processing rejected")
                return False

            elif response == "a":
                annotation = input("Enter annotation: ").strip()
                vc_tracker.vc_step(
                    "human_approved",
                    count=1,
                    meta={"annotation": annotation}
                )
                print(f"\n✅ Processing approved with annotation: {annotation}")
                return True

            else:
                print("Invalid choice. Please enter 'y', 'n', or 'a'")

        except KeyboardInterrupt:
            print("\n\n[INFO] Input cancelled by user")
            print("Treating as rejection for safety")
            vc_tracker.vc_step("human_rejected", count=1, meta={"reason": "cancelled"})
            return False
        except EOFError:
            print("\n\n[INFO] End of input")
            print("Treating as rejection for safety")
            vc_tracker.vc_step("human_rejected", count=1, meta={"reason": "eof"})
            return False


def get_approval_status(flags: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
    """
    Get approval status information.

    Args:
        flags: List of detected flags
        mode: Approval mode

    Returns:
        Status dictionary
    """
    requires_approval = mode != "none" and len(flags) > 0

    return {
        "requires_approval": requires_approval,
        "flags_count": len(flags),
        "mode": mode
    }
