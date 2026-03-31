"""
Comprehensive test for all 18 bug fixes in the Legal AI Platform.
Run from backend/ with: .\venv\Scripts\python.exe test_all_fixes.py
"""
import sys
import os

# Ensure parent dir is on path so 'backend.*' imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

passed = 0
failed = 0
total = 0


def test(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


# =============================================
# 1. contract_analyzer.py — no bad import
# =============================================
print("\n=== Fix 1: No 'from email.mime import text' ===")
with open(os.path.join(os.path.dirname(__file__), "pipelines", "contract_analyzer.py")) as f:
    source = f.read()
test("No email.mime import", "from email.mime" not in source)

# =============================================
# 2. Clause segmentation preserves paragraphs
# =============================================
print("\n=== Fix 2: Clause segmentation preserves paragraph breaks ===")
from backend.pipelines.contract_analyzer import segment_clauses

sample_contract = """EMPLOYMENT AGREEMENT

This Employment Agreement is entered into as of January 1, 2024, by and between ACME Corporation and John Doe.

1. TERM OF EMPLOYMENT
The Employee shall be employed for a period of two years commencing on the date hereof. Either party may terminate this agreement with 30 days written notice and a cure period of 15 business days.

2. COMPENSATION AND PAYMENT
The Employee shall receive an annual salary of $120,000, payable in bi-weekly installments. A late fee of 1.5% per month will be applied to any overdue payments. Net 90 payment terms apply for contractor invoices.

3. CONFIDENTIALITY
The Employee agrees to maintain strict confidentiality of all proprietary information. This non-disclosure obligation shall survive the termination of employment indefinitely. Injunctive relief may be sought for any breach.

4. LIABILITY
The Company shall have unlimited liability for damages arising from gross negligence. Any claims must be filed within one year of the incident.

5. WARRANTY OF SERVICES
All services are provided as is without warranty of any kind, express or implied. The Company disclaims all warranties including merchantability.

6. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Texas, without regard to its conflict of laws provisions.

7. TERMINATION
Either party may immediately terminate this agreement without cause upon written notice. No cure period shall be required for termination under this section.
"""

clauses = segment_clauses(sample_contract)
test("Multiple clauses detected", len(clauses) >= 5, f"Got {len(clauses)} clauses")
test("No hardcoded 5-clause limit", len(clauses) >= 6, f"Got {len(clauses)} clauses (should be >= 6)")

# =============================================
# 3. LABEL_SHORT_NAMES mapping exists
# =============================================
print("\n=== Fix 3: LABEL_SHORT_NAMES mapping ===")
from backend.pipelines.contract_analyzer import LABEL_SHORT_NAMES

test("LABEL_SHORT_NAMES has 6 entries", len(LABEL_SHORT_NAMES) == 6)
test("Maps to 'Termination'", "Termination" in LABEL_SHORT_NAMES.values())
test("Maps to 'Payment'", "Payment" in LABEL_SHORT_NAMES.values())
test("Maps to 'Warranty'", "Warranty" in LABEL_SHORT_NAMES.values())
test("Maps to 'Confidentiality'", "Confidentiality" in LABEL_SHORT_NAMES.values())

# =============================================
# 4. "no clauses" check is AFTER the loop
# =============================================
print("\n=== Fix 4: 'No clauses' check after loop ===")
# Check source indentation: 'if not analyzed_clauses' should be at function-level indent
lines = source.split("\n")
for i, line in enumerate(lines):
    if "if not analyzed_clauses" in line:
        # Should NOT be inside a for-loop (should have 4 spaces indent, not 8+)
        indent = len(line) - len(line.lstrip())
        test("'if not analyzed_clauses' at correct indent", indent <= 4, f"indent={indent}")
        break

# =============================================
# 5. No hardcoded 5-clause limit
# =============================================
print("\n=== Fix 5: No hardcoded clause limit ===")
test("No '[:5]' slicing in source", "[:5]" not in source)
test("No 'clauses[:' in source", "clauses[:" not in source)

# =============================================
# 6. Risk engine — Payment, Warranty, Confidentiality rules
# =============================================
print("\n=== Fix 6: Risk engine supports all clause types ===")
from backend.services.risk_engine import assess_risk

risk_tests = [
    ("Liability", "The company shall have unlimited liability for all damages", "HIGH"),
    ("Liability", "Liability is capped at the total contract value", "LOW"),
    ("Termination", "Either party may immediately terminate without cause", "HIGH"),
    ("Termination", "Termination requires 30 days notice and cure period", "LOW"),
    ("Governing Law", "Governed by the laws of Texas", "MEDIUM"),
    ("Payment", "A late fee of 1.5 percent will be applied", "MEDIUM"),
    ("Payment", "Payment is due net 90 days", "MEDIUM"),
    ("Warranty", "The software is provided as is without warranty", "HIGH"),
    ("Warranty", "Limited warranty for defects in materials", "MEDIUM"),
    ("Confidentiality", "Confidentiality obligations shall survive indefinitely", "MEDIUM"),
    ("Confidentiality", "Standard non-disclosure agreement terms", "LOW"),
    ("Confidentiality", "Injunctive relief may be sought for breach", "MEDIUM"),
]

for clause_type, text, expected_level in risk_tests:
    result = assess_risk(text, clause_type)
    test(
        f"Risk({clause_type}): {expected_level}",
        result["level"] == expected_level,
        f"got {result['level']}, reason: {result['reason']}"
    )

# =============================================
# 7. __init__.py files exist
# =============================================
print("\n=== Fix 7: All __init__.py files exist ===")
base = os.path.dirname(__file__)
init_paths = [
    os.path.join(base, "__init__.py"),
    os.path.join(base, "pipelines", "__init__.py"),
    os.path.join(base, "services", "__init__.py"),
    os.path.join(base, "routers", "__init__.py"),
    os.path.join(base, "database", "__init__.py"),
]
for p in init_paths:
    rel = os.path.relpath(p, base)
    test(f"{rel} exists", os.path.exists(p))

# =============================================
# 8. Tesseract path configurable via env var
# =============================================
print("\n=== Fix 8: Tesseract path configurable ===")
with open(os.path.join(base, "services", "parsers.py")) as f:
    parsers_src = f.read()
test("Uses TESSERACT_CMD env var", "TESSERACT_CMD" in parsers_src)
test("Uses os.getenv", 'os.getenv("TESSERACT_CMD")' in parsers_src or "os.getenv('TESSERACT_CMD')" in parsers_src)

# =============================================
# 9. ChromaDB uses absolute path via pathlib
# =============================================
print("\n=== Fix 9: ChromaDB absolute path ===")
with open(os.path.join(base, "database", "connection.py")) as f:
    conn_src = f.read()
test("Uses pathlib", "from pathlib import Path" in conn_src or "import pathlib" in conn_src)
test("Uses Path(__file__)", "Path(__file__)" in conn_src)
test("No hardcoded relative ./chroma_db", "path='./chroma_db'" not in conn_src and 'path="./chroma_db"' not in conn_src)

# =============================================
# 10. Upload response doesn't send full parsed text
# =============================================
print("\n=== Fix 10: Upload response doesn't send full parsed text ===")
with open(os.path.join(base, "routers", "upload.py")) as f:
    upload_src = f.read()
test("No 'parsed' key in response", '"parsed"' not in upload_src or "'parsed'" not in upload_src)

# =============================================
# 11. .env.example exists
# =============================================
print("\n=== Fix 11: .env.example exists ===")
env_path = os.path.join(base, ".env.example")
test(".env.example exists", os.path.exists(env_path))
if os.path.exists(env_path):
    with open(env_path) as f:
        env_content = f.read()
    test(".env.example has DATABASE_URL", "DATABASE_URL" in env_content)
    test(".env.example has TESSERACT_CMD", "TESSERACT_CMD" in env_content)

# =============================================
# Frontend checks (source file analysis only)
# =============================================
frontend_src = os.path.join(base, "..", "frontend", "src")

# 12. index.css — max-width fix
print("\n=== Fix 12: CSS max-width fix ===")
with open(os.path.join(frontend_src, "index.css")) as f:
    css_src = f.read()
test("No 'max-w-px' in CSS", "max-w-px" not in css_src)
test("Has 'max-width' in CSS", "max-width" in css_src)

# 13. background-clip standard property
print("\n=== Fix 13: background-clip standard property ===")
test("Has 'background-clip' (standard)", "background-clip:" in css_src)

# 14. Responsive breakpoint
print("\n=== Fix 14: Responsive breakpoint ===")
test("Has @media max-width: 768px", "768px" in css_src)

# 15. App.css deleted
print("\n=== Fix 15: App.css deleted ===")
app_css_path = os.path.join(frontend_src, "App.css")
test("App.css does not exist", not os.path.exists(app_css_path))

# 16. index.html fixes
print("\n=== Fix 16: index.html fixes ===")
with open(os.path.join(base, "..", "frontend", "index.html")) as f:
    html_src = f.read()
test("Title is 'Legal AI Platform'", "Legal AI Platform" in html_src)
test("Has meta description", 'meta name="description"' in html_src)
test("Loads Inter font", "fonts.googleapis.com" in html_src and "Inter" in html_src)

# 17. Vite proxy config
print("\n=== Fix 17: Vite proxy config ===")
with open(os.path.join(base, "..", "frontend", "vite.config.js")) as f:
    vite_src = f.read()
test("Has /api proxy", "'/api'" in vite_src)
test("Proxies to localhost:8000", "localhost:8000" in vite_src)

# 18. UploadForm uses relative URL
print("\n=== Fix 18: UploadForm uses relative URL ===")
with open(os.path.join(frontend_src, "components", "UploadForm.jsx")) as f:
    upload_form_src = f.read()
test("Uses '/api/upload'", "'/api/upload'" in upload_form_src)
test("No hardcoded localhost URL", "http://localhost:8000" not in upload_form_src)

# App.jsx — no duplicate index.css import
print("\n=== Bonus: App.jsx no duplicate CSS import ===")
with open(os.path.join(frontend_src, "App.jsx")) as f:
    app_src = f.read()
test("No index.css import in App.jsx", "index.css" not in app_src)

# =============================================
# SUMMARY
# =============================================
print(f"\n{'='*50}")
print(f"RESULTS: {passed}/{total} tests passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {failed} test(s) failed!")
print(f"{'='*50}")
