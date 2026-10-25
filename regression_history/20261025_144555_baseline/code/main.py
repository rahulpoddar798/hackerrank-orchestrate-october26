"""Run from any directory: python code/main.py --dataset dataset --output output.csv."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from auditor.ingest import EvidenceIndex
from auditor.engine import AuditEngine
from auditor.model import rows
from auditor.validate import validate_output
from auditor.documents import STATS

def run(dataset,requests,output,artifacts,cache):
    started=time.perf_counter()
    for key in STATS:STATS[key]=0
    index=EvidenceIndex(dataset,cache).ingest()
    engine=AuditEngine(index,rows(dataset/'deletion_rules.csv'))
    request_rows=rows(requests)
    predictions=[engine.audit(r) for r in sorted(request_rows,key=lambda r:r['case_id'])]
    validation=validate_output(predictions,request_rows,index,engine.case_traces)
    if not validation['valid']: raise ValueError(json.dumps(validation))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['case_id','deletion_status','steps_json']);writer.writeheader();writer.writerows(predictions)
    artifacts.mkdir(parents=True,exist_ok=True)
    for name,obj in [('validation',validation),('inventory',index.inventory),('ingestion_diagnostics',index.diagnostics),('coverage',index.coverage),('document_facts',index.document_facts),('case_traces',engine.case_traces)]:
        (artifacts/(name+'.json')).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
    usage={'runtime_model_calls':engine.intent.usage,'local_extraction':dict(STATS),'requests':len(request_rows),'elapsed_seconds':round(time.perf_counter()-started,3),'status_counts':dict(Counter(p['deletion_status'] for p in predictions)),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'unresolved_cases':validation['unresolved_cases']}
    (artifacts/'run.json').write_text(json.dumps(usage,indent=2),encoding='utf8')
    print(json.dumps({**validation,**usage}))
    return predictions,index,engine

def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description='Evidence-driven deletion audit')
    parser.add_argument('--dataset',type=Path,default=root/'dataset')
    parser.add_argument('--requests',type=Path)
    parser.add_argument('--output',type=Path,default=root/'output.csv')
    parser.add_argument('--artifacts',type=Path,default=root/'evaluation_artifacts/full')
    parser.add_argument('--cache',type=Path,default=root/'.audit_cache')
    parser.add_argument('--strict',action='store_true',help='Return exit code 2 if any case has unresolved evidence or policy conditions')
    args=parser.parse_args()
    _,_,engine=run(args.dataset,args.requests or args.dataset/'deletion_requests.csv',args.output,args.artifacts,args.cache)
    if args.strict and any(t['uncertainties'] for t in engine.case_traces.values()):
        print('Strict audit rejected: unresolved cases are recorded in case_traces.json',file=__import__('sys').stderr)
        raise SystemExit(2)

if __name__=='__main__': main()
