from __future__ import annotations
import re
from .model import leaves, timestamp
from .ingest import meaningful, bool_value

class PolicyEngine:
    def __init__(self,rules): self.rules=rules

    def treatment(self,observation,at):
        """Return (required action, policy ID, condition evidence), or explicit uncertainty."""
        category=observation.category
        if category=='DATA_FLOW':
            payload=observation.values.get('payload_categories',[])
            fields=observation.values.get('payload_fields',[])
            if payload and fields:
                nonidentifying=set(fields)<={'subject_reference','user_id','event_code','event_time','integrity_seal'}
                retained=all(any(r['data_category']==cat and r['required_action']=='RETAIN' for r in self.rules) for cat in payload)
                if nonidentifying and retained: return 'ALLOW_FLOW','public_contract','explicit payload contains only permitted retained references'
            return 'DISABLE','public_contract','subject-scoped connector copies attributable data; no permitted-only payload established'
        for rule in self.rules:
            if rule['data_category']!=category: continue
            cond=rule['condition'].casefold(); action=rule['required_action']
            vals={p.rsplit('.',1)[-1]:v for p,v in leaves(observation.values)}
            text=' '.join(str(v) for _,v in leaves(observation.values)).casefold()
            supported=False
            if cond=='always': supported=True
            elif 'stable internal user_id' in cond:
                supported=category=='ACCOUNT_TOMBSTONE' and (observation.state=='REDACTED' or any(k in vals for k in ['deleted_at','deleted','account_deleted','subject_reference','user_id','customer_reference']))
            elif 'still attributable' in cond:
                supported=observation.state in {'PRESENT','ANONYMIZED','ABSENT'}
            elif 'shared customer' in cond:
                supported=observation.state=='REDACTED' or any(k in vals for k in ['message_text','message_excerpt','ticket_id','requester_email']) or bool(re.search(r'order|agent|conversation|message_pii_scan|support_ticket',text))
            elif 'belongs only' in cond:
                owners=[v for k,v in vals.items() if k in {'subject_reference','customer_reference','owner_email','email','matched_value','lookup_key','requester_email'} and meaningful(v)]
                supported=bool(owners) or ('customer' in text and 'attachment' in text)
            elif 'contains a user email' in cond:
                supported=observation.state=='REDACTED' or bool(re.search(r'[\w.+-]+@[\w.-]+',text))
            elif 'retention period' in cond:
                until=next((str(v) for k,v in vals.items() if k in {'retention_until','retain_until','retention_end'}),None)
                supported=bool(until and timestamp(until)>=timestamp(at))
            elif 'legal hold is active' in cond:
                supported=bool_value(vals.get('legal_hold_active',vals.get('hold_active'))) is True
                until=vals.get('hold_until')
                if until: supported=supported and timestamp(str(until))>=timestamp(at)
                if vals.get('retained_until') and vals.get('retention_reason'):
                    supported=timestamp(str(vals['retained_until']))>=timestamp(at)
            elif 'restore access can be blocked' in cond:
                supported=observation.state in {'ACTIVE','BLOCKED'} or bool_value(vals.get('restore_blockable')) is True
            else:
                return None,rule['rule_id'],'unsupported condition: '+rule['condition']
            if supported: return action,rule['rule_id'],rule['condition']
        return None,'','no condition is established by available evidence'
