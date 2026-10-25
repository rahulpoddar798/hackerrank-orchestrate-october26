"""Measured before/after history and exact unresolved reasons, evaluation only."""
import collections
import hashlib
import json
import os
import re
from datetime import datetime,timezone
from pathlib import Path


def generate(root):
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    baseline=root/read(root/'evaluation_artifacts/regression_baseline.json')['path']
    before=read(baseline/'sample_metrics.json');after=read(root/'evaluation_artifacts/sample_metrics.json')
    old_full=read(baseline/'full/run.json');new_full=read(root/'evaluation_artifacts/full/run.json')
    traces=read(root/'evaluation_artifacts/full/case_traces.json')
    reasons=collections.defaultdict(set);resources=collections.defaultdict(set);cases=[]
    for cid,trace in sorted(traces.items()):
        if not trace['uncertainties']:continue
        detailed=[]
        for message in trace['uncertainties']:
            match=re.search(r'\b([A-Z][A-Z_]+):',message)
            code=match[1] if match else ('RESOURCE_STATE_MISSING' if 'no state observation' in message else 'UNRESOLVED_EVIDENCE')
            reasons[code].add(cid);detailed.append({'code':code,'reason':message})
        for gap in trace.get('policy_gaps',[]):
            for code in re.findall(r'\b([A-Z][A-Z_]+):',gap['reason']):resources[code].add((gap['system_id'],gap['resource_id']))
        cases.append({'case_id':cid,'reasons':detailed,'policy_gaps':trace.get('policy_gaps',[])})
    summary={'unresolved_cases':len(cases),'case_counts_by_reason':{k:len(v) for k,v in sorted(reasons.items())},'resource_counts_by_reason':{k:len(v) for k,v in sorted(resources.items())},'cases':cases}
    (root/'evaluation_artifacts/unresolved_reasons.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    model_configuration={key:bool(os.environ.get(key)) for key in ['AUDIT_MODEL_BASE_URL','AUDIT_MODEL_NAME','AUDIT_MODEL_API_KEY']}
    model={'live_provider_available':all(model_configuration[k] for k in ['AUDIT_MODEL_BASE_URL','AUDIT_MODEL_NAME']),'configuration_presence':model_configuration,'confirmed_live_calls':len(new_full['runtime_model_calls']),'live_accuracy_effect':'not measured: no configured live provider','mock_tests':'transport/schema/cache/usage contract tests only; not real model calls or accuracy measurements'}
    (root/'evaluation_artifacts/model_path_status.json').write_text(json.dumps(model,indent=2),encoding='utf8')
    lines=['# Semantic improvement regression history','',f'Baseline source and reports are preserved at `{baseline.relative_to(root).as_posix()}`. Participant data was not copied into that snapshot or changed.','',
      '| Metric | Baseline | Current |','|---|---:|---:|']
    for label,key in [('Status accuracy','status_accuracy'),('Exact case accuracy (historical baseline equals sequence)','exact_case_accuracy'),('Sequence accuracy','sequence_accuracy'),('Exact step precision','step_precision'),('Exact step recall','step_recall'),('Field accuracy','field_accuracy')]:
        lines.append(f"| {label} | {before.get(key,before['sequence_accuracy']):.4%} | {after.get(key,after['sequence_accuracy']):.4%} |")
    lines += [f"| Exact steps matched | {before['exact_steps_matched']}/{before['expected_steps']} | {after['exact_steps_matched']}/{after['expected_steps']} |",f"| Unresolved full-dataset audits | {old_full['unresolved_cases']}/{old_full['requests']} | {new_full['unresolved_cases']}/{new_full['requests']} |",'',
      '**Quality gate remains NOT acceptance-complete.** Stricter condition checks remove unsupported redaction/deletion inferences; lower sample agreement is reported rather than concealed. The new relationship/scope algorithms succeed on independently specified proof fixtures but cannot create associations or completeness declarations absent from the supplied data.','',
      '## Exact reasons remaining','',
      'Case counts overlap when one case has several missing conditions. Resource counts deduplicate known policy resource IDs across physical copies; account-coverage gaps have no grounded resource address to count. No reduction is claimed from merely deduplicating diagnostics.','', '| Reason | Cases | Known distinct policy resource IDs |','|---|---:|---:|']
    for code,count in summary['case_counts_by_reason'].items():lines.append(f"| {code} | {count} | {summary['resource_counts_by_reason'].get(code,0)} |")
    lines += ['','## Optional model path','',
      f"Configured live provider available: {model['live_provider_available']}. Confirmed generative calls in the final dataset run: {model['confirmed_live_calls']}. No credentials were printed or stored. Transport/schema/caching/usage tests use controlled mocked responses; their tokens are fixture values and are not reported as runtime model usage. Live-model accuracy and cost effects are unmeasured. Runtime generative API cost remains USD 0.00 because no live calls occurred.",'',
      '## Remaining sample regressions','',
      'Compare root_cause_investigation.md and the evaluation report. The retained baseline lets every changed step be audited. No public expected row or case-specific mapping is read by inference.','',
      '## Every unresolved full-dataset case','', '| Case | Exact diagnosed reasons |','|---|---|']
    for case in cases:lines.append('| '+case['case_id']+' | '+'; '.join(item['reason'].replace('|','/') for item in case['reasons'])+' |')
    (root/'code/evaluation/semantic_regression_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    history=root/'code/evaluation/regression_history.md'
    if not history.exists():
        history.write_text('# Regression measurements (append only)\n\n| Version | Status | Exact case/sequence | Step precision | Step recall | Field | Unresolved | Output SHA-256 |\n|---|---:|---:|---:|---:|---:|---:|---|\n'+f"| baseline | {before['status_accuracy']:.4%} | {before['sequence_accuracy']:.4%} | {before['step_precision']:.4%} | {before['step_recall']:.4%} | {before['field_accuracy']:.4%} | {old_full['unresolved_cases']} | {old_full['output_sha256']} |\n",encoding='utf8')
    signature=hashlib.sha256(json.dumps([after,new_full['output_sha256']],sort_keys=True).encode()).hexdigest()[:12]
    version='semantic-'+signature
    if version not in history.read_text(encoding='utf8'):
        with history.open('a',encoding='utf8') as f:f.write(f"| {version} | {after['status_accuracy']:.4%} | {after['sequence_accuracy']:.4%} | {after['step_precision']:.4%} | {after['step_recall']:.4%} | {after['field_accuracy']:.4%} | {new_full['unresolved_cases']} | {new_full['output_sha256']} |\n")
    print(json.dumps({'before_status':before['status_accuracy'],'after_status':after['status_accuracy'],'before_exact':before['exact_sequences'],'after_exact':after['exact_sequences'],'unresolved':summary['unresolved_cases'],'reasons':summary['case_counts_by_reason'],'live_model_available':model['live_provider_available']}))


if __name__=='__main__':generate(Path(__file__).resolve().parents[2])
