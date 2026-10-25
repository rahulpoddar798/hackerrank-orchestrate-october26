# Runtime usage and cost report

This report describes the final run producing output.csv, SHA-256 `f322ddb74ff7ba25c2adc5a84e246972a8579e149280c14bbc302f5aaf292370`, over 518 requests.

| Provider | Exact runtime generative model | Actual calls | Input tokens | Output tokens | Total tokens | Estimated API cost |
|---|---|---:|---:|---:|---:|---:|
| None | None: deterministic audit pipeline | 0 | 0 | 0 | 0 | USD 0.00 |

Overall: 0 generative API calls. Total and average tokens per request: **0**. Estimated total and per-request API cost: **USD 0.00**.

Local extraction in this final run: 4 PDF documents; 0 fresh OCR calls; 11 content-addressed OCR cache hits. The initial cold extraction used the installed Microsoft Windows.Media.Ocr engine for 11 screenshots. Microsoft does not expose a model identifier or token accounting through this local API, so neither is invented. Local OCR has no paid API charge; compute/electricity costs are not estimated.

The optional OpenAI-compatible chat endpoint is disabled by default. AUDIT_MODEL_BASE_URL, AUDIT_MODEL_NAME and optional AUDIT_MODEL_PROVIDER/AUDIT_MODEL_API_KEY configure ambiguous-intent fallback. Uncached responses record provider-reported exact model and token counts. Cached responses do not count as new calls. No credentials are stored in artifacts.

Codex development-session usage is separate from runtime inference. The zero runtime figures do not claim zero development usage.

## Measured development-session snapshot

Source: Codex runtime token_count cumulative telemetry delta since master task. Exact model: `gpt-6.1-sol`. Snapshot: 2026-10-25T08:51:56.985Z; baseline immediately before master task: 2026-10-25T08:05:51.750Z.

| Metric | Runtime-reported development delta |
|---|---:|
| Input tokens (including cached input) | 9,816,303 |
| Cached input tokens (subset of input) | 9,477,120 |
| Output tokens (including reasoning) | 67,558 |
| Reasoning output tokens (subset of output) | 22,449 |
| Total input + output tokens | 9,883,861 |

These are authoritative cumulative Codex telemetry differences at the stated snapshot, not billing estimates and not a final end-of-turn total. Later report/packaging/chat activity is excluded. Development model-call counts and billing costs were not measured; neither is fabricated. Cached and reasoning subset counters are not added again to totals.
