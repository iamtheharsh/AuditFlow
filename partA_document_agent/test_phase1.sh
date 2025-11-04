#!/bin/bash
# Test script for Phase 1 Document Review Agent
# This script runs all three test scenarios and displays results

echo "================================================================================"
echo "Document Review Agent - Phase 1 Test Suite"
echo "================================================================================"
echo ""

# Test 1: Clean PDF
echo "Test 1: Processing Clean PDF (no human approval needed)"
echo "--------------------------------------------------------------------------------"
python3 src/main.py --input test_docs/sample_clean.pdf --job-id DOC-2025-T1 --human-approval none
echo ""
echo "Result files:"
ls -lh output/DOC-2025-T1_* 2>/dev/null || echo "No output files found"
echo ""
echo ""

# Test 2: Sensitive PDF (auto approval)
echo "Test 2: Processing Sensitive PDF (auto approval)"
echo "--------------------------------------------------------------------------------"
python3 src/main.py --input test_docs/sample_sensitive.pdf --job-id DOC-2025-T2 --human-approval auto
echo ""
echo "Result files:"
ls -lh output/DOC-2025-T2_* 2>/dev/null || echo "No output files found"
echo ""
echo ""

# Test 3: URL
echo "Test 3: Processing URL"
echo "--------------------------------------------------------------------------------"
python3 src/main.py --input https://example.com --job-id DOC-2025-T3 --human-approval none
echo ""
echo "Result files:"
ls -lh output/DOC-2025-T3_* 2>/dev/null || echo "No output files found"
echo ""
echo ""

echo "================================================================================"
echo "Test Suite Complete"
echo "================================================================================"
echo ""
echo "Summary of outputs:"
echo "-------------------"
echo "Each test produces:"
echo "  - <JOB_ID>_raw.txt     : Extracted text"
echo "  - <JOB_ID>_log.txt     : Human-readable log"
echo "  - <JOB_ID>_vc_summary.json : Value Credit summary"
echo ""
echo "All test outputs saved in: output/"
echo "Example outputs available in: output/examples/"
echo ""
