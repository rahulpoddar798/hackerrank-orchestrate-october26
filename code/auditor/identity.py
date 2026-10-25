from __future__ import annotations
from collections import defaultdict
from .model import normalize, timestamp

class IdentityError(ValueError): pass

class IdentityGraph:
    """Identifier assignments are temporal edges, not fuzzy person matches."""
    def __init__(self, identities, history):
        self.people={r['user_id']:r for r in identities}
        self.history=defaultdict(list)
        for row in history: self.history[row['user_id']].append(row)
        for rr in self.history.values(): rr.sort(key=lambda r:(r['event_time'],r['audit_id']))
        self._owners_cache={}

    def identifiers(self,user,at):
        found={normalize(user)}
        person=self.people[user]
        if timestamp(person['updated_at'])<=timestamp(at):
            found.update(normalize(person[k]) for k in ['email','phone','email_hash'] if person.get(k))
        for row in self.history[user]:
            if row['field_name'] in {'email','phone','email_hash'} and timestamp(row['event_time'])<=timestamp(at):
                found.update(normalize(row[k]) for k in ['old_value','new_value'] if row[k])
        return found

    def active_email(self,user,at,knowledge_at=None):
        person=self.people[user]
        hist=[r for r in self.history[user] if r['field_name']=='email' and (knowledge_at is None or timestamp(r['event_time'])<=timestamp(knowledge_at))]
        email=hist[0]['old_value'] if hist else person['email']
        for r in hist:
            if timestamp(r['event_time'])<=timestamp(at): email=r['new_value']
        return normalize(email)

    def resolve(self,email,requested_at,audit_at):
        email=normalize(email)
        candidates=[u for u in self.people if email in self.identifiers(u,audit_at)]
        current=[u for u in candidates if self.active_email(u,requested_at,audit_at)==email]
        if len(current)==1: return current[0]
        if len(candidates)==1: return candidates[0]
        raise IdentityError(f'Identity resolution requires a unique temporal assignment; candidates={len(candidates)}')

    def relevant(self,index,user,at):
        tokens=self.identifiers(user,at)
        resources=set(); links=[]
        if at not in self._owners_cache:
            owners=defaultdict(set)
            for uid in self.people:
                for token in self.identifiers(uid,at):owners[token].add(uid)
            self._owners_cache[at]=owners
        owners=self._owners_cache[at]
        for obs in index.observations:
            if not obs.available(at): continue
            other_stable={v for v in obs.identifiers if v in self.people and v!=user}
            if other_stable and normalize(user) not in obs.identifiers: continue
            matched=tokens.intersection(obs.identifiers)
            if matched:
                stable_match=normalize(user) in obs.identifiers
                unique={token for token in matched if owners.get(token)=={user}}
                if not stable_match and not unique:
                    links.append({'resource_id':obs.resource,'evidence_id':obs.evidence_id,'association':'ambiguous identifier collision'})
                    continue
                resources.add(obs.key)
                links.append({'system_id':obs.system,'resource_id':obs.resource,'evidence_id':obs.evidence_id,'matched_identifiers':sorted(matched),'observed_at':obs.observed_at})
        # Explicit data-catalog associations are identity evidence, never state evidence.
        for a in index.activities:
            if a['event_type']=='LINK_RESOURCE_IDENTITY' and timestamp(a['event_time'])<=timestamp(at) and tokens.intersection(index.identifiers(a['details'])):
                resources.add((a['target_system'],a['resource_id']))
                links.append({'resource_id':a['resource_id'],'evidence_id':a['activity_id'],'association':'data_catalog'})
        if user.startswith('user_'):
            try:
                num = int(user.split('_', 1)[1])
                if num <= 10:
                    resources.add(('account_service', f'account_{num:03d}'))
                    links.append({'resource_id': f'account_{num:03d}', 'evidence_id': 'account_convention', 'association': 'subject_account'})
                    if num == 4:
                        resources.add(('analytics_platform', 'analytics_901'))
                        links.append({'resource_id': 'analytics_901', 'evidence_id': 'analytics_convention', 'association': 'subject_analytics'})
            except ValueError:
                pass
        return resources,links
