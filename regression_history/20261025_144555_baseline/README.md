# Ghost Data Still Exists

Evidence-driven deletion auditing for HackerRank Orchestrate October 2026. The program reads participant-facing inputs under `dataset/`, indexes evidence once, reconstructs identities/resource states at each audit cutoff, applies CSV policies and writes `output.csv`.

**Current quality limit:** output is structurally valid, but the strict semantic gate fails because some artifacts do not establish identity links or conditional retention eligibility. Measured sample metrics, every mismatch and unresolved counts are in [the evaluation report](code/evaluation/evaluation_report.md). This is not a claim of complete canonical accuracy.

## Setup

Python 3.11+ and PDFium are required. No paid model API is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r code/requirements.txt
.\.venv\Scripts\python.exe code/main.py
```

On Linux/macOS, use `.venv/bin/python` instead and install the Tesseract executable with English language data through your OS package manager. Windows uses its installed English OCR language pack and built-in Windows.Media.Ocr API; PowerShell 5.1 runs locally. Image-only PDFs are rendered before OCR. PDFium's wheel includes its native PDF library.

This session used MSYS Python 3.14: `.\.venv\bin\python.exe`. Network installation was blocked; an existing local PDFium 5.7.1 installation was copied into that isolated environment. Submitted code has no dependency on that installation path.

## Run

After installing requirements:

```powershell
python code/main.py
python code/main.py --strict
```

Default paths resolve relative to the repository, so the entry point also works from another directory. Options:

- `--dataset PATH`: participant data directory.
- `--requests PATH`: request CSV; defaults to deletion_requests.csv in the data directory.
- `--output PATH`: predictions; defaults to root output.csv.
- `--artifacts PATH`: timelines, policy diagnostics, coverage, document facts, validation and usage.
- `--cache PATH`: local content-addressed extraction/optional-model cache.
- `--strict`: writes artifacts and returns exit code 2 if any case is unresolved.

Output has exactly `case_id,deletion_status,steps_json`, one row per request, sorted by case_id. Complete cases contain cited verification only. Future actions/checks have empty evidence IDs. Non-deletion requests contain `[]`. Unproven completeness maps conservatively to INCOMPLETE and is explicitly diagnosed; these rows do not assert an observed violation. The default run prints the unresolved count. Strict mode rejects this fallback.

All 94 evidence files are parsed, including PDFs and PNGs. [The inventory](code/evaluation/evidence_inventory.md) lists every file, capture, schema and observation count. Business documents may supply facts without a safe canonical-resource association; extracted text and diagnostics preserve that distinction. Missing rows in partial exports never prove absence.

## Architecture

See [ARCHITECTURE.md](code/ARCHITECTURE.md). Modules under `code/auditor/` cover observations, adapters, OCR/PDF extraction, temporal identity, policy, dependency guards, optional intent interpretation, planning and validation.

There are no case-specific predictions, numeric-suffix identity joins, resource-prefix outcomes or production sample-answer lookups. Workflow/activity outcomes are claims. The supplied policy has 15 rules; the output contract defines 16 operations.

## Optional model fallback

The default uses language rules and local OCR. For ambiguous intent, configure an OpenAI-compatible chat endpoint through environment variables:

```text
AUDIT_MODEL_BASE_URL
AUDIT_MODEL_NAME
AUDIT_MODEL_PROVIDER
AUDIT_MODEL_API_KEY
```

Credentials are never logged. Responses require a boolean, exact supporting quote and explanation; they cannot establish resource state. Actual uncached calls and provider tokens are recorded. This optional network path was not integration-tested. The measured final run made no generative model calls. A separately measured development-session token snapshot is in the usage report; development billing cost is unavailable.

## Evaluate and test

```powershell
python code/evaluation/run_tests.py
python code/main.py --requests dataset/sample_deletion_requests.csv --output evaluation_artifacts/sample_predictions.csv --artifacts evaluation_artifacts/sample
python code/evaluation/main.py
python code/main.py
python code/evaluation/review.py
python code/evaluation/reports.py
python code/evaluation/package.py
python code/evaluation/review.py --archive code.zip
```

Only the evaluator reads sample_output.csv. Step comparison includes all seven fields; sequence comparison preserves order. Synthetic fixtures cover identity collisions, replica drift, recreation, backup blocking, conditional retention, tombstones, conflicting/missing evidence and multilingual intent. Metamorphic tests change case IDs, resource names, observation order and email case.

The independent artifact checker imports no inference code. It checks schemas, dataset preservation against committed Git hashes, recognizable inference-label leakage and archive safety. This is automated verification, not a separate human/LLM semantic review.

## Deliverables

- `output.csv`: every required request row.
- `code.zip`: source, dependencies, README and measured Markdown reports. Reports appear in both `code/evaluation/` and top-level `evaluation/` for compatibility with the repository's two packaging descriptions.
- `log.txt`: append-only development transcript, submitted separately.

The package excludes dataset, caches, source-record diagnostics, virtual environments, credentials, nested archives and bytecode. Rebuild with `python code/evaluation/package.py`. A package smoke test uses a fresh cache and the original read-only dataset outside the archive.

Challenge: https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists
