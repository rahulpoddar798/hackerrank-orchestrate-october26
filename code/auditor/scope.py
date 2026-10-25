"""Absence proofs require explicit completeness, matching predicates, and known IDs."""
from __future__ import annotations
from dataclasses import dataclass
from .model import Observation, normalize, timestamp, leaves


@dataclass
class Coverage:
    system: str
    category: str
    observed_at: str
    captured_at: str
    evidence_id: str
    complete: bool
    resource_ids: tuple[str, ...]
    subjects: tuple[str, ...] = ()
    location: str = 'primary'
    provenance: str = ''
    available_at: str = ''

    def available(self, at):
        return all(timestamp(t) <= timestamp(at) for t in [self.observed_at,self.captured_at,self.available_at] if t)


def explicit_complete(metadata):
    """Only positive completeness declarations count, never empty records alone."""
    if not isinstance(metadata, dict):
        return False
    for key in ['complete','is_complete','exhaustive']:
        if metadata.get(key) is True or metadata.get(key) == 1 or str(metadata.get(key)).casefold() == 'true':
            return True
    return str(metadata.get('completeness','')).casefold() in {'complete','exhaustive'}


def scoped_absences(index, keys, subject_tokens, at):
    proofs = []
    for coverage in getattr(index,'coverage_proofs',[]):
        if not coverage.complete or not coverage.available(at):
            continue
        if coverage.subjects and not set(coverage.subjects).intersection(subject_tokens):
            continue
        for key in keys:
            if key[0] != coverage.system or key[1] in coverage.resource_ids:
                continue
            categories = {o.category for o in index.by_resource.get(key,[]) if o.available(at)}
            if categories != {coverage.category}:
                continue
            # An inventory proves absence of a known record only within its exact scope.
            observation = Observation(key[0],key[1],coverage.category,'ABSENT',coverage.observed_at,coverage.captured_at,coverage.evidence_id,
                {'scope_complete':True,'scope_subjects':list(coverage.subjects),'scope_resources':list(coverage.resource_ids)},
                sorted(subject_tokens.intersection(coverage.subjects)),coverage='declared_complete_scope',location=coverage.location,
                provenance=coverage.provenance,available_at=coverage.available_at)
            proofs.append(observation)
    return proofs
