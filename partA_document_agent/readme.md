# Part A: Document Review Agent

## Overview

The Document Review Agent processes documents (PDFs and URLs), extracts text, detects sensitive information, and manages human approval workflows. All operations are tracked using the Value Credit (VC) system for complete auditability.

## Assumptions & Scope – Phase 0

| Category | Assumption / Decision |
|----------|----------------------|
| Language & Runtime | Python 3.10 + for main implementation (other languages optional later). |
| Execution Mode | CLI-based for now (Flask UI optional in later phases). |
| Input Types | Local PDF and URL inputs only (docx, txt optional later). |
| External API | Use https://httpbin.org/post for demo; OpenAI LLM optional later. |
| Human Approval Mode | Default = CLI prompt; optional auto mode for headless runs. |
| Output Location | /output/ directory inside project root. |
| File Naming | All job outputs prefixed by <JOB_ID> (e.g., DOC-2025-001_raw.txt). |
| Data Security | No real PII in test docs – only synthetic data. |
| Logging Policy | Print to console + mirror in output/<JOB_ID>_log.txt. |
| Testing Artifacts | Dummy PDF and URL text sample created under /test_docs/. |
| Dependencies | pypdf, requests, beautifulsoup4, typer, json, time. |
| Value Credit System | VC = "Value Credit"; used to track processing steps per job. |
| Project Structure Philosophy | Clean modular folders, explicit responsibility per file, same pattern for both Part A & B. |

## Architecture

### Core Modules

- **extractor.py** - Text extraction from PDFs and URLs
- **redflag_detector.py** - PII and sensitive data detection
- **api_client.py** - External API communication
- **human_approval.py** - Human-in-the-loop approval workflow
- **vc_tracker.py** - Value Credit tracking and reporting

### Processing Flow

```
Input Document → Text Extraction → Red-Flag Detection → External API Call → Human Approval → Final Report
     ↓                ↓                   ↓                   ↓                ↓               ↓
  [VC: 1]        [VC: 1]            [VC: n flags]        [VC: 1]         [VC: 1]       [VC: 1]
```

## Usage

### Basic CLI Usage

```bash
# Process a local PDF
python src/main.py --input test_docs/sample_clean.pdf --job-id DOC-2025-001

# Process a URL
python src/main.py --input https://example.com --job-id DOC-2025-002 --human-approval cli

# Auto-approve mode (no human interaction)
python src/main.py --input test_docs/sample_sensitive.pdf --job-id DOC-2025-003 --human-approval auto
```

### Command Line Arguments

- `--input`: Path to local PDF or URL to process
- `--job-id`: Unique identifier (format: DOC-YYYY-NNN)
- `--human-approval`: Mode selection (auto|cli|none, default: cli)
- `--external-api`: API endpoint (httpbin|openai, default: httpbin)

## Output Structure

All outputs are stored in `/output/` directory:

```
output/
├── DOC-2025-001_raw.txt          # Extracted text
├── DOC-2025-001_log.txt          # Processing log
├── DOC-2025-001_vc_summary.json  # Value Credit report
└── examples/                      # Example outputs
    ├── sample_clean_output.json
    └── sample_sensitive_output.json
```

### VC Summary Format

```json
{
  "job_id": "DOC-2025-001",
  "steps": [
    {"name": "text_extracted", "count": 1, "duration_ms": 420},
    {"name": "red_flags_found", "count": 2, "details": [...]},
    {"name": "external_api_called", "count": 1, "endpoint": "..."},
    {"name": "human_approval_requested", "count": 1},
    {"name": "human_approved", "count": 1}
  ],
  "total_vc_steps": 5
}
```

## Test Documents

### Available Samples

- **sample_clean.pdf** - Document with no sensitive data
- **sample_sensitive.pdf** - Document with fake PII (emails, phone numbers)
- **sample_url.txt** - Test URL for URL-based extraction

### Red-Flag Detection Patterns

The system detects:
- Email addresses (regex pattern)
- Phone numbers (US format)
- Configurable keywords (password, ssn, confidential, etc.)

## API Integration

### httpbin.org (Default)

- Endpoint: https://httpbin.org/post
- Purpose: Echo metadata for demonstration
- No authentication required
- Response time: ~200-500ms

### OpenAI (Optional)

- Endpoint: OpenAI API
- Purpose: LLM-based content analysis
- Requires: OPENAI_API_KEY in .env
- Token usage tracking included

## Human Approval Workflow

### Modes

1. **CLI Prompt** (default) - Interactive command-line approval
2. **Auto** - Automatic approval for headless runs
3. **None** - Skip approval step entirely

### Approval Options

- **Approve** - Continue with current findings
- **Reject** - Stop processing
- **Annotate** - Add notes and approve

All decisions are logged in the VC summary with timestamps.

## ✅ Phase 0 Setup Checklist

- [ ] Python env created and activated
- [ ] Requirements installed
- [ ] Folder structure created exactly as specified
- [ ] Dummy test files added
- [ ] .env.example created
- [ ] README assumptions verified
- [ ] Git repo initialized

## Development

### Running Tests

```bash
# Test text extraction
python -m pytest tests/test_extractor.py -v

# Test red-flag detection
python -m pytest tests/test_redflag.py -v

# Test end-to-end flow
python -m pytest tests/test_e2e.py -v
```

### Adding New Detectors

1. Create detector function in `redflag_detector.py`
2. Add regex pattern or keyword list
3. Update VC tracking in `vc_tracker.py`
4. Add test case in `tests/`
5. Document in this README

## Troubleshooting

### Common Issues

**PDF Extraction Fails**
- Ensure file is not password-protected
- Check file is valid PDF format
- Verify pypdf is installed correctly

**No Red Flags Detected**
- Check patterns in redflag_detector.py
- Verify test document contains expected PII
- Review extraction quality in raw output

**External API Timeout**
- Check internet connection
- Verify httpbin.org is accessible
- Review timeout settings in api_client.py

## Security Notes

- Never commit real PII or sensitive documents
- Use synthetic data only in test files
- Store API keys in .env, never in code
- All processing logged with timestamps
- Output files may contain sensitive data - secure appropriately

## Future Enhancements (Phase 2+)

- [ ] Support docx, txt, and md file formats
- [ ] Advanced PII detectors (credit cards, SSNs, etc.)
- [ ] Web UI for human approval
- [ ] Retry logic for API failures
- [ ] Configurable detection rules (YAML)
- [ ] Batch processing mode
- [ ] Email/notification on completion
- [ ] Visual report generation (PDF/HTML)
