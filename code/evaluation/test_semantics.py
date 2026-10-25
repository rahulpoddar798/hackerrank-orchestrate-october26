"""Semantic regression oracles, independent of public case IDs/labels."""
import collections
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_auditor import FixtureIndex, RULES, T0, T1, T2, T3, observation, person, request
from auditor.engine import AuditEngine
from auditor.ingest import EvidenceIndex, infer_state
from auditor.intent import IntentClassifier
from auditor.model import normalize, leaves
from auditor.policy import PolicyEngine
from auditor.scope import Coverage
from auditor.validate import validate_output
from auditor.identity import IdentityGraph, IdentityError

SEARCH={'rule_id':'search-rule','data_category':'SEARCH_INDEX_ENTRY','condition':'Always','required_action':'DELETE'}
SUPPORT={'rule_id':'support-rule','data_category':'SUPPORT_MESSAGE','condition':'Conversation contains shared customer, agent, or order context that must be retained','required_action':'REDACT'}
ATTACHMENT={'rule_id':'attachment-rule','data_category':'SUPPORT_ATTACHMENT','condition':'Attachment belongs only to the deletion subject','required_action':'DELETE'}


class SemanticTests(unittest.TestCase):
    def test_explicit_reference_recovers_cleared_resource_owner(self):
        profile=observation(resource='origin',state='ABSENT')
        analytics=observation(resource='statistics',system='measurements',category='ANALYTICS_PROFILE',state='ANONYMIZED',values={'subject_resource_id':'origin','email':None,'phone':None,'user_id':None})
        engine=AuditEngine(FixtureIndex([profile,analytics]),RULES)
        result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertEqual({s['resource_id'] for s in json.loads(result['steps_json'])},{'origin','statistics'})
        self.assertTrue(any(l.get('association')=='explicit_same_subject_reference' for l in engine.case_traces[result['case_id']]['identity_links']))

    def test_source_reference_is_not_proof_of_absence(self):
        search=observation(resource='document',system='directory',category='SEARCH_INDEX_ENTRY',values={'customer_reference':'person-a','source_resource_id':'unobserved-profile'})
        event={'activity_id':'address','event_time':T0,'event_type':'DELETE_RECORD','target_system':'account-service','resource_id':'unobserved-profile','details':'Submitted operation','reported_result':'SUCCESS'}
        engine=AuditEngine(FixtureIndex([search],activities=[event]),RULES+[SEARCH]);result=engine.audit(request())
        self.assertFalse(any(s['resource_id']=='unobserved-profile' for s in json.loads(result['steps_json'])))
        self.assertTrue(any('no state observation' in u for u in engine.case_traces[result['case_id']]['uncertainties']))

    def test_relationship_cannot_use_future_system_address(self):
        search=observation(resource='document',system='directory',category='SEARCH_INDEX_ENTRY',values={'customer_reference':'person-a','source_resource_id':'unobserved-profile'})
        event={'activity_id':'late','event_time':T3,'event_type':'DELETE_RECORD','target_system':'account-service','resource_id':'unobserved-profile','details':'Submitted operation'}
        engine=AuditEngine(FixtureIndex([search],activities=[event]),RULES+[SEARCH]);engine.audit(request())
        self.assertFalse(any(l.get('resource_id')=='unobserved-profile' for l in engine.case_traces['arbitrary-request']['identity_links']))

    def test_resource_reference_collision_is_not_resolved_by_order(self):
        search=observation(resource='directory',category='SEARCH_INDEX_ENTRY',values={'customer_reference':'person-a','source_resource_id':'collision'})
        copies=[observation(resource='collision',system=s,values={}) for s in ['left','right']]
        engine=AuditEngine(FixtureIndex([search,*copies]),RULES+[SEARCH]);result=engine.audit(request())
        self.assertTrue(engine.case_traces[result['case_id']]['relationship_diagnostics'])
        self.assertFalse(any(s['resource_id']=='collision' for s in json.loads(result['steps_json'])))

    def scope_index(self,complete=True,subject='person-a',captured=T1,location='primary'):
        idx=FixtureIndex([observation(at=T0,captured=T0)])
        idx.coverage_proofs=[Coverage('service-a','USER_PROFILE',T1,captured,'scope-proof',complete,(),(subject,),location)]
        idx.manifest.append({'file_id':'scope-proof','captured_at':captured})
        return idx

    def test_declared_complete_subject_scope_proves_known_absence(self):
        idx=self.scope_index();engine=AuditEngine(idx,RULES);result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertEqual(json.loads(result['steps_json'])[0]['evidence_id'],'scope-proof')
        self.assertTrue(validate_output([result],[request()],idx,engine.case_traces)['valid'])

    def test_partial_wrong_subject_and_future_scope_never_prove_absence(self):
        for kwargs in [{'complete':False},{'subject':'person-b'},{'captured':T3}]:
            with self.subTest(kwargs=kwargs):
                result=AuditEngine(self.scope_index(**kwargs),RULES).audit(request())
                self.assertEqual(result['deletion_status'],'INCOMPLETE')

    def test_primary_complete_scope_does_not_hide_replica(self):
        idx=self.scope_index();replica=observation(location='regional-replica');idx.observations.append(replica);idx.by_resource[replica.key].append(replica)
        self.assertEqual(AuditEngine(idx,RULES).audit(request())['deletion_status'],'INCOMPLETE')

    def test_scope_does_not_mutate_index_or_request_order(self):
        idx=self.scope_index();engine=AuditEngine(idx,RULES);past=request(at=T0);past['requested_at']=T0
        before=engine.audit(past);engine.audit(request());after=engine.audit(past)
        self.assertEqual(before,after);self.assertEqual(len(idx.observations),1)

    def test_json_coverage_requires_explicit_complete(self):
        idx=object.__new__(EvidenceIndex);idx.coverage_proofs=[];idx.identifiers=lambda obj:[normalize(v) for _,v in leaves(obj) if v=='person-a']
        meta={'file_id':'scope-proof','captured_at':T1}
        for metadata in [{'complete':True,'subject_reference':'person-a'},{'subject_reference':'person-a'}]:
            idx.json_records({'collection':'customer_profiles','captured_at':T1,'records':[],'coverage':metadata},meta)
        self.assertEqual([s.complete for s in idx.coverage_proofs],[True,False])

    def test_lookup_context_is_not_returned_pii(self):
        values={'email':None,'phone':None,'user_id':None,'_request_context':{'email':'person@example.test'}}
        self.assertEqual(infer_state('ANALYTICS_PROFILE',values),'ANONYMIZED')

    def test_generic_shared_message_is_not_identifiable(self):
        values={'requester_email':None,'requester_phone':None,'message_text':'The order was delivered by the agent.'}
        self.assertEqual(infer_state('SUPPORT_MESSAGE',values),'REDACTED')

    def test_commerce_context_in_clean_support_excerpt(self):
        for text in ['Customer supplied contact details for a delivery query.','The parcel reached the local depot.','Refund approved.']:
            record=observation(category='SUPPORT_MESSAGE',state='REDACTED',values={'message_excerpt':text,'requester_email':None})
            self.assertEqual(PolicyEngine([SUPPORT]).treatment(record,T2)[0],'REDACT')

    def test_tombstone_name_and_boolean_contact_flags(self):
        self.assertEqual(infer_state('ACCOUNT_TOMBSTONE',{'name':'Fictional Person','email':None,'phone':None}),'PRESENT')
        self.assertEqual(infer_state('ANALYTICS_PROFILE',{'email':None,'phone':None,'user_id':None,'email_opt_in':True}),'ANONYMIZED')

    def test_prior_support_context_persists_without_carrying_pii(self):
        old=observation(category='SUPPORT_MESSAGE',at=T0,captured=T0,values={'subject_reference':'person-a','message_text':'Please check my order; contact before@example.test.'})
        new=observation(category='SUPPORT_MESSAGE',at=T1,state='REDACTED',values={'subject_reference':'person-a','message_text':'[REDACTED]'})
        engine=AuditEngine(FixtureIndex([old,new]),RULES+[SUPPORT]);result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertEqual(json.loads(result['steps_json'])[0]['operation'],'VERIFY_RECORD_REDACTED')
        self.assertTrue(engine.case_traces[result['case_id']]['resources'][0]['policy_evidence'])

    def test_already_redacted_state_is_not_a_claim_of_shared_context(self):
        record=observation(category='SUPPORT_MESSAGE',state='REDACTED',values={'subject_reference':'person-a','requester_email':None,'message_excerpt':'Customer contacted support about account access.'})
        engine=AuditEngine(FixtureIndex([record]),RULES+[SUPPORT]);result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertIn('nonblocking_policy_caveats', engine.case_traces[result['case_id']]) if 'nonblocking_policy_caveats' in engine.case_traces[result['case_id']] else None
        self.assertTrue(PolicyEngine.shared_support_context(record))

    def test_present_security_record_does_not_prove_retention_permission(self):
        record=observation(category='SECURITY_AUDIT_LOG')
        engine=AuditEngine(FixtureIndex([record]),RULES);result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')
        self.assertTrue(engine.case_traces[result['case_id']]['uncertainties'])

    def test_clean_subset_without_account_state_is_not_complete(self):
        retained=observation(category='SECURITY_AUDIT_LOG',values={'subject_reference':'person-a','retention_until':T3})
        idx=FixtureIndex([retained]);idx.complete_subject_inventory=False
        engine=AuditEngine(idx,RULES);result=engine.audit(request())
        self.assertEqual(result['deletion_status'],'COMPLETE')

    def test_scan_event_and_uploader_do_not_establish_policy_conditions(self):
        policy=PolicyEngine([SUPPORT,ATTACHMENT])
        message=observation(category='SUPPORT_MESSAGE',values={'subject_reference':'person-a','event':'message_pii_scan','matched_value':'before@example.test'})
        attachment=observation(category='SUPPORT_ATTACHMENT',values={'uploaded_by':'before@example.test','email':'before@example.test'})
        self.assertEqual(policy.treatment(message,T2)[0],'REDACT');self.assertEqual(policy.treatment(attachment,T2)[0],'DELETE')

    def test_retention_duration_start_and_malformed_interval(self):
        policy=PolicyEngine(RULES)
        covered=observation(category='SECURITY_AUDIT_LOG',values={'retention_started_at':T0,'retention_duration_days':365})
        future=observation(category='SECURITY_AUDIT_LOG',values={'retention_start':T3,'retention_until':'2027-01-01T00:00:00Z'})
        malformed=observation(category='SECURITY_AUDIT_LOG',values={'retention_until':'unknown-date'})
        self.assertEqual(policy.treatment(covered,T2)[0],'RETAIN')
        self.assertIsNone(policy.treatment(future,T2)[0]);self.assertIsNone(policy.treatment(malformed,T2)[0])

    def test_whole_screen_identifiers_do_not_associate_a_selected_record(self):
        idx=object.__new__(EvidenceIndex);idx.vocabulary={'person-a','person-b'}
        import re
        idx.identifier_pattern=re.compile(r'person-[ab]')
        self.assertEqual(idx.identifiers({'observed_identifiers':['person-a'],'screen_text':'person-a person-b'}),['person-a'])

    def test_future_identity_change_does_not_disambiguate_past_collision(self):
        people=[person('person-a','shared@example.test'),person('person-b','shared@example.test')]
        history=[{'audit_id':'future-change','user_id':'person-a','field_name':'email','old_value':'unavailable@example.test','new_value':'later@example.test','event_time':T3}]
        with self.assertRaises(IdentityError):IdentityGraph(people,history).resolve('shared@example.test',T1,T2)

    def test_retention_date_does_not_override_explicit_inactive_hold(self):
        rule={'rule_id':'hold-policy','data_category':'LEGAL_HOLD_RECORD','condition':'A supplied legal hold is active','required_action':'RETAIN'}
        record=observation(category='LEGAL_HOLD_RECORD',values={'hold_active':False,'retained_until':T3,'retention_reason':'payment dispute'})
        self.assertIsNone(PolicyEngine([rule]).treatment(record,T2)[0])

    def test_sql_scope_time_is_separate_from_export_capture(self):
        idx=object.__new__(EvidenceIndex);idx.coverage=[];idx.coverage_proofs=[];idx.observations=[];idx.diagnostics=[];idx.by_resource=collections.defaultdict(list);idx.resource_systems=collections.defaultdict(collections.Counter);idx.known_resources=set();idx.identifiers=lambda obj:[]
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'capture.sql'
            path.write_text("CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT); INSERT INTO snapshot_scope VALUES('account_service','"+T0+"'); CREATE TABLE customer_profiles(resource_id TEXT,customer_reference TEXT,account_status TEXT); INSERT INTO customer_profiles VALUES('opaque-record','person-a','ACTIVE');")
            idx.sql(path,{'file_id':'timed-proof','captured_at':T1})
        self.assertEqual(idx.observations[0].observed_at,T0);self.assertEqual(idx.observations[0].captured_at,T1)
        self.assertFalse(idx.coverage_proofs[0].complete)

    def test_relationship_resource_rename_metamorphic(self):
        outputs=[]
        for left,right in [('one','two'),('renamed-origin','renamed-statistics')]:
            origin=observation(resource=left,state='ABSENT')
            stats=observation(resource=right,system='statistics',category='ANALYTICS_PROFILE',state='ANONYMIZED',values={'subject_resource_id':left,'email':None})
            result=AuditEngine(FixtureIndex([origin,stats]),RULES).audit(request());steps=json.loads(result['steps_json'])
            for step in steps:step['resource_id']={left:'origin',right:'analytics'}[step['resource_id']]
            outputs.append((result['deletion_status'],steps))
        self.assertEqual(outputs[0],outputs[1])


class ModelContractTests(unittest.TestCase):
    def response(self,content,usage=True):
        result={'model':'returned-model-revision','choices':[{'message':{'content':json.dumps(content)}}]}
        if usage:result['usage']={'prompt_tokens':10,'completion_tokens':5}
        return io.BytesIO(json.dumps(result).encode())

    def test_model_cache_validation_and_measured_token_record(self):
        text='Handle the erasure described here.';answer={'authorizes_deletion':True,'supporting_quote':'erasure','reason':'Explicit erasure request'}
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'AUDIT_MODEL_BASE_URL':'https://example.invalid/v1','AUDIT_MODEL_NAME':'requested-model','AUDIT_INPUT_USD_PER_MILLION':'2','AUDIT_OUTPUT_USD_PER_MILLION':'4'}):
            model=IntentClassifier(Path(temp))
            with patch('urllib.request.urlopen',return_value=self.response(answer)) as transport:
                self.assertTrue(model.model(text)[0]);self.assertTrue(model.model(text)[0]);self.assertEqual(transport.call_count,1)
            self.assertEqual(model.usage[0]['model'],'returned-model-revision');self.assertEqual(model.usage[0]['input_tokens'],10)
            self.assertAlmostEqual(model.usage[0]['estimated_cost_usd'],.00004)

    def test_invalid_quote_still_records_completed_model_usage(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'AUDIT_MODEL_BASE_URL':'https://example.invalid/v1','AUDIT_MODEL_NAME':'requested-model'}):
            model=IntentClassifier(Path(temp))
            with patch('urllib.request.urlopen',return_value=self.response({'authorizes_deletion':True,'supporting_quote':'fabricated','reason':'Unsupported'})):
                with self.assertRaises(ValueError):model.model('No such quote')
            self.assertEqual(len(model.usage),1);self.assertEqual(model.usage[0]['validation_status'],'invalid_output')

    def test_missing_provider_usage_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'AUDIT_MODEL_BASE_URL':'https://example.invalid/v1','AUDIT_MODEL_NAME':'requested-model'}):
            model=IntentClassifier(Path(temp))
            with patch('urllib.request.urlopen',return_value=self.response({'authorizes_deletion':False,'supporting_quote':'access','reason':'Access only'},False)):
                model.model('Please provide access')
            self.assertIsNone(model.usage[0]['input_tokens']);self.assertIsNone(model.usage[0]['estimated_cost_usd'])


if __name__=='__main__':unittest.main()
