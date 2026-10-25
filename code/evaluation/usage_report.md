# Runtime usage and cost report

This report describes the final run producing output.csv, SHA-256 `c1ff20ee736145f512e4fa52febf2c134d4cb6a2d238958b8bff7a5c1e865081`, over 518 requests.

| Provider | Exact runtime generative model | Actual calls | Input tokens | Output tokens | Total tokens | Estimated API cost |
|---|---|---:|---:|---:|---:|---:|
| None | None: deterministic audit pipeline | 0 | 0 | 0 | 0 | USD 0.00 |

Overall: 0 generative API calls. Total and average tokens per request: **0**. Estimated total and per-request API cost: **USD 0.00**.

Local extraction in this final run: 4 PDF documents; 0 fresh OCR calls; 11 content-addressed OCR cache hits. The initial cold extraction used the installed Microsoft Windows.Media.Ocr engine for 11 screenshots. Microsoft does not expose a model identifier or token accounting through this local API, so neither is invented. Local OCR has no paid API charge; compute/electricity costs are not estimated.

The optional OpenAI-compatible chat endpoint is disabled by default. AUDIT_MODEL_BASE_URL, AUDIT_MODEL_NAME and optional AUDIT_MODEL_PROVIDER/AUDIT_MODEL_API_KEY configure ambiguous-intent fallback. Uncached responses record provider-reported exact model and token counts. Cached responses do not count as new calls. No credentials are stored in artifacts.

The live provider was unavailable (no endpoint/model/credentials configured). Tests used controlled mocked responses to check transport and accounting behavior; fixture token values and fixture costs are not runtime model measurements. Real-model accuracy effects are unmeasured. AUDIT_INPUT_USD_PER_MILLION and AUDIT_OUTPUT_USD_PER_MILLION optionally supply explicit estimation rates; missing tokens/rates stay unreported rather than becoming zero. Completed invalid model outputs retain their actual provider-reported usage records.

Codex development-session usage is separate from runtime inference. The zero runtime figures do not claim zero development usage.

## Measured development-session snapshot

Source: Codex runtime token_count cumulative telemetry delta since semantic-improvement request. Exact model: `gpt-6.1-sol`. Snapshot: 2026-10-25T09:54:50.607Z; baseline immediately before the measured task: 2026-10-25T09:03:38.253Z.

| Metric | Runtime-reported development delta |
|---|---:|
| Input tokens (including cached input) | 8,212,466 |
| Cached input tokens (subset of input) | 8,175,104 |
| Output tokens (including reasoning) | 66,559 |
| Reasoning output tokens (subset of output) | 41,802 |
| Total input + output tokens | 8,279,025 |

These are authoritative cumulative Codex telemetry differences at the stated snapshot, not billing estimates and not a final end-of-turn total. Later report/packaging/chat activity is excluded. Development model-call counts and billing costs were not measured; neither is fabricated. Cached and reasoning subset counters are not added again to totals.
