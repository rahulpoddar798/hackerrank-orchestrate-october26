"""Extract explicit recreation dependencies without interpreting resource names."""
from __future__ import annotations
from .model import leaves

def analyze_dependencies(index,keys,at,steps):
    resource_keys={rid:key for key in sorted(keys) for rid in [key[1]]}
    edges=[]
    remediations={s['resource_id']:s for s in steps if s['phase']=='REMEDIATION'}
    for key in sorted(keys):
        for obs in index.by_resource.get(key,[]):
            if not obs.available(at): continue
            for path,value in leaves(obs.values):
                field=path.rsplit('.',1)[-1].split('[')[0]
                if field in {'source_resource_id','upstream_resource_id','depends_on','source_resource_ids'} and isinstance(value,str) and value in resource_keys:
                    edges.append({'source_resource':value,'downstream_resource':obs.resource,'evidence_id':obs.evidence_id,'relationship':'explicit copy/reference'})
    guards=[s for s in remediations.values() if s['operation'] in {'DISABLE_DATA_FLOW','BLOCK_RESTORE'}]
    for guard in guards:
        for s in remediations.values():
            if s['operation'] in {'DELETE_RECORD','REDACT_RECORD','ANONYMIZE_RECORD'}:
                edges.append({'before':guard['resource_id'],'after':s['resource_id'],'relationship':'prevent subject data recreation before record treatment'})
    # Each destructive action is after all guards under the mandated public order.
    positions={s['resource_id']:i for i,s in enumerate(steps) if s['phase']=='REMEDIATION'}
    violations=[e for e in edges if 'before' in e and positions[e['before']]>=positions[e['after']]]
    return {'edges':edges,'guard_order_violations':violations,'serialization':'public phase/operation/system/resource order'}
