#!/usr/bin/env python3
"""
Generate test PDF documents for Document Review Agent testing.
Run this script to create sample_clean.pdf and sample_sensitive.pdf
"""

import os
from pathlib import Path

def create_test_pdfs():
    """Create test PDF files using reportlab."""

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        print("reportlab not installed. Installing...")
        os.system("pip install reportlab")
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

    # Create output directory
    output_dir = Path("value-credits-agent/partA_document_agent/test_docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample Clean PDF
    clean_pdf = output_dir / "sample_clean.pdf"
    c = canvas.Canvas(str(clean_pdf), pagesize=letter)
    width, height = letter

    y = height - 50
    c.setFont("Helvetica", 12)

    lines = [
        "This is a test document for the Document Review Agent.",
        "",
        "It contains no sensitive information and should pass all red-flag detection tests.",
        "",
        "The purpose of this document is to verify that:",
        "1. Text extraction works correctly",
        "2. No false positives are reported",
        "3. The processing pipeline completes successfully",
        "",
        "This document was created for testing purposes only.",
        "No personal or confidential information is included.",
        "",
        "Generated for Phase 0 setup."
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    c.save()
    print(f"✓ Created: {clean_pdf}")

    # Sample Sensitive PDF
    sensitive_pdf = output_dir / "sample_sensitive.pdf"
    c = canvas.Canvas(str(sensitive_pdf), pagesize=letter)
    y = height - 50
    c.setFont("Helvetica", 12)

    lines = [
        "This is a test document with synthetic PII data for red-flag detection.",
        "",
        "Contact Information:",
        "Email: test.user@example.com",
        "Phone: 987-654-3210",
        "",
        "Credentials:",
        "Password: MySecret123!",
        "",
        "Note: This document contains FAKE sensitive data for testing only.",
        "All phone numbers, emails, and credentials are fictitious.",
        "DO NOT use this document outside of testing purposes.",
        "",
        "The red-flag detector should find:",
        "1. Email address: test.user@example.com",
        "2. Phone number: 987-654-3210",
        "3. Keyword: password",
        "",
        "Generated for Phase 0 setup."
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    c.save()
    print(f"✓ Created: {sensitive_pdf}")
    print("\n✅ All test PDFs created successfully!")

if __name__ == "__main__":
    create_test_pdfs()
