# Part B: Meta Auditor

## Overview

The Meta Auditor is an automated code analysis tool that inspects codebases to detect external API calls, LLM usage, and cloud service integrations. It generates audit reports and can automatically inject Value Credit (VC) tracking decorators into discovered code paths.

## Core Capabilities

### 1. Code Crawling & Parsing
- Recursively walks directory structures
- Parses Python files using AST (Abstract Syntax Tree)
- JavaScript/Node.js support via regex and heuristics
- Identifies function calls, imports, and API usage patterns

### 2. External API Detection
Detects HTTP client usage:
- Python: `requests.get/post`, `urllib.request`, `httpx`, `aiohttp`
- JavaScript: `fetch()`, `axios.*`, `node-fetch`
- Records file location, line number, and endpoint URLs

### 3. LLM Usage Identification
Finds machine learning and LLM integrations:
- OpenAI API calls (`openai.ChatCompletion.create`)
- Anthropic Claude API
- Hugging Face Transformers (`transformers`, `pipeline`)
- Local model inference (PyTorch, ONNX)

### 4. Token Usage Estimation
For detected LLM calls:
- Estimates token count from prompt strings (chars/4 heuristic)
- Calculates low/likely/high ranges
- Identifies cost drivers (model type, max_tokens, temperature)
- Generates cost projections

### 5. Automated Code Injection
Safe decorator injection system:
- Inserts VC tracking decorators above detected functions
- Creates patched copies (never overwrites originals)
- Supports custom metric naming
- Rollback capability (use patched/ directory)

## Usage

### Basic Audit

```bash
# Audit a Python project
python src/auditor.py --target ../partA_document_agent/src --output output/

# Generate report only (no injection)
python src/auditor.py --target ../partA_document_agent --report-only

# Custom injection directory
python src/auditor.py --target . --injection-dir my_patched/
```

### Command Line Arguments

- `--target`: Path to codebase to audit (required)
- `--output`: Directory for audit reports (default: output/)
- `--injection-dir`: Directory for patched code (default: patched/)
- `--report-only`: Generate report without injecting decorators
- `--language`: Target language (python|javascript|auto, default: auto)

## Output Structure

```
output/
├── audit_report.json          # Machine-readable findings
└── sample_report.txt          # Human-readable summary
patched/                       # Decorated code copies
    ├── src/
    │   ├── extractor.py       # Original
    │   ├── extractor.py.patched  # With VC decorators
    │   └── ...
    └── ...
```

### Audit Report Format (JSON)

```json
{
  "scan_metadata": {
    "target_path": "../partA_document_agent/src",
    "timestamp": "2025-11-04T12:00:00Z",
    "files_scanned": 12
  },
  "findings": {
    "external_apis": [
      {
        "file": "src/api_client.py",
        "line": 45,
        "function": "call_httpbin",
        "pattern": "requests.post",
        "endpoint": "https://httpbin.org/post"
      }
    ],
    "llm_usage": [
      {
        "file": "src/llm_client.py",
        "line": 23,
        "library": "openai",
        "model": "gpt-4o",
        "estimated_tokens": 1200,
        "parameters": {"max_tokens": 500, "temperature": 0.7}
      }
    ],
    "cloud_hints": [
      {
        "file": "src/model_loader.py",
        "line": 12,
        "library": "transformers",
        "type": "local_inference"
      }
    ]
  },
  "suggested_metrics": [
    "text_extracted",
    "external_api_call",
    "llm_token_usage",
    "model_inference"
  ],
  "total_cost_drivers": 4
}
```

### Sample Report (Text)

```
================================================================================
META AUDITOR - CODEBASE SCAN REPORT
================================================================================
Target: partA_document_agent/src
Timestamp: 2025-11-04 12:00:00Z
Files Scanned: 12

--------------------------------------------------------------------------------
EXTERNAL API CALLS DETECTED: 2
--------------------------------------------------------------------------------
1. requests.post at src/api_client.py:45
   Endpoint: https://httpbin.org/post
   [Suggested VC] @vc_tracker("external_api_call")

2. urllib.request.urlopen at src/downloader.py:78
   [Suggested VC] @vc_tracker("external_api_call")

--------------------------------------------------------------------------------
LLM USAGE DETECTED: 1
--------------------------------------------------------------------------------
1. openai.ChatCompletion.create at src/llm_client.py:23
   Model: gpt-4o
   Max Tokens: 500
   Estimated Tokens: 1,200
   [Suggested VC] @vc_tracker("llm_token_usage")

--------------------------------------------------------------------------------
CLOUD COMPUTE HINTS: 1
--------------------------------------------------------------------------------
1. transformers import in src/model_loader.py:12
   Type: Local inference engine
   [Suggested VC] @vc_tracker("model_inference")

--------------------------------------------------------------------------------
DECORATOR INJECTION SUMMARY
--------------------------------------------------------------------------------
Sites flagged for injection: 3
Patched files written to: patched/
Review patched files before deploying to production

Total Estimated Cost Drivers: 4
Recommended Metrics: text_extracted, external_api_call, llm_token_usage, model_inference
```

## Injection Decorator Example

The auditor can inject decorators like this:

**Before (src/api_client.py)**
```python
def call_external_api(data):
    response = requests.post("https://api.example.com", json=data)
    return response.json()
```

**After (src/api_client.py.patched)**
```python
# [VC] external_api_call detected here - Line 12
@vc_tracker("external_api_call")
def call_external_api(data):
    response = requests.post("https://api.example.com", json=data)
    return response.json()
```

## Detection Patterns

### Python Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `requests.get\|post\|put\|delete` | HTTP calls | `requests.post(url, json=data)` |
| `urllib.request` | URL fetching | `urllib.request.urlopen(url)` |
| `httpx\.(get\|post\|put)` | HTTPX client | `httpx.post(url, json=data)` |
| `openai\.(ChatCompletion\|Completion)` | OpenAI API | `openai.ChatCompletion.create(...)` |
| `from transformers import` | Hugging Face | `from transformers import pipeline` |
| `pipeline\(.*model` | HF pipeline | `pipeline("text-classification")` |
| `model\.generate\|forward` | Model inference | `model.generate(input_ids)` |
| `boto3\|google\.cloud\|azure` | Cloud SDK | `boto3.client('s3')` |

### JavaScript Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `fetch\(.*\)` | Fetch API | `fetch(url, options)` |
| `axios\.(get\|post\|put)` | Axios | `axios.post(url, data)` |
| `node-fetch` | Node fetch | `nodefetch(url)` |
| `openai\.(chat\|completions)` | OpenAI JS | `openai.chat.completions.create(...)` |

## Token Estimation Heuristics

The auditor uses character-based estimation:
- **Prompt tokens**: `len(prompt_string) / 4`
- **Context window**: Sum of all prompt+response text
- **Output range**:
  - Low: `chars / 5`
  - Likely: `chars / 4`
  - High: `chars / 3`

**Example:**
```python
prompt = f"Analyze this text: {text[:500]}"  # 25 chars
# Estimated: 6-8 tokens (likely: 25/4 = 6.25)
```

## Test Code Samples

The auditor includes mock code for testing:

```python
# test_code/mock_project.py
import requests
import openai

def test_external_call():
    response = requests.post("https://api.example.com", data={})
    return response.json()

def test_llm_call():
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100
    )
    return result
```

Running the auditor on this test code should detect:
- 1 external API call
- 1 LLM usage
- Suggested metrics: external_api_call, llm_token_usage

## Safety Features

### Non-Destructive Injection
- Original files are NEVER modified
- Patched copies written to separate directory
- Clear naming convention (`.patched` extension)
- Easy to compare changes (`diff`)

### Review Process
1. Auditor generates report
2. Review human-readable summary
3. Inspect patched files manually
4. Copy to production only after approval
5. Run tests to verify functionality

## Integration with Part A

The Meta Auditor is designed to work seamlessly with the Document Review Agent:

1. **Audit Part A codebase** to identify existing external calls
2. **Inject VC decorators** automatically
3. **Run Part A** and verify VC tracking works
4. **Compare outputs** before and after injection
5. **Deploy with confidence** knowing all operations are tracked

### Example Workflow

```bash
# Step 1: Audit the Part A code
cd partB_meta_auditor
python src/auditor.py --target ../partA_document_agent/src

# Step 2: Review output/sample_report.txt

# Step 3: Run Part A to generate baseline
cd ../partA_document_agent
python src/main.py --input test_docs/sample_clean.pdf

# Step 4: Copy patched files
cp -r ../partB_meta_auditor/patched/* src/

# Step 5: Run again with VC tracking
python src/main.py --input test_docs/sample_clean.pdf

# Step 6: Compare VC summaries
diff output/DOC-*-vc_summary.json output/DOC-*-vc_summary.json
```

## Extending the Auditor

### Adding New Patterns

1. **Edit `src/auditor.py`**
   ```python
   # Add to PATTERNS dictionary
   PATTERNS = {
       'external_api': [
           (r'your_library\.(get|post)', 'Your Library HTTP'),
           # ...
       ],
       'llm_usage': [
           (r'another_llm\.(generate|infer)', 'Another LLM'),
           # ...
       ]
   }
   ```

2. **Add tests** in `test_code/`
3. **Update documentation** here

### Custom Injection Logic

Override injection behavior in `src/injection.py`:
```python
def custom_injector(file_path, line_number, pattern_type, context):
    # Your custom injection logic
    return modified_code
```

## Limitations

- **Python AST**: Most accurate for Python code
- **JavaScript**: Regex-based, less precise than AST
- **Dynamic imports**: Cannot detect runtime string-based imports
- **Reflection**: May miss dynamically generated API calls
- **Context awareness**: Simple heuristics, not full semantic analysis

## Future Enhancements

- [ ] Tree-sitter integration for robust parsing
- [ ] Support for more languages (Go, Rust, Java)
- [ ] Real token counting via tiktoken
- [ ] Configuration file (YAML) for custom patterns
- [ ] CI/CD integration (GitHub Actions)
- [ ] Visual report (HTML with charts)
- [ ] Cost projection calculator
- [ ] Git history analysis
- [ ] Security vulnerability scanning
- [ ] License compliance checking
