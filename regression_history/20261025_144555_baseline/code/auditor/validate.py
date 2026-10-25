from __future__ import annotations
import json
from .model import STEP_FIELDS, STATES, step_sort, timestamp

def validate_output(predictions,requests,index,traces=None):
    errors=[]
    request_map={r['case_id']:r for r in requests}
    ids=[p['case_id'] for p in predictions]
    if ids!=sorted(request_map) or len(set(ids))!=len(ids): errors.append('Case coverage, uniqueness, or sorting mismatch')
    evidence={m['file_id']:m['captured_at'] for m in index.manifest}
    evidence.update({a['activity_id']:a['event_time'] for a in index.activities})
    evidence.update({a['audit_id']:a['event_time'] for a in index.audit})
    count=0
    for p in predictions:
        cid=p['case_id']; status=p['deletion_status']
        if set(p)!={'case_id','deletion_status','steps_json'}: errors.append(cid+': wrong CSV fields')
        if status not in {'COMPLETE','INCOMPLETE','NOT_APPLICABLE'}: errors.append(cid+': invalid status')
        try: steps=json.loads(p['steps_json'])
        except (ValueError,TypeError): errors.append(cid+': invalid JSON');continue
        if not isinstance(steps,list): errors.append(cid+': steps must be an array');continue
        if status=='NOT_APPLICABLE' and steps: errors.append(cid+': non-deletion has steps')
        if steps!=sorted(steps,key=step_sort): errors.append(cid+': step ordering mismatch')
        seen=set()
        for i,s in enumerate(steps,1):
            count+=1
            if set(s)!=STEP_FIELDS or s['step_no']!=i: errors.append(cid+': step schema/numbering mismatch')
            if STATES.get(s['operation'])!=s['state']: errors.append(cid+': invalid operation/state')
            if status=='COMPLETE' and s['phase']!='VERIFICATION': errors.append(cid+': complete case contains non-verification')
            required=s['phase']=='FINDING' or status=='COMPLETE'
            eid=s['evidence_id']
            if required:
                if eid not in evidence: errors.append(cid+': unknown/missing evidence '+eid)
                elif timestamp(evidence[eid])>timestamp(request_map[cid]['audit_at']): errors.append(cid+': future evidence')
                relevant=[o for o in index.by_resource.get((s['system_id'],s['resource_id']),[]) if o.evidence_id==eid and o.available(request_map[cid]['audit_at'])]
                if not relevant: errors.append(cid+': citation lacks a timely resource observation')
                elif required:
                    needed={'VERIFY_RECORD_ABSENT':'ABSENT','VERIFY_RECORD_PRESENT':'PRESENT','VERIFY_RECORD_REDACTED':'REDACTED','VERIFY_RECORD_ANONYMIZED':'ANONYMIZED','VERIFY_DATA_FLOW_DISABLED':'DISABLED','VERIFY_RESTORE_BLOCKED':'BLOCKED','REPORT_REMAINING_RECORD':'PRESENT','REPORT_EXPOSED_PII':'PRESENT','REPORT_ACTIVE_DATA_FLOW':'ACTIVE','REPORT_RESTORE_RISK':'ACTIVE'}[s['operation']]
                    if not any(o.state==needed for o in relevant): errors.append(cid+': citation does not prove reported state')
            elif eid: errors.append(cid+': proposed action has evidence ID')
            key=(s['phase'],s['system_id'],s['resource_id'],s['operation'])
            if key in seen: errors.append(cid+': duplicate step')
            seen.add(key)
    return {'valid':not errors,'cases':len(predictions),'steps':count,'errors':errors,'unresolved_cases':sum(bool(t['uncertainties']) for t in (traces or {}).values())}
