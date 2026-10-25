"""Independent artifact checker: deliberately imports no inference implementation."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

OPERATIONS=[['REPORT_REMAINING_RECORD','REPORT_EXPOSED_PII','REPORT_ACTIVE_DATA_FLOW','REPORT_RESTORE_RISK'],['DISABLE_DATA_FLOW','BLOCK_RESTORE','DELETE_RECORD','REDACT_RECORD','ANONYMIZE_RECORD'],['VERIFY_RECORD_ABSENT','VERIFY_RECORD_PRESENT','VERIFY_RECORD_REDACTED','VERIFY_RECORD_ANONYMIZED','VERIFY_DATA_FLOW_DISABLED','VERIFY_RESTORE_BLOCKED']]
PHASES=['FINDING','REMEDIATION','VERIFICATION']
STATES=['PRESENT','PRESENT','ACTIVE','ACTIVE','DISABLED','BLOCKED','ABSENT','REDACTED','ANONYMIZED','ABSENT','PRESENT','REDACTED','ANONYMIZED','DISABLED','BLOCKED']
def load(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def review(root,archive=None):
    errors=[]
    output=load(root/'output.csv'); requests=load(root/'dataset/deletion_requests.csv')
    if [r['case_id'] for r in output]!=sorted(r['case_id'] for r in requests):errors.append('case coverage/order')
    cutoffs={r['case_id']:r['audit_at'] for r in requests}
    evidence={r['file_id']:r['captured_at'] for r in load(root/'dataset/evidence_files.csv')}
    evidence.update({r['activity_id']:r['event_time'] for r in load(root/'dataset/system_activity.csv')})
    evidence.update({r['audit_id']:r['event_time'] for r in load(root/'dataset/user_audit_log.csv')})
    state_map=dict(zip(sum(OPERATIONS,[]),STATES));steps_count=0;empty_deletions=[]
    for row in output:
        cid=row['case_id'];status=row['deletion_status'];steps=json.loads(row['steps_json'])
        if list(row)!=['case_id','deletion_status','steps_json']:errors.append(cid+': header')
        if status=='NOT_APPLICABLE' and steps:errors.append(cid+': non-deletion steps')
        if status!='NOT_APPLICABLE' and not steps:empty_deletions.append(cid)
        order=[]
        for number,s in enumerate(steps,1):
            steps_count+=1
            if set(s)!={'step_no','phase','system_id','resource_id','operation','state','evidence_id'}:errors.append(cid+': fields')
            if s['step_no']!=number or state_map.get(s['operation'])!=s['state']:errors.append(cid+': enum/number')
            phase=PHASES.index(s['phase']);order.append((phase,OPERATIONS[phase].index(s['operation']),s['system_id'],s['resource_id']))
            required=status=='COMPLETE' or s['phase']=='FINDING'
            if required:
                if s['evidence_id'] not in evidence or evidence[s['evidence_id']]>cutoffs[cid]:errors.append(cid+': citation/cutoff')
            elif s['evidence_id']:errors.append(cid+': future-action citation')
            if status=='COMPLETE' and s['phase']!='VERIFICATION':errors.append(cid+': complete-phase')
        if order!=sorted(order):errors.append(cid+': step order')
    # Compare Git's committed dataset blob hashes; this is read-only and uses no labels.
    git=subprocess.run(['git','ls-files','-s','--','dataset'],cwd=root,capture_output=True,text=True)
    checked=0
    if git.returncode==0:
        for line in git.stdout.splitlines():
            metadata,name=line.split('\t',1);expected=metadata.split()[1];data=(root/name).read_bytes()
            actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();checked+=1
            if actual!=expected:errors.append('Dataset changed: '+name)
    leakage=[]
    for p in (root/'code/auditor').glob('*.py'):
        if re.search(r'\b(?:case|user|account|evidence)_[0-9]+\b',p.read_text(encoding='utf8')):leakage.append(str(p.relative_to(root)))
        if 'sample_output.csv' in p.read_text(encoding='utf8'):leakage.append(str(p.relative_to(root)))
    if leakage:errors.append('Potential inference label leakage: '+str(leakage))
    archive_files=[]
    if archive:
        with zipfile.ZipFile(archive) as z:
            archive_files=z.namelist()
            for name in archive_files:
                parts=Path(name).parts
                if any(p in {'dataset','.venv','__pycache__','.audit_cache','.git','node_modules'} for p in parts) or Path(name).suffix.lower() in {'.zip','.gz','.tgz','.tar','.7z','.rar','.pyc'} or Path(name).name=='.env':errors.append('Forbidden archive entry: '+name)
                if name.startswith(('/','\\')) or '..' in parts:errors.append('Unsafe archive path')
            for name in ['README.md','code/main.py','code/evaluation/evaluation_report.md','code/evaluation/usage_report.md','evaluation/evaluation_report.md','evaluation/usage_report.md']:
                if name not in archive_files:errors.append('Missing archive item: '+name)
            if z.testzip():errors.append('Archive CRC error')
    return {'passed':not errors,'errors':errors,'cases':len(output),'steps':steps_count,'dataset_files_unchanged':checked,'inference_leakage_scan':leakage,'empty_deletion_outputs':empty_deletions,'archive_entries':len(archive_files),'review_type':'independent automated artifact/static checks; not a separate human or LLM code review'}

def main():
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path);a=p.parse_args()
    result=review(root,a.archive);out=root/'evaluation_artifacts/independent_review.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
