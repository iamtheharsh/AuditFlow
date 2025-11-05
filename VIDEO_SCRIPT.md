# 📹 Value Credits Agent - Video Script (2 Minutes)

**Total Duration: ~2 minutes**
**Scene Setup: Terminal window showing commands and output**

---

## 🎬 SCENE 1: Introduction (15 seconds)

**[Show screen: Terminal prompt]**

**Narrator:**
```
Hi! I'm demonstrating the Value Credits Agent - a two-part system that processes
documents with automated auditing. Let's see it in action!
```

**[Type command on screen]**

```bash
cd value-credits-agent
```

---

## 🎬 SCENE 2: Part A - Document Review Agent (60 seconds)

**[Navigate to Part A]**

```bash
cd partA_document_agent
```

**Narrator:**
```
Part A: Document Review Agent. It processes documents, detects PII,
and tracks Value Credits at each step.
```

**[Show directory structure]**

```bash
ls -la src/
# Shows: main.py, extractor.py, redflag_detector.py, api_client.py, vc_tracker.py
```

**Narrator:**
```
Let's run it on a sample document with sensitive data:
```

**[Run the command]**

```bash
python3 src/main.py --input test_docs/sample_clean.pdf --output output/ --job-id DOC-2025-002 --human-approval auto
```

**[Show the output - fast-forward through it, highlight key parts]**

**Narrator (as output scrolls):**
```
✓ Text extracted: 440 characters
✓ Red-flag detected: 1 keyword found (confidential)
✓ External API called: httpbin.org/post (3.2 seconds)
✓ Human approval: Auto-approved
✓ Total VC steps: 6
```

**[Pause at summary]**

**Narrator:**
```
Notice the VC tracking - each step is logged with timestamps and metadata.
Let's check the output:
```

**[Show the files created]**

```bash
ls -la output/DOC-2025-002_*
# DOC-2025-002_raw.txt, DOC-2025-002_vc_summary.json, DOC-2025-002_log.txt
```

**[Show VC summary]**

```bash
cat output/DOC-2025-002_vc_summary.json
```

**[Highlight on screen]**
```json
{
  "job_id": "DOC-2025-002",
  "total_vc_steps": 6,
  "vc_summary": [
    {"name": "text_extracted", "count": 1, "duration_ms": 2.1},
    {"name": "red_flags_found", "count": 1},
    {"name": "external_api_called", "count": 1, "duration_ms": 3237.6},
    {"name": "human_approved", "count": 1}
  ]
}
```

**Narrator:**
```
Complete audit trail with 6 Value Credit steps, including timing!
```

---

## 🎬 SCENE 3: Part B - Meta Auditor (35 seconds)

**[Navigate to Part B]**

```bash
cd ../partB_meta_auditor
```

**Narrator:**
```
Part B: Meta Auditor. It scans codebases to detect API calls,
LLM usage, and suggests automated VC instrumentation.
```

**Narrator:**
```
Let's audit the Part A source code itself:
```

```bash
python3 src/auditor.py --target ../partA_document_agent/src/ --output-dir output/
```

**[Show output - emphasize findings]**

**Narrator:**
```
✓ 9 files scanned
✓ 2,319 lines of code
✓ 2 external API calls detected
✓ Report generated
```

**[Show the report]**

```bash
cat output/AUDIT-20251105-174031_audit_report.txt
```

**[Highlight key findings]**

```
FINDINGS:
1. EXTERNAL API - extractor.py:149 - requests.get()
2. EXTERNAL API - api_client.py:130 - requests.post()

RECOMMENDATIONS:
- Add @vc_tracker('external_api_call') decorator
- Suggested metrics: external_api_call
```

**Narrator:**
```
The auditor automatically detected external API calls and suggested
where to add Value Credit tracking!
```

---

## 🎬 SCENE 4: Bonus - Decorator Injection (10 seconds)

**Narrator:**
```
Bonus feature: Automatic decorator injection!
```

```bash
python3 src/auditor.py --target ../partA_document_agent/src/ --output-dir output/ --inject
```

**[Show injection results]**

```
Injection complete!
  Files patched: 2
  Total injections: 2

Output: output/patched/
```

**Narrator:**
```
The auditor created patched versions with @vc_tracker decorators
automatically injected!
```

---

## 🎬 SCENE 5: Wrap-up (10 seconds)

**[Show file structure]**

```bash
tree -L 2
```

**Narrator:**
```
That's it! Complete system with:
• Document processing with PII detection
• External API integration with retry logic
• Value Credit tracking for auditability
• Automated code auditing with decorator injection

Full source code: https://github.com/iamtheharsh/AuditFlow

Thanks for watching! 🎉
```

**[Fade to black with GitHub URL on screen]**

---

## 📋 Key Points to Emphasize:

1. **VC Tracking**: Every operation logged with timestamps and metadata
2. **PII Detection**: Emails, phones, keywords with confidence scores
3. **API Resilience**: Retry logic and circuit breaker pattern
4. **Code Analysis**: AST-based scanning for patterns
5. **Auto-Injection**: Decorators added automatically to tracked functions
6. **Audit Reports**: Both JSON and human-readable formats

## 🎥 Screen Recording Tips:

- **Use full-screen terminal** for clarity
- **Speed up long waits** (API calls, file scanning)
- **Highlight/circle** important output with cursor
- **Use zoom** for detailed JSON output
- **Add timestamps** in corner
- **Smooth transitions** between Part A and Part B

## 📝 What to Show on Screen:

- Terminal commands (type them in real-time if possible)
- Output files and their structure
- JSON summaries with syntax highlighting
- Before/after code with decorators
- Directory trees showing project structure

---

**Ready to record! Just follow this script and record your screen. 🚀**
