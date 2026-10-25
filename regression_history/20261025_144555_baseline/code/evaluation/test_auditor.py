"""Independent synthetic fixtures. No public sample answers are imported."""
from __future__ import annotations
import collections
import copy
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auditor.engine import AuditEngine
from auditor.identity import IdentityGraph, IdentityError
from auditor.ingest import infer_state, EvidenceIndex
from auditor.intent import IntentClassifier
from auditor.model import Observation, normalize
from auditor.validate import validate_output

T0='2026-01-01T00:00:00Z'; T1='2026-02-01T00:00:00Z'; T2='2026-03-01T00:00:00Z'; T3='2026-04-01T00:00:00Z'
RULES=[{'rule_id':'policy-a','data_category':'USER_PROFILE','condition':'Always','required_action':'DELETE'},
 {'rule_id':'policy-b','data_category':'ACCOUNT_TOMBSTONE','condition':'Account is deleted and only a stable internal user_id is needed to preserve references to retained records','required_action':'REDACT'},
 {'rule_id':'policy-c','data_category':'BACKUP_ARCHIVE','condition':'Restore access can be blocked','required_action':'RETAIN'},
 {'rule_id':'policy-d','data_category':'SECURITY_AUDIT_LOG','condition':'Record is within the supplied retention period','required_action':'RETAIN'},
 {'rule_id':'policy-e','data_category':'ANALYTICS_PROFILE','condition':'Record is still attributable to a user','required_action':'ANONYMIZE'}]

def person(uid='person-a',email='before@example.test'):
    return {'user_id':uid,'email':email,'phone':'+00 123456789','email_hash':uid+'-hash','name':'Fictional Person','updated_at':T0}

def observation(resource='opaque-r',state='PRESENT',at=T1,captured=T1,category='USER_PROFILE',system='service-a',values=None,location='primary',eid='proof-a'):
    values={'customer_reference':'person-a'} if values is None else values
    return Observation(system,resource,category,state,at,captured,eid,values,[normalize(v) for v in values.values() if v is not None],location=location)

class FixtureIndex:
    def __init__(self,observations,identities=None,history=None,activities=None):
        self.observations=observations; self.identities=identities or [person()]; self.audit=history or [];self.activities=activities or []
        self.cache=Path(tempfile.gettempdir())/'audit-intent-test-cache'
        self.by_resource=collections.defaultdict(list)
        for o in observations:self.by_resource[o.key].append(o)
        self.manifest=[{'file_id':o.evidence_id,'captured_at':o.captured_at} for o in observations]
        self.identifiers=lambda obj:[normalize(v) for v in str(obj).split()]

def request(text='Please delete my account.',cid='arbitrary-request',email='before@example.test',at=T2):
    return {'case_id':cid,'email':email,'requested_at':T1,'audit_at':at,'request_text':text,'reported_status':'COMPLETE','reported_at':T1}

class AuditTests(unittest.TestCase):
    def audit(self,obs,req=None,**kwargs):
        engine=AuditEngine(FixtureIndex(obs,**kwargs),RULES)
        result=engine.audit(req or request()); return result,engine

    def test_historical_identifier_and_reassignment(self):
        history=[{'audit_id':'change-a','user_id':'person-a','event_time':T1,'field_name':'email','old_value':'before@example.test','new_value':'after@example.test'}]
        a=person(email='after@example.test'); a['updated_at']=T1
        b=person('person-b','before@example.test');b['updated_at']=T1
        history.append({'audit_id':'change-b','user_id':'person-b','event_time':T1,'field_name':'email','old_value':'other@example.test','new_value':'before@example.test'})
        graph=IdentityGraph([a,b],history)
        self.assertEqual(graph.resolve('BEFORE@EXAMPLE.TEST',T0,T2),'person-a')
        self.assertEqual(graph.resolve('before@example.test',T2,T2),'person-b')
        collision=IdentityGraph([a,b,person('person-c','before@example.test')],history)
        with self.assertRaises(IdentityError): collision.resolve('before@example.test',T2,T2)

    def test_replica_drift(self):
        result,_=self.audit([observation(state='ABSENT'),observation(state='PRESENT',location='regional-replica')])
        self.assertEqual(result['deletion_status'],'INCOMPLETE')
        self.assertEqual(json.loads(result['steps_json'])[0]['operation'],'REPORT_REMAINING_RECORD')

    def test_recreation_overrides_old_absence(self):
        result,_=self.audit([observation(state='ABSENT',at=T0),observation(at=T1)])
        self.assertEqual(result['deletion_status'],'INCOMPLETE')

    def test_future_capture_and_future_observation_excluded(self):
        result,_=self.audit([observation(state='ABSENT'),observation(at=T1,captured=T3),observation(at=T3,captured=T1)])
        self.assertEqual(result['deletion_status'],'COMPLETE')

    def test_claim_does_not_override_readback(self):
        claim=observation(state='ABSENT',at=T2);claim.claim=True
        result,_=self.audit([observation(),claim]);self.assertEqual(result['deletion_status'],'INCOMPLETE')

    def test_tombstone_exposed_pii(self):
        values={'subject_reference':'person-a','account_status':'DELETED','email':'before@example.test'}
        state=infer_state('ACCOUNT_TOMBSTONE',values)
        result,_=self.audit([observation(category='ACCOUNT_TOMBSTONE',values=values,state=state)])
        steps=json.loads(result['steps_json']);self.assertEqual(steps[0]['operation'],'REPORT_EXPOSED_PII');self.assertEqual(steps[1]['operation'],'REDACT_RECORD')

    def test_clean_tombstone_keeps_stable_reference(self):
        values={'subject_reference':'person-a','account_status':'DELETED','name':None,'email':None,'phone':None,'email_hash':None}
        state=infer_state('ACCOUNT_TOMBSTONE',values)
        result,_=self.audit([observation(category='ACCOUNT_TOMBSTONE',values=values,state=state)])
        self.assertEqual(result['deletion_status'],'COMPLETE')

    def test_backup_block_before_record_change(self):
        backup=observation(resource='opaque-backup',category='BACKUP_ARCHIVE',system='vault',state='ACTIVE',values={'subject_reference':'person-a','restore_allowed':True})
        result,_=self.audit([observation(),backup]);steps=json.loads(result['steps_json'])
        remedies=[s['operation'] for s in steps if s['phase']=='REMEDIATION'];self.assertEqual(remedies,['BLOCK_RESTORE','DELETE_RECORD'])

    def test_conditional_retention_unknown_is_not_default_delete(self):
        result,engine=self.audit([observation(category='SECURITY_AUDIT_LOG')])
        self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])
        self.assertFalse(any(s['operation']=='DELETE_RECORD' for s in json.loads(result['steps_json'])))

    def test_retained_record_with_period(self):
        result,_=self.audit([observation(category='SECURITY_AUDIT_LOG',values={'subject_reference':'person-a','retention_until':T3})])
        self.assertEqual(result['deletion_status'],'COMPLETE');self.assertEqual(json.loads(result['steps_json'])[0]['operation'],'VERIFY_RECORD_PRESENT')

    def test_multilingual_and_non_deletion(self):
        classifier=IntentClassifier(Path('.audit_cache'))
        for text in ['Veuillez supprimer mon compte.','アカウントを削除してください。','Please delete my account.','请删除我的账户。']:
            self.assertIs(classifier.classify(text)[0],True,text)
        for text in ['Please export my data.','Do not delete my account.','Please replace my mobile number and leave the account active.']:
            self.assertIs(classifier.classify(text)[0],False,text)

    def test_case_id_and_file_order_metamorphic(self):
        obs=[observation(at=T0),observation(at=T1,state='ABSENT')]
        first,_=self.audit(obs,request(cid='case-a'))
        second,_=self.audit(list(reversed(obs)),request(cid='unrelated-name'))
        self.assertEqual(first['deletion_status'],second['deletion_status']);self.assertEqual(first['steps_json'],second['steps_json'])

    def test_resource_rename_metamorphic(self):
        first,_=self.audit([observation(resource='left')]);second,_=self.audit([observation(resource='renamed')])
        self.assertEqual(first['deletion_status'],second['deletion_status'])
        a=json.loads(first['steps_json']); b=json.loads(second['steps_json'])
        for s in a:s['resource_id']='renamed'
        self.assertEqual(a,b)

    def test_email_case_metamorphic(self):
        a,_=self.audit([observation()],request(email='BEFORE@EXAMPLE.TEST'));b,_=self.audit([observation()])
        self.assertEqual(a,b)

    def test_partial_export_does_not_prove_absence(self):
        with tempfile.TemporaryDirectory() as temp:
            idx=object.__new__(EvidenceIndex); idx.diagnostics=[];idx.coverage=[];idx.observations=[];idx.by_resource=collections.defaultdict(list);idx.resource_systems=collections.defaultdict(collections.Counter);idx.known_resources=set();idx.identifiers=lambda obj:[]
            p=Path(temp)/'snapshot.sql';p.write_text('CREATE TABLE customer_profiles(resource_id TEXT, email TEXT);')
            idx.sql(p,{'file_id':'proof','captured_at':T1})
            self.assertEqual(idx.observations,[])

    def test_missing_information_not_proof_of_anonymization(self):
        self.assertEqual(infer_state('ANALYTICS_PROFILE',{'metrics':{'orders':2}}),'UNKNOWN')

    def test_sql_last_write_time_is_not_snapshot_observation_time(self):
        with tempfile.TemporaryDirectory() as temp:
            idx=object.__new__(EvidenceIndex);idx.diagnostics=[];idx.coverage=[];idx.observations=[];idx.by_resource=collections.defaultdict(list);idx.resource_systems=collections.defaultdict(collections.Counter);idx.known_resources=set();idx.identifiers=lambda obj:[]
            p=Path(temp)/'capture.sql'
            p.write_text("CREATE TABLE customer_data_primary(resource_id TEXT,origin_system TEXT,collection_name TEXT,record_json TEXT,updated_at TEXT); INSERT INTO customer_data_primary VALUES('opaque','account_service','customer_profiles','{\"email\":\"fictional@example.test\"}','"+T0+"');")
            idx.sql(p,{'file_id':'proof','captured_at':T2})
            self.assertEqual(idx.observations[0].observed_at,T2)
            self.assertEqual(idx.observations[0].values['_record_updated_at'],T0)

    def test_explicit_redacted_label_cannot_hide_real_pii(self):
        self.assertEqual(infer_state('ACCOUNT_TOMBSTONE',{'email':'person@example.test'},'REDACTED'),'PRESENT')

    def test_permitted_retained_reference_flow(self):
        obs=observation(resource='independent-flow',system='integration',category='DATA_FLOW',state='ACTIVE',values={'subject_reference':'person-a','enabled':True,'payload_categories':['SECURITY_AUDIT_LOG'],'payload_fields':['subject_reference','event_code']})
        result,_=self.audit([observation(state='ABSENT'),obs]);self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertFalse(any(s['operation']=='DISABLE_DATA_FLOW' for s in json.loads(result['steps_json'])))

    def test_same_time_contradiction_is_not_complete(self):
        result,engine=self.audit([observation(state='ABSENT'),observation(state='PRESENT',eid='proof-b')])
        self.assertEqual(result['deletion_status'],'INCOMPLETE');self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])

    def test_policy_is_loaded_dynamically(self):
        engine=AuditEngine(FixtureIndex([observation()]),[{'rule_id':'replacement-policy','data_category':'USER_PROFILE','condition':'Always','required_action':'RETAIN'}])
        result=engine.audit(request());self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertEqual(json.loads(result['steps_json'])[0]['operation'],'VERIFY_RECORD_PRESENT')

    def test_no_unsupported_pii_finding_from_sparse_record(self):
        obs=observation(category='ANALYTICS_PROFILE',state='UNKNOWN')
        result,engine=self.audit([obs]);self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])
        self.assertFalse(any(s['phase']=='FINDING' for s in json.loads(result['steps_json'])))

    def test_ambiguous_intent_never_plans_destruction(self):
        result,engine=self.audit([observation()],request(text='Please handle my privacy situation.'))
        self.assertEqual(json.loads(result['steps_json']),[])
        self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])

    def test_missing_transformed_record_is_not_false_pii(self):
        result,engine=self.audit([observation(category='ANALYTICS_PROFILE',state='ABSENT')])
        self.assertEqual(result['deletion_status'],'INCOMPLETE')
        self.assertFalse(any(s['phase']=='FINDING' for s in json.loads(result['steps_json'])))
        self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])

    def test_resource_reassigned_to_other_subject_is_not_deleted(self):
        other=observation(at=T2,values={'customer_reference':'person-b'})
        result,engine=self.audit([observation(at=T0),other],identities=[person(),person('person-b','other@example.test')])
        self.assertEqual(result['deletion_status'],'INCOMPLETE')
        self.assertFalse(any(s['phase']=='REMEDIATION' for s in json.loads(result['steps_json'])))

if __name__=='__main__': unittest.main(verbosity=2)
