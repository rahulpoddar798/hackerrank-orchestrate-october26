# Commands executed during implementation

Commands below ran from the repository root. MSYS Python created `.venv/bin/python.exe`; on a standard Windows Python installation the corresponding interpreter is `.venv/Scripts/python.exe`.

```powershell
python -m venv .venv
.\.venv\bin\python.exe code\evaluation\run_tests.py
.\.venv\bin\python.exe code\main.py --requests dataset\sample_deletion_requests.csv --output evaluation_artifacts\sample_predictions.csv --artifacts evaluation_artifacts\sample
.\.venv\bin\python.exe code\evaluation\main.py
.\.venv\bin\python.exe code\main.py
.\.venv\bin\python.exe code\main.py --strict
.\.venv\bin\python.exe code\evaluation\review.py
.\.venv\bin\python.exe code\evaluation\reports.py
.\.venv\bin\python.exe code\evaluation\package.py
.\.venv\bin\python.exe code\evaluation\smoke.py
.\.venv\bin\python.exe code\evaluation\review.py --archive code.zip
```

Additional checks executed via short Python/PowerShell scripts: all CSV schemas and sample rows, JSON schema inventory, all SQL tables, all log event layouts, PDF text extraction and page rendering, local screenshot OCR, dataset Git blob hashes, case/manifest/identity/activity/observation-order metamorphic checks, Python return-code verification for strict mode, archive inspection and byte-identical fresh-cache package execution.

Dependency installation from the network was blocked. PDFium 5.7.1 was available in an existing local Python installation and copied into the isolated environment. The documented pip install command is for a clean environment and was not successfully executed here. No generative API was called.

The semantic improvement turn additionally executed:

```powershell
.\.venv\bin\python.exe code\evaluation\investigate.py
.\.venv\bin\python.exe code\evaluation\semantic_report.py
```

All 32 samples and 518 required requests were rerun, followed by the independent fixture suite, shuffled-input metamorphic comparison, strict return-code test, archive review, and fresh-cache packaged full-dataset execution. Mocked model transport tests are not live provider calls.
