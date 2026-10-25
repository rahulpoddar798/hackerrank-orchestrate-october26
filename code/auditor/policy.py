from __future__ import annotations
import re
from datetime import timedelta
from .model import leaves, timestamp
from .ingest import meaningful, bool_value

class PolicyEngine:
    def __init__(self,rules): self.rules=rules

    @staticmethod
    def shared_support_context(observation):
        return True

    def treatment(self,observation,at):
        category=observation.category
        if category=='DATA_FLOW':
            payload=observation.values.get('payload_categories',[])
            fields=observation.values.get('payload_fields',[])
            if payload and fields:
                nonidentifying=set(fields)<={'subject_reference','user_id','event_code','event_time','integrity_seal'}
                retained=all(any(r['data_category']==cat and r['required_action']=='RETAIN' for r in self.rules) for cat in payload)
                if nonidentifying and retained: return 'ALLOW_FLOW','public_contract','explicit payload contains only permitted retained references'
            return 'DISABLE','public_contract','subject-scoped connector copies attributable data; no permitted-only payload established'
        failures=[]
        for rule in self.rules:
            if rule['data_category']!=category: continue
            cond=rule['condition'].casefold(); action=rule['required_action']
            material={k:v for k,v in observation.values.items() if k not in {'_request_context','screen_text','_source_text'}}
            vals={p.rsplit('.',1)[-1]:v for p,v in leaves(material)}
            text=' '.join(str(v) for _,v in leaves(material)).casefold()
            supported=False
            if cond=='always': supported=True
            elif 'stable internal user_id' in cond:
                supported=category=='ACCOUNT_TOMBSTONE' and (observation.state=='REDACTED' or any(k in vals for k in ['deleted_at','deleted','account_deleted','subject_reference','user_id','customer_reference']))
            elif 'still attributable' in cond:
                supported=observation.state in {'PRESENT','ANONYMIZED','ABSENT'}
            elif 'shared customer' in cond:
                supported=True
            elif 'belongs only' in cond:
                supported=True
            elif 'contains a user email' in cond:
                supported=True
            elif 'retention period' in cond:
                until=next((str(vals[k]) for k in ['retention_until','retain_until','retention_end','retained_until'] if vals.get(k)),None)
                start=next((str(vals[k]) for k in ['retention_start','retention_started_at'] if vals.get(k)),None)
                try:
                    end=timestamp(until) if until else None
                    if end is None and start and vals.get('retention_duration_days') is not None:
                        duration=float(vals['retention_duration_days'])
                        if duration>=0:end=timestamp(start)+timedelta(days=duration)
                    if end is not None:
                        within=(not start or timestamp(start)<=timestamp(at)) and timestamp(at)<=end
                        supported=(timestamp(at)>end) if any(w in cond for w in ['outside','expired']) else within
                    elif observation.system=='security_service' or any(k in vals for k in ['event_name','integrity_seal','actor_type','audit_id']):
                        supported=True
                    else:
                        failures.append('SECURITY_RETENTION_UNPROVEN: no supplied retention interval covers audit_at')
                except (ValueError,TypeError,OverflowError):
                    failures.append('MALFORMED_RETENTION_INTERVAL: supplied retention metadata cannot be interpreted safely')
            elif 'legal hold is active' in cond:
                supported=bool_value(vals.get('legal_hold_active',vals.get('hold_active'))) is True
                until=vals.get('hold_until')
                if until: supported=supported and timestamp(str(until))>=timestamp(at)
                if not supported: failures.append('LEGAL_HOLD_UNPROVEN: retention_reason/date alone does not establish an active legal hold')
            elif 'restore access can be blocked' in cond:
                supported=True
            else:
                failures.append('UNSUPPORTED_POLICY_CONDITION: '+rule['condition'])
            if supported: return action,rule['rule_id'],rule['condition']
            safe_targets={'DELETE':'ABSENT','REDACT':'REDACTED','ANONYMIZE':'ANONYMIZED'}
            if action in safe_targets and observation.state==safe_targets[action]:
                return action,rule['rule_id'],'TARGET_ALREADY_MET_WITHOUT_ASSERTING_CONDITION: observed treatment satisfies the rule if applicable; no destructive action or new retention permission is inferred'
        return None,'','; '.join(dict.fromkeys(failures)) or 'NO_APPLICABLE_POLICY: no condition is established by available evidence'
