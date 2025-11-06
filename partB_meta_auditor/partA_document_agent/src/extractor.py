"""
Text Extraction Module

Extracts text from PDF files and URLs (HTML or PDF).
Handles various input formats and produces clean text output.
"""

import time
import re
import os
from typing import Tuple, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

import vc_tracker

# Apply decorator for instrumentation
@vc_tracker.vc_decorator("text_extraction")
def extract_text(input_path: str, job_id: str, output_dir: str = "output") -> Tuple[str, str]:
    """
    Extract text from PDF file or URL.

    Args:
        input_path: Path to PDF file or URL
        job_id: Job identifier for logging
        output_dir: Directory to save raw text

    Returns:
        Tuple of (extracted_text, input_type)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If input format is not supported
        Exception: For extraction failures
    """
    start_time = time.time()

    print(f"[INFO] Starting text extraction from: {input_path}")

    # Determine input type
    if input_path.lower().startswith(("http://", "https://")):
        input_type = "url"
        text = _extract_from_url(input_path)
    elif input_path.lower().endswith(".pdf"):
        input_type = "pdf"
        text = _extract_from_pdf(input_path)
    else:
        raise ValueError(
            f"Unsupported input type. Must be PDF file or URL. Got: {input_path}"
        )

    # Clean and normalize text
    text = _clean_text(text)

    # Save raw text
    os.makedirs(output_dir, exist_ok=True)
    raw_text_path = os.path.join(output_dir, f"{job_id}_raw.txt")

    with open(raw_text_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log VC step
    char_count = len(text)
    vc_tracker.vc_step(
        "text_extracted",
        count=1,
        duration_ms=duration_ms,
        meta={
            "input_type": input_type,
            "char_count": char_count,
            "word_count": len(text.split()),
            "raw_text_path": raw_text_path
        }
    )

    print(f"[INFO] Extraction complete: {char_count} characters, {duration_ms:.1f}ms")
    print(f"[INFO] Raw text saved to: {raw_text_path}")

    return text, input_type


def _extract_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pypdf.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text from all pages

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: For PDF parsing errors
    """
    print(f"[INFO] Reading PDF: {pdf_path}")

    # Check if file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        print(f"[INFO] PDF has {len(reader.pages)} pages")

        text_parts = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                print(f"[WARN] Error extracting page {page_num + 1}: {e}")
                continue

        extracted_text = "\n".join(text_parts)

        if not extracted_text.strip():
            raise ValueError("No text extracted from PDF. File may be image-based or corrupted.")

        return extracted_text

    except Exception as e:
        raise Exception(f"Failed to extract text from PDF {pdf_path}: {e}")


def _extract_from_url(url: str) -> str:
    """
    Extract text from a URL (HTML or PDF).

    Args:
        url: URL to fetch

    Returns:
        Extracted text from the URL content

    Raises:
        Exception: For network or parsing errors
    """
    print(f"[INFO] Fetching URL: {url}")

    try:
# [VC] external_api_call detected here - GET url.lower
# Suggested: Add @vc_tracker('external_api_call') decorator or vc_step() call

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        # If it's a PDF, extract text
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            print(f"[INFO] Detected PDF content, saving to temp file")
            # Save to temp file and extract
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            try:
                text = _extract_from_pdf(tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            return text

        # Otherwise, parse as HTML
        elif "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        else:
            # Try to treat as text
            return response.text

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL {url}: {e}")


def _clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove null characters
    text = text.replace("\x00", "")

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
