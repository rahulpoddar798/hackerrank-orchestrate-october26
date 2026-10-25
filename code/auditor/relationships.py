"""Typed, temporal relationship traversal. No numeric or proximity joins."""
from __future__ import annotations
from collections import defaultdict
from .model import leaves, normalize, timestamp


class RelationshipIndex:
    def __init__(self, index):
        self.index = index

    def expand(self, seeds, subject, at):
        keys = set(seeds)
        associations = []
        diagnostics = []
        observations = [o for o in self.index.observations if o.available(at)]
        resource_keys = defaultdict(set)
        for observation in observations:
            resource_keys[observation.resource].add(observation.key)
        # Activity supplies a resource/system address, never its state or owner.
        for event in self.index.activities:
            if timestamp(event['event_time']) > timestamp(at):
                continue
            if event['event_type'] in {'DELETE_RECORD','REDACT_RECORD','ANONYMIZE_RECORD','LINK_RESOURCE_IDENTITY'}:
                resource_keys[event['resource_id']].add((event['target_system'], event['resource_id']))
        edges = []
        for observation in observations:
            for path, value in leaves(observation.values):
                field = path.rsplit('.', 1)[-1]
                # These properties explicitly identify the subject's own record.
                same_subject = field in {'subject_resource_id','identity_resource_id','account_resource_id'}
                # A search document's declared source profile is a copied subject record.
                same_subject |= field == 'source_resource_id' and observation.category == 'SEARCH_INDEX_ENTRY'
                if not same_subject or not isinstance(value, str):
                    continue
                targets = resource_keys.get(value, set())
                if len(targets) != 1:
                    diagnostics.append({'reason':'ambiguous_resource_reference','from':observation.key,'reference_field':path,'candidate_count':len(targets)})
                    continue
                edges.append((observation.key, next(iter(targets)), observation, path))
        changed = True
        while changed:
            changed = False
            for left, right, proof, field in edges:
                if (left in keys) == (right in keys):
                    continue
                candidate = right if left in keys else left
                owners = {
                    normalize(v) for o in observations if o.key == candidate
                    for p,v in leaves(o.values)
                    if p.rsplit('.',1)[-1] in {'user_id','customer_reference','subject_reference'}
                    and isinstance(v,str) and v in {person['user_id'] for person in self.index.identities}
                }
                if owners - {normalize(subject)}:
                    diagnostics.append({'reason':'relationship_owner_conflict','resource':candidate,'evidence_id':proof.evidence_id})
                    continue
                keys.add(candidate)
                associations.append({'system_id':candidate[0],'resource_id':candidate[1],'evidence_id':proof.evidence_id,'association':'explicit_same_subject_reference','reference_field':field,'from_resource':proof.resource})
                changed = True
        return keys, associations, diagnostics
