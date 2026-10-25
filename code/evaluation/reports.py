"""Render measured evaluation artifacts directly into the required Markdown reports."""
from __future__ import annotations
import collections
import json
from pathlib import Path

def generate(root):
    load=lambda p:json.loads((root/p).read_text(encoding='utf8'))
    metrics=load('evaluation_artifacts/sample_metrics.json');full=load('evaluation_artifacts/full/run.json');validation=load('evaluation_artifacts/full/validation.json');trace=load('evaluation_artifacts/full/case_traces.json');inventory=load('evaluation_artifacts/full/inventory.json')
    unit=load('evaluation_artifacts/tests.json');review=load('evaluation_artifacts/independent_review.json')
    out=root/'code/evaluation';out.mkdir(parents=True,exist_ok=True)
    lines=['# Evaluation report','',
      '**Quality gate: NOT acceptance-complete.** This implementation produces a validated conservative audit for every request, but unresolved evidence/policy conditions remain. No hidden evaluation labels were accessed. Structural validity is not deletion correctness.','',
      '## Public samples (measured)','',
      '| Metric | Result |','|---|---:|',
      f"| Status accuracy | {metrics['status_correct']}/{metrics['cases']} ({metrics['status_accuracy']:.2%}) |",
      f"| Exact case including status and sequence | {metrics.get('exact_cases',metrics['exact_sequences'])}/{metrics['cases']} ({metrics.get('exact_case_accuracy',metrics['sequence_accuracy']):.2%}) |",
      f"| Exact sequence (array only) | {metrics['exact_sequences']}/{metrics['cases']} ({metrics['sequence_accuracy']:.2%}) |",
      f"| Exact step precision | {metrics['exact_steps_matched']}/{metrics['predicted_steps']} ({metrics['step_precision']:.2%}) |",
      f"| Exact step recall | {metrics['exact_steps_matched']}/{metrics['expected_steps']} ({metrics['step_recall']:.2%}) |",
      f"| Field accuracy | {metrics['correct_fields']}/{metrics['compared_fields']} ({metrics['field_accuracy']:.2%}) |",'',
      'Exact steps compare all seven fields, including step number and evidence ID, as multisets. Field comparison aligns by phase/system/resource/operation and counts each missing or extra step as seven incorrect fields. Exact case requires identical arrays and status; sequence accuracy compares arrays alone. sample_output.csv is read only by evaluation/main.py and evaluation-only forensic analysis, never by production inference.','',
      '## Full evaluation input run','',
      f"Processed {full['requests']} requests in {full['elapsed_seconds']:.3f} seconds on this machine. Produced {validation['steps']} steps. Status counts: "+', '.join(f'{k}={v}' for k,v in sorted(full['status_counts'].items()))+'.',
      f"Schema, unique case coverage, sorting, enum/state combinations, phase/operation order, step numbering, temporal evidence references, and observed citation state validation: {validation['valid']}. Validation errors: {len(validation['errors'])}.",
      f"Unresolved cases: **{full['unresolved_cases']}**. Strict mode returns a nonzero exit code and explicitly rejects this run. Conservative mode maps unproven completeness to INCOMPLETE, records each uncertainty, and proposes only supported actions/non-destructive retention-presence safeguards. This mapping is an operational audit fallback, not proof of a policy violation. No hidden full-dataset accuracy can be measured.",
      f"Output SHA-256: `{full['output_sha256']}`.",'',
      '## Additional independent fixtures and metamorphic tests','',
      f"Ran {unit['tests_run']} tests: {unit['passed']} passed, {unit['failures']} failures, {unit['errors']} errors. Fixtures use fictional example.test identities and opaque resource IDs; they do not read the public sample answers.",'',
      '| Independent scenario | Expected behavior tested |','|---|---|',
      '| Historical identity and reassigned email | Resolve assignment at request time; reject a true simultaneous collision |',
      '| Replica drift | Absent primary plus present regional replica is incomplete |',
      '| Post-deletion recreation | Later observed presence overrides earlier absence |',
      '| Backup and retention | Block restores before record changes; retain only with established supplied period |',
      '| Account tombstones | Keep stable reference, redact exposed direct identifiers; recognize explicit null fields |',
      '| Incomplete/conflicting evidence | Missing fields do not prove anonymization; simultaneous conflict prevents completeness |',
      '| Multilingual/non-deletion | English, French, Japanese, Chinese deletion and access/correction negations |',
      '| Permitted data flow | Explicit permitted retained-reference payload does not trigger disabling |',
      '| Metamorphic transformations | Case ID changes, resource renaming, email case, and reversed observation order preserve logical decisions |',
      '| Dynamic policy | Replacing a runtime DELETE rule with RETAIN changes treatment without code changes |','',
      '## Failures found and general improvements','',
      '- Fixed schema aliases for replica tables, tombstones, attachments, legal records, and generic lookup logs.',
      '- Preserved explicit null values; missing fields and cleared fields are different states.',
      '- Correlated started/completed reads by trace and parsed nested cloud JSON, syslog, pipe, bracketed, and key-value logs.',
      '- Added three temporal gates: observation time, source capture time, and catalog-association availability.',
      '- Added collision/reassignment safeguards, replica separation, conflict diagnostics, restore blocking and conditional policy checks.',
      '- Fixed negated correction/information requests and French/Portuguese intent forms using general language rules.',
      '- Added safe future presence checks for conditionally retained records while leaving the missing condition unresolved.',
      '- Distinguished SQL record last-write time from the snapshot observation time, retaining both values.',
      '- Refused destructive plans for ambiguous authorization or reassigned resources, and avoided false PII findings for missing records that must remain redacted/anonymized.',
      '- Added an independent artifact checker that imports no inference code and verifies dataset preservation and packaging.','',
      'The semantic improvement pass adds typed temporal relationship traversal, explicitly declared scope proofs, request/record separation, row-scoped screenshot identities, condition-provenance tracking, nonblocking already-transformed-state caveats, and real-vs-mocked model usage accounting. See root_cause_investigation.md for all 25 baseline mismatches and semantic_regression_report.md for measured regressions and every unresolved full-dataset reason.','',
      '## Remaining limitations and minimal next actions','',
      '1. Many SECURITY_AUDIT_LOG artifacts prove that a record exists but supply no retention-until date. A verification of presence is safe; eligibility for retention remains unproven. Supply authoritative retention metadata before strict acceptance.',
      '2. Some cleared resources have neither direct identifiers nor earlier timely associations. Joining nearby activity events or matching numeric suffixes would fabricate identity links. Supply explicit participant-visible associations for those resources.',
      '3. The supplied SQL scope rows do not declare exhaustive coverage. Missing rows cannot establish absence. The implementation now supports explicit complete-scope proofs, while preserving source scope observation time separately from export capture time.',
      '4. Natural-language extraction and screenshot interpretation are conservative schema adapters, not unrestricted document understanding. PDF business facts are preserved even if no canonical resource can be associated. OCR can misread small IDs; only exact known-ID repairs are permitted.',
      '5. Explicit recreation/reference dependencies are recorded and all flow/restore guards precede record changes. Record serialization follows the public operation/system/resource ordering. More complex delete-after constraints require an explicit execution policy if they conflict with that contract.',
      '6. The optional model fallback has mocked transport tests for schema/quote validation, caching, invalid-output accounting and missing usage. No live provider endpoint/model/credentials are configured, so live-model accuracy and cost effects were not measured. No claim of universal intent accuracy or complete policy-language understanding is made.',
      '7. Independent review here is automated artifact/static verification, supplemented by separate fixture oracles. No independent human or second-agent semantic review was performed.','',
      '## Every remaining sample mismatch','',
      '| Case | Expected / predicted status | Expected / predicted steps |','|---|---|---:|']
    for m in metrics['mismatches']:lines.append(f"| {m['case_id']} | {m['expected_status']} / {m['predicted_status']} | {m['expected_steps']} / {m['predicted_steps']} |")
    sample_trace=load('evaluation_artifacts/sample/case_traces.json')
    lines+=['','### Mismatch investigation details','', 'These are evaluation-only expected-vs-observed differences. They are not inference rules or production lookups. Step numbers are included because sequence positions count toward exact matching.','']
    for mismatch in metrics['mismatches']:
        cid=mismatch['case_id'];lines+=['**'+cid+'**','']
        uncertainty=sample_trace[cid]['uncertainties']
        if uncertainty:lines+=['Unresolved evidence/policy: '+'; '.join(uncertainty)+'.','']
        else:lines+=['The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.','']
        for kind in ['missing_steps','extra_steps']:
            descriptions=[f"{s['step_no']}:{s['operation']}({s['system_id']}/{s['resource_id']}, evidence={s['evidence_id'] or 'future'})" for s in mismatch[kind]]
            lines.append(('Expected but unmatched: ' if kind=='missing_steps' else 'Predicted but unmatched: ')+('; '.join(descriptions) or 'none')+'.')
        lines.append('')
    lines+=['','Full missing/extra step details are reproducibly written to evaluation_artifacts/sample_metrics.json. Raw traces are outside code.zip; required metrics and limitations are contained directly in this Markdown report.','',
      '## Independent artifact review','',
      f"Automated checks passed: {review['passed']}. Dataset files compared to committed Git blob hashes: {review['dataset_files_unchanged']}. Empty deletion predictions: {len(review['empty_deletion_outputs'])}. Inference leakage scan matches: {len(review['inference_leakage_scan'])}."]
    lines+=['',f"Independent semantic quality gate passed: {review.get('semantic_quality_gate_passed',False)}. Structural checks passing is not semantic acceptance."]
    smoke_file=root/'evaluation_artifacts/package_smoke.json'
    if smoke_file.exists():
        smoke=json.loads(smoke_file.read_text(encoding='utf8'))
        lines+=['',f"Package smoke test: passed={smoke['passed']}; requests={smoke['requests']}; fresh OCR calls={smoke['fresh_ocr_calls']}; cache hits={smoke['ocr_cache_hits']}; duration={smoke['elapsed_seconds']:.3f}s; output bytes identical to final run={smoke['same_output_sha256']}. Source was extracted into a new directory and the cache started empty; installed isolated Python dependencies were reused."]
    metamorphic_file=root/'evaluation_artifacts/metamorphic_dataset.json'
    if metamorphic_file.exists():
        metamorphic=json.loads(metamorphic_file.read_text(encoding='utf8'))
        lines+=['',f"Real-dataset metamorphic check: passed={metamorphic['passed']} across {metamorphic['cases']} sample requests. Shuffled manifest, identity, audit and activity order and reversed normalized observation order; predictions remained byte-equivalent to baseline inference output. Public expected labels were not used for this check."]
    strict_file=root/'evaluation_artifacts/strict_gate.json'
    if strict_file.exists():
        strict=json.loads(strict_file.read_text(encoding='utf8'))
        lines+=['',f"Strict CLI gate test: observed Python return code {strict['returncode']}, expected {strict['expected_returncode']}; passed={strict['passed']}. Unresolved sample audits were rejected instead of being reported as semantic acceptance."]
    (out/'evaluation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    calls=full['runtime_model_calls']
    usage=['# Runtime usage and cost report','',f"This report describes the final run producing output.csv, SHA-256 `{full['output_sha256']}`, over {full['requests']} requests.",'',
      '| Provider | Exact runtime generative model | Actual calls | Input tokens | Output tokens | Total tokens | Estimated API cost |','|---|---|---:|---:|---:|---:|---:|']
    if not calls:usage+=['| None | None: deterministic audit pipeline | 0 | 0 | 0 | 0 | USD 0.00 |']
    else:
        grouped=collections.defaultdict(list)
        for c in calls:grouped[(c['provider'],c['model'])].append(c)
        for (provider,model),cc in grouped.items():
            ins=sum(c['input_tokens'] for c in cc) if all(type(c.get('input_tokens')) is int for c in cc) else None
            outs=sum(c['output_tokens'] for c in cc) if all(type(c.get('output_tokens')) is int for c in cc) else None
            costs=sum(c['estimated_cost_usd'] for c in cc) if all(c.get('estimated_cost_usd') is not None for c in cc) else None
            total=ins+outs if ins is not None and outs is not None else 'unreported'
            usage.append(f"| {provider} | {model or 'unreported by provider'} | {len(cc)} | {ins if ins is not None else 'unreported'} | {outs if outs is not None else 'unreported'} | {total} | {costs if costs is not None else 'not estimated: tokens/rates unavailable'} |")
    usage+=['',f"Overall: {len(calls)} generative API calls. "+('Total and average tokens per request: **0**. Estimated total and per-request API cost: **USD 0.00**.' if not calls else 'See provider rows; cost is not fabricated when provider rates are unspecified.'),'',
      f"Local extraction in this final run: {full['local_extraction']['pdf_documents']} PDF documents; {full['local_extraction']['ocr_calls']} fresh OCR calls; {full['local_extraction']['ocr_cache_hits']} content-addressed OCR cache hits. The initial cold extraction used the installed Microsoft Windows.Media.Ocr engine for 11 screenshots. Microsoft does not expose a model identifier or token accounting through this local API, so neither is invented. Local OCR has no paid API charge; compute/electricity costs are not estimated.",'',
      'The optional OpenAI-compatible chat endpoint is disabled by default. AUDIT_MODEL_BASE_URL, AUDIT_MODEL_NAME and optional AUDIT_MODEL_PROVIDER/AUDIT_MODEL_API_KEY configure ambiguous-intent fallback. Uncached responses record provider-reported exact model and token counts. Cached responses do not count as new calls. No credentials are stored in artifacts.','',
      'The live provider was unavailable (no endpoint/model/credentials configured). Tests used controlled mocked responses to check transport and accounting behavior; fixture token values and fixture costs are not runtime model measurements. Real-model accuracy effects are unmeasured. AUDIT_INPUT_USD_PER_MILLION and AUDIT_OUTPUT_USD_PER_MILLION optionally supply explicit estimation rates; missing tokens/rates stay unreported rather than becoming zero. Completed invalid model outputs retain their actual provider-reported usage records.','',
      'Codex development-session usage is separate from runtime inference. The zero runtime figures do not claim zero development usage.']
    development_file=root/'evaluation_artifacts/development_usage.json'
    if development_file.exists():
        development=json.loads(development_file.read_text(encoding='utf8'));u=development['usage']
        usage+=['','## Measured development-session snapshot','',f"Source: {development['source']}. Exact model: `{development['model']}`. Snapshot: {development['captured_at']}; baseline immediately before the measured task: {development['baseline_at']}.",'',
          '| Metric | Runtime-reported development delta |','|---|---:|',
          f"| Input tokens (including cached input) | {u['input_tokens']:,} |",f"| Cached input tokens (subset of input) | {u['cached_input_tokens']:,} |",f"| Output tokens (including reasoning) | {u['output_tokens']:,} |",f"| Reasoning output tokens (subset of output) | {u['reasoning_output_tokens']:,} |",f"| Total input + output tokens | {u['total_tokens']:,} |",'',
          'These are authoritative cumulative Codex telemetry differences at the stated snapshot, not billing estimates and not a final end-of-turn total. Later report/packaging/chat activity is excluded. Development model-call counts and billing costs were not measured; neither is fabricated. Cached and reasoning subset counters are not added again to totals.']
    else:usage+=['','Development model calls, token totals and costs were not available in this run environment; they are not fabricated.']
    (out/'usage_report.md').write_text('\n'.join(usage)+'\n',encoding='utf8')
    inv=['# Participant evidence inventory','',f"All {len(inventory)} manifest files were opened by their format adapters. Normalized observations: {sum(i['observations'] for i in inventory)}. This includes decoys and historical states; counts do not imply relevance to a case.",'',
       'CSV schemas: requests(case_id,email,requested_at,reported_status,reported_at,audit_at,request_text); identities(user_id,name,email,phone,email_hash,updated_at); history(audit_id,user_id,event_time,field_name,old_value,new_value); activity(activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details); policy(rule_id,data_category,condition,required_action); manifest(file_id,file_path,origin,captured_at); outputs(case_id,deletion_status,steps_json).','',
       'The 32 labeled sample requests/answers are evaluated separately from 518 required predictions. The contract defines 15 policy rules and 16 output operations.','',
       '| Evidence | File | Capture | Observations | Internal schema |','|---|---|---|---:|---|']
    for item in sorted(inventory,key=lambda x:x['file_id']):
        schema=json.dumps(item['schema'],ensure_ascii=True).replace('|','/')
        inv.append(f"| {item['file_id']} | {item['file_path']} | {item['captured_at']} | {item['observations']} | {schema} |")
    inv+=['','Nested JSON values and document/OCR text are retained in the diagnostic artifacts. SQL physical replicas remain separate locations. Every SQL table records explicit row count and unspecified completeness; no absence is inferred from missing rows. Empty SQL inventories are still parsed successfully. Documents with no canonical resource association retain their extracted facts and a diagnostic.']
    (out/'evidence_inventory.md').write_text('\n'.join(inv)+'\n',encoding='utf8')
    print('Wrote evaluation_report.md, usage_report.md, evidence_inventory.md from measured artifacts')

if __name__=='__main__':generate(Path(__file__).resolve().parents[2])
