from __future__ import annotations
import collections
import json
from dataclasses import replace
from .identity import IdentityGraph, IdentityError
from .intent import IntentClassifier
from .policy import PolicyEngine
from .model import STATES, step_sort, timestamp, normalize, leaves
from .dependencies import analyze_dependencies

TARGETS={'DELETE':('ABSENT','VERIFY_RECORD_ABSENT','REPORT_REMAINING_RECORD','DELETE_RECORD'),
         'REDACT':('REDACTED','VERIFY_RECORD_REDACTED','REPORT_EXPOSED_PII','REDACT_RECORD'),
         'ANONYMIZE':('ANONYMIZED','VERIFY_RECORD_ANONYMIZED','REPORT_EXPOSED_PII','ANONYMIZE_RECORD'),
         'DISABLE':('DISABLED','VERIFY_DATA_FLOW_DISABLED','REPORT_ACTIVE_DATA_FLOW','DISABLE_DATA_FLOW'),
         'BLOCK':('BLOCKED','VERIFY_RESTORE_BLOCKED','REPORT_RESTORE_RISK','BLOCK_RESTORE'),
         'RETAIN':('PRESENT','VERIFY_RECORD_PRESENT',None,None)}

class AuditEngine:
    def __init__(self,index,rules):
        self.index=index
        self.identities=IdentityGraph(index.identities,index.audit)
        self.policy=PolicyEngine(rules)
        self.intent=IntentClassifier(index.cache)
        self.case_traces={}

    def timeline(self,key,at):
        obs=[o for o in self.index.by_resource[key] if o.available(at) and not o.claim]
        # Order independent of manifest/file traversal. Fresh readbacks win; on equal
        # timestamps prefer concrete structured values, then lexicographic evidence ID.
        return sorted(obs,key=lambda o:(timestamp(o.observed_at),o.confidence,len(list(leaves(o.values))),o.evidence_id))

    def audit(self,request):
        cid=request['case_id']; at=request['audit_at']
        authorized,reason=self.intent.classify(request['request_text'])
        trace={'intent':authorized,'intent_reason':reason,'uncertainties':[],'resources':[],'identity_links':[],'claims':[]}
        self.case_traces[cid]=trace
        if authorized is False: return {'case_id':cid,'deletion_status':'NOT_APPLICABLE','steps_json':'[]'}
        if authorized is None:
            trace['uncertainties'].append(reason)
            return self.result(cid,[],True)
        try: user=self.identities.resolve(request['email'],request['requested_at'],at)
        except IdentityError as e:
            trace['uncertainties'].append(str(e)); return self.result(cid,[],True)
        trace['subject']=user
        keys,links=self.identities.relevant(self.index,user,at)
        trace['identity_links']=links
        if any(link.get('association')=='ambiguous identifier collision' for link in links):
            trace['uncertainties'].append('Some candidate resources have non-unique identifier ownership')
        if not keys: trace['uncertainties'].append('No resource has a grounded association available by audit_at')
        plans=[]; findings=[]
        for key in sorted(keys):
            timeline=self.timeline(key,at)
            if not timeline:
                trace['uncertainties'].append('Associated resource has no state observation: '+str(key));continue
            locations={}
            for obs in timeline: locations[obs.location]=obs
            for location,obs in list(locations.items()):
                simultaneous=[o for o in timeline if o.location==location and timestamp(o.observed_at)==timestamp(obs.observed_at)]
                if len({o.state for o in simultaneous})>1:
                    trace['uncertainties'].append(f'{key}: contradictory simultaneous observations at {location}')
                    locations[location]=max(simultaneous,key=lambda o:(o.state in {'PRESENT','ACTIVE'},o.confidence,o.evidence_id))
            decisions=[]
            for location,obs in locations.items():
                stable_fields={normalize(v) for p,v in leaves(obs.values) if p.rsplit('.',1)[-1] in {'user_id','customer_reference','subject_reference'} and v is not None and normalize(v) in self.identities.people}
                if stable_fields-{normalize(user)}:
                    trace['uncertainties'].append(f'{key}: current record has another stable subject reference; destructive treatment requires ownership review')
                    continue
                # Retention/hold metadata can persist; never carry old PII forward.
                metadata={}
                for previous in timeline:
                    for k,v in previous.values.items():
                        if k in {'retention_until','retain_until','retained_until','hold_until','legal_hold_active','hold_active','retention_reason'}: metadata[k]=v
                action,rule,condition=self.policy.treatment(replace(obs,values={**metadata,**obs.values}),at)
                if action=='ALLOW_FLOW':
                    trace['resources'].append({'system_id':key[0],'resource_id':key[1],'actual_state':obs.state,'policy_action':action,'compliant':True,'condition':condition,'timeline':[o.to_dict() for o in timeline]})
                    continue
                if obs.category=='BACKUP_ARCHIVE' and action=='RETAIN': action='BLOCK'
                if action is None:
                    trace['uncertainties'].append(f'{key}: {condition}')
                    # Preserve existing conditionally retained records during review.
                    # This future non-destructive safeguard does not assert that the
                    # missing retention condition has been established.
                    candidate_rules=[r for r in self.policy.rules if r['data_category']==obs.category]
                    if obs.state=='PRESENT' and any(r['required_action']=='RETAIN' for r in candidate_rules):
                        decisions.append((obs,'RETAIN','VERIFY_RECORD_PRESENT',None,None,True,'pending_condition'))
                    continue
                target,verify,finding,remedy=TARGETS[action]
                actual=obs.state
                # An absent deletable/PII-bearing copy is safe. Required retained
                # records/tombstones cannot be silently considered compliant if missing.
                compliant=actual==target
                if actual=='ABSENT' and action in {'REDACT','ANONYMIZE'}:
                    finding=remedy=None
                    trace['uncertainties'].append(f'{key}: required transformed record is absent; public operation set has no recovery operation')
                if actual=='UNKNOWN': trace['uncertainties'].append(f'{key}: state unknown')
                decisions.append((obs,action,verify,finding,remedy,compliant,rule))
            if not decisions: continue
            bad=[d for d in decisions if not d[5]]
            chosen=max(bad or decisions,key=lambda d:(timestamp(d[0].observed_at),d[0].confidence,d[0].evidence_id))
            obs,action,verify,finding,remedy,compliant,rule=chosen
            if bad:
                if finding:
                    findings.append(self.step('FINDING',key,finding,obs.evidence_id))
                    plans.append(self.step('REMEDIATION',key,remedy,''))
                else: trace['uncertainties'].append(f'{key}: required retained record is absent; public operation set has no recovery operation')
            plans.append(self.step('VERIFICATION',key,verify,obs.evidence_id))
            trace['resources'].append({'system_id':key[0],'resource_id':key[1],'actual_state':obs.state,'policy_action':action,'rule_id':rule,'compliant':not bool(bad),'locations':{k:v.state for k,v in locations.items()},'timeline':[o.to_dict() for o in timeline]})
        incomplete=bool(findings or trace['uncertainties'])
        if incomplete:
            for s in plans:
                if s['phase']=='VERIFICATION': s['evidence_id']=''
        trace['claims']=[a for a in self.index.activities if (a['target_system'],a['resource_id']) in keys and timestamp(a['event_time'])<=timestamp(at)]
        result=self.result(cid,findings+plans,incomplete)
        trace['dependencies']=analyze_dependencies(self.index,keys,at,json.loads(result['steps_json']))
        if trace['dependencies']['guard_order_violations']: raise ValueError('Unsafe remediation guard ordering')
        return result

    @staticmethod
    def step(phase,key,operation,evidence):
        return {'step_no':0,'phase':phase,'system_id':key[0],'resource_id':key[1],'operation':operation,'state':STATES[operation],'evidence_id':evidence}

    @staticmethod
    def result(cid,steps,incomplete):
        steps.sort(key=step_sort)
        for i,s in enumerate(steps,1): s['step_no']=i
        return {'case_id':cid,'deletion_status':'INCOMPLETE' if incomplete else 'COMPLETE','steps_json':json.dumps(steps,ensure_ascii=False,separators=(',',':'))}
