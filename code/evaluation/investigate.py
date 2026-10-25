"""Evaluation-only forensic comparison; production never imports sample labels."""
from __future__ import annotations
import collections
import csv
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auditor.ingest import EvidenceIndex
from auditor.model import rows, timestamp


def step_key(step):
    return tuple(step[k] for k in ['phase','system_id','resource_id','operation'])


def investigate(root):
    baseline=root/json.loads((root/'evaluation_artifacts/regression_baseline.json').read_text())['path']
    old_metrics=json.loads((baseline/'sample_metrics.json').read_text())
    old_predictions={r['case_id']:r for r in rows(baseline/'sample_predictions.csv')}
    old_traces=json.loads((baseline/'sample/case_traces.json').read_text(encoding='utf8'))
    expected={r['case_id']:r for r in rows(root/'dataset/sample_output.csv')}
    requests={r['case_id']:r for r in rows(root/'dataset/sample_deletion_requests.csv')}
    index=EvidenceIndex(root/'dataset',root/'.audit_cache').ingest()
    manifest={m['file_id']:m for m in index.manifest}
    documents={d['file_id']:'\n'.join(d.get('pages',[])) or d.get('extraction',{}).get('text','') for d in index.document_facts}
    raw={m['file_id']:documents.get(m['file_id'],'') if Path(m['file_path']).suffix in {'.pdf','.png'} else (root/'dataset'/m['file_path']).read_text(encoding='utf8') for m in index.manifest}
    positive_citation_gaps=[]
    for cid,row in expected.items():
        for step in json.loads(row['steps_json']):
            eid=step['evidence_id']
            if not eid or eid not in manifest:continue
            key=(step['system_id'],step['resource_id'])
            proved=[o for o in index.by_resource.get(key,[]) if o.evidence_id==eid and o.available(requests[cid]['audit_at']) and o.state==step['state']]
            literal=bool(re.search(r'(?<![\w])'+re.escape(step['resource_id'])+r'(?![\w])',raw[eid]))
            if not proved and not literal and step['state']!='ABSENT':
                positive_citation_gaps.append({'case_id':cid,'resource_id':step['resource_id'],'operation':step['operation'],'evidence_id':eid,'file_path':manifest[eid]['file_path'],'reason':'cited artifact has neither the named record nor a parsed explicit alias; positive state cannot be established by row omission'})
    cases=[];groups=collections.defaultdict(set)
    for mismatch in old_metrics['mismatches']:
        cid=mismatch['case_id'];at=requests[cid]['audit_at']
        e={step_key(s):s for s in json.loads(expected[cid]['steps_json'])}
        p={step_key(s):s for s in json.loads(old_predictions[cid]['steps_json'])}
        findings=[];case_groups=set()
        for key in sorted(e.keys()-p.keys()):
            step=e[key];resource_key=(step['system_id'],step['resource_id'])
            all_observations=index.by_resource.get(resource_key,[])
            timely=[o for o in all_observations if o.available(at)]
            if not all_observations:code='NO_RESOURCE_STATE_OBSERVATION'
            elif not timely:code='ONLY_LATE_CAPTURE_OR_OBSERVATION'
            elif step['phase']=='VERIFICATION':code='MISSING_GROUNDED_IDENTITY_EDGE'
            else:code='UNPROVEN_POLICY_CONDITION'
            case_groups.add(code)
            findings.append({'step':step,'root_cause':code,'timely_observations':[{'evidence_id':o.evidence_id,'state':o.state,'identifiers':o.identifiers,'observed_at':o.observed_at,'captured_at':o.captured_at,'provenance':o.provenance} for o in timely],
                'late_observations':[{'evidence_id':o.evidence_id,'observed_at':o.observed_at,'captured_at':o.captured_at} for o in all_observations if not o.available(at)],
                'cited_source_contains_resource_id':bool(re.search(r'(?<![\w])'+re.escape(step['resource_id'])+r'(?![\w])',raw.get(step['evidence_id'],''))) if step['evidence_id'] else None})
        extras=[p[key] for key in sorted(p.keys()-e.keys())]
        if extras:case_groups.add('ADDITIONAL_GROUNDED_RESOURCES')
        if any(e[key]['step_no']!=p[key]['step_no'] for key in e.keys()&p.keys()):case_groups.add('SEQUENCE_CASCADE')
        if any(e[key]['evidence_id']!=p[key]['evidence_id'] for key in e.keys()&p.keys()):case_groups.add('CONSERVATIVE_STATUS_CHANGES_CITATION_MODE')
        for code in case_groups:groups[code].add(cid)
        cases.append({'case_id':cid,'groups':sorted(case_groups),'baseline_uncertainties':old_traces[cid]['uncertainties'],'missing':findings,'additional':extras})
    report={'baseline_mismatches':len(cases),'group_case_counts':{k:len(v) for k,v in sorted(groups.items())},'cases':cases,'positive_citation_gaps':positive_citation_gaps}
    (root/'evaluation_artifacts/root_causes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Semantic root-cause investigation','',f"All {len(cases)} baseline mismatched public cases were investigated against participant-facing evidence. Expected rows are used only in this evaluation module; no associations or labels from this report enter production inference.",'',
      '## Root causes grouped across cases','', '| Cause | Baseline cases |','|---|---:|']
    lines += [f'| {code} | {count} |' for code,count in report['group_case_counts'].items()]
    lines += ['','Missing identity edges and unavailable observations are different failures. A zero-row read cannot be attached to a person by numeric suffix; an anonymized row cannot be assigned by list position or nearby activity. A later-captured bundle cannot prove earlier availability. Empty snapshot tables without an explicit exhaustive declaration are not global absence proofs.','',
      '## General fixes and evidence supporting them','',
      '- Relationship discovery: participant SQL search documents contain explicit source_resource_id references. Traverse typed same-subject resource references transitively, require an unambiguous timely system address, and reject contradictory owners. An edge proves association only, never state. Independent cleared-analytics and missing-profile fixtures exercise both outcomes.',
      '- Scope interpretation: participant SQL contains snapshot_scope(origin_system,captured_at), but no complete/exhaustive declaration. Preserve these scope times and keep completeness unspecified. Implement absence proofs only for explicitly complete JSON/SQL scopes with matching subject/category/location and a previously known resource. Test partial, wrong-subject, future and replica counterexamples.',
      '- State interpretation: correlated readback logs carry lookup parameters separately from returned fields. Preserve request context for identity, exclude it from returned-PII tests. Do not treat email_opt_in or generic non-empty message_text as identifiers; include tombstone name fields. Tests isolate these failure modes.',
      '- Support policy: real excerpts describe order/delivery queries; those establish business context. A bare message_pii_scan does not establish shared/agent/order context. Retain proven prior context with provenance without carrying historical PII into current state. An already-redacted record can be verified as redacted without asserting the condition that makes retention necessary; caveats remain explicit.',
      '- Retention/exclusivity: security record presence does not establish a supplied retention interval. Support intervals, aliases and explicit start/duration without inventing defaults. An uploader identity alone does not establish an attachment has only one subject. A retention date alone does not establish an active legal hold. These stricter checks can reduce agreement with underspecified sample annotations.',
      '- Completeness gate: some baseline COMPLETE outputs contain a retained security record or cleared support record without any observed account state. A clean known subset is not proof of the requested account deletion. Require a timely associated account readback/deleted-account marker, unless the source explicitly enumerates the complete subject inventory. Unit fixtures explicitly enumerate their isolated domain; the participant manifest does not.',
      '- Multimodal scoping: screenshots contain selected records, other rows and unrelated history. Retain whole-screen text as provenance but do not assign every identifier on the screen to each selected resource. Only row-level identifiers and explicit catalog associations contribute identity edges.',
      '- Optional model: no provider endpoint/model/credentials are configured. Mocked transport tests exercise grounded-output validation, caching, model revision, missing usage and accounting for invalid outputs. Mock outputs are not real-model predictions or accuracy measurements. No real-model accuracy/cost effect is claimed.','',
      '## Positive-state citation gaps in public annotations','',
      ('No unsupported positive-state citations were found. Some missing future verification targets have empty evidence IDs by contract; these are association/coverage gaps, not incorrect citations.' if not positive_citation_gaps else 'These require an explicit participant-visible alias/record or clarification. Positive existence/anonymization cannot be proved by omission.'),'',
      '| Case | Operation | Resource | Cited artifact |','|---|---|---|---|']
    for gap in positive_citation_gaps:lines.append(f"| {gap['case_id']} | {gap['operation']} | {gap['resource_id']} | {gap['evidence_id']}: {gap['file_path']} |")
    lines+=['','## Each baseline mismatch','']
    for case in cases:
        lines+=['### '+case['case_id'],'','Groups: '+', '.join(case['groups'])+'.','']
        for missing in case['missing']:
            step=missing['step'];lines.append(f"- Missing logical step: {step['operation']} / {step['system_id']} / {step['resource_id']}. Cause: {missing['root_cause']}.")
            for o in missing['timely_observations']:
                lines.append(f"  Evidence {o['evidence_id']} ({o['provenance']}): state={o['state']}, observed={o['observed_at']}, captured={o['captured_at']}, explicit identifier matches={o['identifiers'] or 'none'}. An unlinked cleared record remains unassigned.")
            for o in missing['late_observations']:
                lines.append(f"  Excluded {o['evidence_id']}: observed={o['observed_at']}, captured={o['captured_at']}; cutoff={requests[case['case_id']]['audit_at']}.")
            if not missing['timely_observations'] and not missing['late_observations']:lines.append('  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.')
        for extra in case['additional']:
            lines.append(f"- Additional supported step: {extra['operation']} / {extra['resource_id']} / evidence={extra['evidence_id'] or 'future check/action'}. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.")
        if case['baseline_uncertainties']:lines.append('Baseline policy/evidence gaps: '+'; '.join(case['baseline_uncertainties'])+'.')
        lines.append('')
    (root/'code/evaluation/root_cause_investigation.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'investigated_baseline_cases':len(cases),'root_cause_counts':report['group_case_counts'],'positive_citation_gaps':len(positive_citation_gaps)}))


if __name__=='__main__':investigate(Path(__file__).resolve().parents[2])
