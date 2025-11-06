# Document Review and Audit Agent - Value Credits System

## Project Overview

This repository contains a two-part automation system for document processing and codebase auditing with Value Credit (VC) tracking:

- **Part A**: Document Review Agent - Processes documents, detects sensitive information, and manages human approval workflows
- **Part B**: Meta Auditor - Analyzes codebases to detect external API calls, LLM usage, and suggests automated VC instrumentation

## Architecture Philosophy

- **Clean Modular Design**: Each component has a single, well-defined responsibility
- **Value Credit Tracking**: All processing steps are instrumented with VC counters
- **Reproducible Results**: Consistent output structure and logging
- **Extensible Framework**: Easy to add new detectors, processors, and metrics

## Repository Structure

```
value-credits-agent/
├── partA_document_agent/      # Document processing engine
│   ├── src/                   # Core processing modules
│   ├── output/                # Job outputs and results
│   ├── test_docs/             # Sample documents
│   └── readme.md              # Part A documentation
├── partB_meta_auditor/        # Codebase analysis engine
│   ├── src/                   # Scanning and injection tools
│   ├── output/                # Audit reports
│   ├── test_code/             # Mock code samples
│   └── readme.md              # Part B documentation
├── shared/                    # Common utilities
│   ├── utils/                 # Shared helper functions
│   └── constants/             # Shared constants
├── short_demo/                # Video demonstrations
└── master_readme.md           # This file
```

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Virtual environment (recommended)
- Git

### Setup Steps

1. **Clone and Setup Environment**
   ```bash
   cd value-credits-agent
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (if using OpenAI API)
   ```

3. **Verify Setup**
   - Check Phase 0 checklist in respective part readme files
   - Run test artifacts to verify installation

## Quick Start - How to Run

### Part A - Document Review Agent

Navigate to Part A directory:
```bash
cd partA_document_agent
```

**Example 1: Process a clean PDF (no sensitive data)**
```bash
python3 src/main.py --input test_docs/sample_clean.pdf --output output/ --job-id DOC-2025-002 --human-approval auto
```

**Example 2: Process a sensitive PDF (with PII - interactive mode)**
```bash
python3 src/main.py --input test_docs/sample_sensitive.pdf --output output/ --job-id DOC-2025-001
```
*(Will prompt for approval - press 'y' to approve)*

**Example 3: Process a URL**
```bash
python3 src/main.py --input https://httpbin.org/html --output output/ --job-id DOC-2025-003
```

**View Results:**
```bash
ls -la output/DOC-2025-002_*          # List all output files
cat output/DOC-2025-002_vc_summary.json  # View VC summary
```

### Part B - Meta Auditor

Navigate to Part B directory:
```bash
cd ../partB_meta_auditor
```

**Example 1: Scan a codebase (audit mode)**
```bash
python3 src/auditor.py --target ../partA_document_agent/src/ --output-dir output/
```

**Example 2: Scan with decorator injection (bonus feature)**
```bash
python3 src/auditor.py --target ../partA_document_agent/src/ --output-dir output/ --inject
```

**View Results:**
```bash
ls -la output/AUDIT-*.txt                  # List all audit reports
cat output/AUDIT-20251105-174031_audit_report.txt  # View latest report
```

### Command Options

**Common arguments:**
- `--input` or `--target`: File/directory to process
- `--output` or `--output-dir`: Where to save results
- `--job-id`: Unique identifier for the job
- `--human-approval`: auto, cli, or none
- `--inject`: Enable decorator injection (Part B only)

### Expected Output

Each run creates:
- **Raw text file** (`*_raw.txt`) - Extracted content
- **VC summary** (`*_vc_summary.json`) - Value Credits tracking
- **Log file** (`*_log.txt`) - Processing log
- **Audit report** (Part B) - Code analysis findings

### Value Credits Summary Format

The VC summary includes **timestamps and durations for each step** (Bonus feature):

```json
{
  "job_id": "DOC-2025-002",
  "vc_summary": [
    {
      "name": "text_extracted",
      "count": 1,
      "timestamp": "2025-11-06T20:47:43.123Z",
      "duration_ms": 1.2
    },
    {
      "name": "red_flags_found",
      "count": 1,
      "timestamp": "2025-11-06T20:47:43.125Z"
    },
    {
      "name": "external_api_called",
      "count": 1,
      "timestamp": "2025-11-06T20:47:45.623Z",
      "duration_ms": 2497.8
    }
  ],
  "total_vc_steps": 6
}
```

**Features:**
- ✅ ISO 8601 timestamps for each VC step
- ✅ Duration in milliseconds for performance tracking
- ✅ Complete audit trail with metadata

### Troubleshooting

**"python: command not found"**
```bash
# Use python3 instead
python3 src/main.py ...
```

**"No module named 'pypdf'"**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Permission denied**
```bash
# Make sure you're in the correct directory
cd /path/to/value-credits-agent
```

## Phases

### Phase 0: Foundation (Current)
- [x] Project structure creation
- [x] Documentation and assumptions
- [x] Test artifacts and dependencies
- [x] Git initialization

### Phase 1: Document Review Agent MVP
- Text extraction from PDF and URL
- Red-flag detection (PII patterns)
- External API integration
- Human approval workflow
- VC tracking and reporting

### Phase 2: Enhanced Features
- Multiple file format support
- Advanced PII detection
- Web UI for human approval
- Error handling and retries
- Unit tests

### Phase 3: Meta Auditor
- Code crawling and parsing
- External API detection
- LLM usage identification
- Token usage estimation
- Automated code injection

### Phase 4: Integration and Demo
- End-to-end testing
- Video demonstration
- Comprehensive documentation

## Value Credit (VC) System

The VC system tracks all meaningful operations in the pipeline:
- Text extraction events
- PII detection results
- API calls (external and internal)
- Human approval interactions
- Processing timestamps and durations

Each job produces a VC summary JSON with complete audit trail.

## Security & Privacy

- **No Real PII**: All test documents use synthetic data
- **Secure Defaults**: Environment variables for sensitive config
- **Audit Logging**: All actions logged with timestamps
- **Reproducible**: Deterministic processing for consistent results

## Documentation

- [Part A: Document Review Agent](partA_document_agent/readme.md)
- [Part B: Meta Auditor](partB_meta_auditor/readme.md)
- [Assumptions & Scope - Phase 0](partA_document_agent/readme.md#assumptions--scope--phase-0)

## License

Internal use - Development Team
