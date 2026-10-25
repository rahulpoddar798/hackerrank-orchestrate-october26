"""Evaluate public samples; inference code never reads sample_output.csv."""
from __future__ import annotations
import argparse
import collections
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auditor.model import rows,STEP_FIELDS

def step_key(s): return tuple(s[k] for k in ['phase','system_id','resource_id','operation'])

def evaluate(expected,predictions):
    predicted={r['case_id']:r for r in predictions};status=sequence=exact_cases=matched=fields=field_total=total_expected=total_predicted=0;mismatches=[]
    for r in expected:
        p=predicted.get(r['case_id'],{'deletion_status':None,'steps_json':'[]'})
        es=json.loads(r['steps_json']);ps=json.loads(p['steps_json'])
        status+=r['deletion_status']==p['deletion_status'];sequence+=es==ps;exact_cases+=es==ps and r['deletion_status']==p['deletion_status']
        ec=collections.Counter(json.dumps(s,sort_keys=True) for s in es);pc=collections.Counter(json.dumps(s,sort_keys=True) for s in ps)
        matched+=sum((ec&pc).values());total_expected+=len(es);total_predicted+=len(ps)
        em={step_key(s):s for s in es};pm={step_key(s):s for s in ps}
        for key in em.keys()|pm.keys():
            field_total+=len(STEP_FIELDS)
            if key in em and key in pm:fields+=sum(em[key][f]==pm[key][f] for f in STEP_FIELDS)
        if es!=ps or r['deletion_status']!=p['deletion_status']:
            mismatches.append({'case_id':r['case_id'],'expected_status':r['deletion_status'],'predicted_status':p['deletion_status'],'expected_steps':len(es),'predicted_steps':len(ps),'missing_steps':[s for s in es if s not in ps],'extra_steps':[s for s in ps if s not in es]})
    n=len(expected)
    return {'cases':n,'status_correct':status,'status_accuracy':status/n,'exact_cases':exact_cases,'exact_case_accuracy':exact_cases/n,'exact_sequences':sequence,'sequence_accuracy':sequence/n,'exact_steps_matched':matched,'expected_steps':total_expected,'predicted_steps':total_predicted,'step_precision':matched/total_predicted if total_predicted else 0,'step_recall':matched/total_expected if total_expected else 0,'correct_fields':fields,'compared_fields':field_total,'field_accuracy':fields/field_total if field_total else 1,'mismatches':mismatches}

def main():
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser();p.add_argument('--expected',type=Path,default=root/'dataset/sample_output.csv');p.add_argument('--predictions',type=Path,default=root/'evaluation_artifacts/sample_predictions.csv');p.add_argument('--output',type=Path,default=root/'evaluation_artifacts/sample_metrics.json');a=p.parse_args()
    metrics=evaluate(rows(a.expected),rows(a.predictions));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(metrics,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in metrics.items() if k!='mismatches'}))

if __name__=='__main__':main()
