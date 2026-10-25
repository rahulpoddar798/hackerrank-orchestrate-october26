from __future__ import annotations
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path
from .model import Observation, rows, leaves, normalize, timestamp
from .documents import ocr, pdf_pages, render_pdf
from .scope import Coverage, explicit_complete

# Schema semantics, never resource-ID prefixes or case-specific associations.
COLLECTIONS = {
    "customer_profiles": ("account_service", "USER_PROFILE"),
    "profile_lookups": ("account_service", "USER_PROFILE"),
    "customer_search_documents": ("search_service", "SEARCH_INDEX_ENTRY"),
    "index_queries": ("search_service", "SEARCH_INDEX_ENTRY"),
    "customer_analytics_reports": ("analytics_platform", "ANALYTICS_PROFILE"),
    "customer_analytics_profiles": ("analytics_platform", "ANALYTICS_PROFILE"),
    "support_conversations": ("support_platform", "SUPPORT_MESSAGE"),
    "support_records": ("support_platform", "SUPPORT_MESSAGE"),
    "tickets": ("support_platform", "SUPPORT_MESSAGE"),
    "support_attachments": ("support_platform", "SUPPORT_ATTACHMENT"),
    "customer_exports": ("export_service", "USER_EXPORT"),
    "customer_export_jobs": ("export_service", "USER_EXPORT"),
    "exports": ("export_service", "USER_EXPORT"),
    "security_audit_events": ("security_service", "SECURITY_AUDIT_LOG"),
    "audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "connector_configurations": ("integration_service", "DATA_FLOW"),
    "connectors": ("integration_service", "DATA_FLOW"),
    "backup_catalog": ("backup_service", "BACKUP_ARCHIVE"),
    "restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "account_tombstones": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "deleted_account_references": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "email_delivery_logs": ("email_delivery_service", "EMAIL_DELIVERY_LOG"),
    "marketing_profiles": ("marketing_service", "MARKETING_PROFILE"),
    "profile_cache": ("cache_service", "CACHE_ENTRY"),
    "ticket_attachments": ("support_platform", "SUPPORT_ATTACHMENT"),
    "deleted_customer_references": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "retained_order_records": ("legal_service", "LEGAL_HOLD_RECORD"),
    "backup_restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "connector_subscriptions": ("integration_service", "DATA_FLOW"),
    "security_audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "customer_profiles_primary": ("account_service", "USER_PROFILE"),
    "customer_profiles_failover_replica": ("account_service", "USER_PROFILE"),
    "search_documents_primary": ("search_service", "SEARCH_INDEX_ENTRY"),
}
EVENT_CATEGORIES = [
    ("profile_lookup", "USER_PROFILE"), ("index_query", "SEARCH_INDEX_ENTRY"),
    ("analytics", "ANALYTICS_PROFILE"), ("attachment", "SUPPORT_ATTACHMENT"),
    ("contact_query", "SECONDARY_IDENTIFIER"), ("contact_lookup", "SECONDARY_IDENTIFIER"),
    ("message", "SUPPORT_MESSAGE"), ("support_ticket", "SUPPORT_MESSAGE"),
    ("export_", "USER_EXPORT"), ("audit_record", "SECURITY_AUDIT_LOG"),
    ("connector", "DATA_FLOW"), ("restore_", "BACKUP_ARCHIVE"),
]
NULLS = {"", "null", "none", "[redacted]", "redacted", "no direct identifier", "-"}
ISO = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z"

def meaningful(v):
    return v is not None and normalize(v) not in NULLS

def bool_value(v):
    if isinstance(v, bool): return v
    return {"true":True,"false":False,"1":True,"0":False,"yes":True,"no":False}.get(str(v).casefold())

def infer_state(category: str, values: dict, explicit: str = "") -> str:
    material = {k:v for k,v in values.items() if k not in {'_request_context','screen_text','_source_text'}}
    flat = {p.rsplit(".",1)[-1]: v for p,v in leaves(material)}
    explicit = str(explicit).upper()
    if explicit in {"NOT_FOUND", "ABSENT", "DELETED"}: return "ABSENT"
    if flat.get("status_code") == 404 or str(flat.get("rows")) == "0" or str(flat.get("http_status")) == "404": return "ABSENT"
    if category == "DATA_FLOW":
        enabled = bool_value(flat.get("enabled", flat.get("scheduler_registered")))
        return "ACTIVE" if explicit == "ACTIVE" or enabled is True else "DISABLED" if explicit == "DISABLED" or enabled is False else "UNKNOWN"
    if category == "BACKUP_ARCHIVE":
        allowed = bool_value(flat.get("restore_allowed", flat.get("allowed")))
        if flat.get('decision') in {'deny','blocked'} or bool_value(flat.get('deletion_block')) is True: return 'BLOCKED'
        if bool_value(flat.get('eligible')) is True and bool_value(flat.get('deletion_block')) is False: return 'ACTIVE'
        return "ACTIVE" if explicit == "ACTIVE" or allowed is True else "BLOCKED" if explicit == "BLOCKED" or allowed is False else "PRESENT"
    if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY", "SUPPORT_MESSAGE", "EMAIL_DELIVERY_LOG", "ACCOUNT_TOMBSTONE"}:
        personal_fields = {'email','email_hash','phone','full_name','requester_name','display_name','requester_email','requester_phone','owner_email','owner_phone','customer_email','recipient_email','matched_value'}
        if category=='ACCOUNT_TOMBSTONE': personal_fields.add('name')
        direct = [(p,v) for p,v in leaves(material) if p.rsplit('.',1)[-1] in personal_fields]
        # A message body is not PII merely because it is non-empty. Preserve
        # non-identifying shared order/agent context after contact fields are cleared.
        for p,v in leaves(material):
            if p.rsplit('.',1)[-1] in {'message_text','message_excerpt'} and isinstance(v,str):
                if re.search(r'[\w.+-]+@[\w.-]+|\+\d[\d ()-]{7,}',v):direct.append((p,v))
        if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
            direct += [(p,v) for p,v in leaves(values) if p.rsplit(".",1)[-1] in {"user_id", "customer_reference", "subject_reference"}]
        exposed = any(meaningful(v) for p,v in direct)
        if exposed: return "PRESENT"
        if direct or explicit in {"ANONYMIZED", "REDACTED"}:
            return "ANONYMIZED" if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"} else "REDACTED"
        if explicit not in {'IDENTIFIABLE','FOUND','PRESENT'}: return 'UNKNOWN'
    return "PRESENT"

def parse_kv(line):
    return {m[0]:m[1] if m[1] != "" else m[2] for m in re.findall(r'([A-Za-z_][\w.-]*)=(?:"((?:\\.|[^"\\])*)"|([^\s|]+))',line)}

class EvidenceIndex:
    def __init__(self, dataset: Path, cache: Path):
        self.dataset, self.cache = dataset.resolve(), cache
        self.activities = rows(dataset / "system_activity.csv")
        self.identities = rows(dataset / "user_identities.csv")
        self.audit = rows(dataset / "user_audit_log.csv")
        self.manifest = rows(dataset / "evidence_files.csv")
        self.observations: list[Observation] = []
        self.diagnostics = []
        self.inventory = []
        self.document_facts=[]
        self.coverage=[]
        self.coverage_proofs=[]
        self.vocabulary = set()
        for row in self.identities:
            self.vocabulary.update(normalize(row[k]) for k in ["user_id","email","phone","email_hash"] if row.get(k))
        for row in self.audit:
            if row["field_name"] != "name":
                self.vocabulary.update(normalize(row[k]) for k in ["old_value","new_value"] if row[k])
        self.resource_systems = collections.defaultdict(collections.Counter)
        for a in self.activities:
            if a["event_type"] in {"DELETE_RECORD","ANONYMIZE_RECORD","REDACT_RECORD","RETAIN_RECORD","BLOCK_RESTORE","CHECK_RESTORE_ACCESS","CHECK_DATA_FLOW","DISABLE_DATA_FLOW","LINK_RESOURCE_IDENTITY"}:
                self.resource_systems[a["resource_id"]][a["target_system"]] += 1
        self.known_resources = set(a["resource_id"] for a in self.activities)
        self.identifier_pattern = re.compile(r"(?<![\w@.+-])(?:"+"|".join(re.escape(x) for x in sorted(self.vocabulary,key=lambda x:(-len(x),x)) if len(x)>3)+r")(?![\w@.+-])", re.I)
        self.by_resource = collections.defaultdict(list)
        self._text_patterns = {}

    def identifiers(self, obj):
        found = set()
        for path,v in leaves(obj):
            if path.split('.',1)[0] in {'screen_text','_source_text'}:
                continue
            n=normalize(v)
            if n in self.vocabulary: found.add(n)
            if isinstance(v,str):
                found.update(normalize(m.group()) for m in self.identifier_pattern.finditer(v))
        return sorted(found)

    def add(self, meta, resource, system, category, values, observed=None, state="", location="primary", provenance="", confidence=1.0, claim=False,available_at=""):
        if not resource or not system or not category:
            self.diagnostics.append({"evidence_id":meta["file_id"],"reason":"unresolved schema","resource":resource,"system":system,"category":category})
            return
        observation=Observation(system,str(resource),category,infer_state(category,values,state),observed or meta["captured_at"],meta["captured_at"],meta["file_id"],values,self.identifiers(values),meta.get("origin",""),location=location,provenance=provenance,confidence=confidence,claim=claim)
        observation.available_at=available_at
        self.observations.append(observation)
        self.by_resource[observation.key].append(observation)
        self.resource_systems[resource][system] += 3
        self.known_resources.add(str(resource))

    def ingest(self):
        # Parse structured records first; images can ground references to those records.
        priority={".json":0,".sql":1,".csv":2,".log":3,".txt":4,".pdf":5,".png":6}
        for m in sorted(self.manifest,key=lambda m:(priority.get(Path(m["file_path"]).suffix,99),m["file_id"])):
            path=(self.dataset/m["file_path"]).resolve()
            if not path.is_relative_to(self.dataset): raise ValueError("Evidence path escapes dataset")
            before=len(self.observations)
            suffix=path.suffix.lower()
            info={**m,"format":suffix,"bytes":path.stat().st_size}
            if suffix==".json":
                obj=json.loads(path.read_text(encoding="utf8")); info["schema"]=sorted(obj) if isinstance(obj,dict) else ["array"]
                self.json_records(obj,m)
            elif suffix==".sql": info["schema"]=self.sql(path,m)
            elif suffix==".csv":
                records=rows(path); info["schema"]=list(records[0]) if records else []; self.json_records({"records":records},m)
            elif suffix==".log": info["schema"]=self.logs(path,m)
            elif suffix==".txt": self.text_records(path.read_text(encoding="utf8"),m); info["schema"]=["pipe_delimited_shift_handover"]
            elif suffix==".pdf":
                pages=pdf_pages(path); info["schema"]=["pdf_pages",len(pages)]; self.document("\n".join(pages),m)
                self.document_facts.append({**m,'pages':pages,'identifiers':self.identifiers(pages),'type':'pdf','resource_associations_are_separate':True})
                if not any(x.strip() for x in pages):
                    for rendered in render_pdf(path,self.cache/"pdf"):
                        self.document(ocr(rendered,self.cache)["text"],m)
            elif suffix==".png":
                data=ocr(path,self.cache); info["schema"]=[data["engine"],"layout_words"]
                self.document_facts.append({**m,'extraction':data,'type':'screenshot'})
                self.screenshot(data,m)
            else: raise ValueError("Unsupported evidence: "+suffix)
            info["observations"]=len(self.observations)-before
            self.inventory.append(info)
        return self

    def json_records(self,obj,m,system="",collection="",observed="",location="primary"):
        if isinstance(obj,list):
            for r in obj: self.json_records(r,m,system,collection,observed,location)
            return
        if not isinstance(obj,dict): return
        observed=obj.get("observed_at",obj.get("recorded_at",obj.get("captured_at",observed)))
        system=obj.get("data_store",obj.get("system",system))
        collection=obj.get("collection",collection)
        if isinstance(obj.get('records'),list):
            declaration=obj.get('coverage',obj.get('scope',{}))
            if isinstance(declaration,dict):
                default_sys,category=COLLECTIONS.get(collection,(system,''))
                category=obj.get('record_type',obj.get('data_category',category))
                if category and (system or default_sys):
                    self.coverage_proofs.append(Coverage(system or default_sys,category,observed or m['captured_at'],m['captured_at'],m['file_id'],explicit_complete(declaration),
                        tuple(str(r['resource_id']) for r in obj['records'] if isinstance(r,dict) and r.get('resource_id')),
                        tuple(self.identifiers(declaration)),location,'explicit JSON coverage declaration'))
        if obj.get("resource_id"):
            default_sys,category=COLLECTIONS.get(collection,(system,""))
            category=obj.get("record_type",obj.get("data_category",category))
            vals=dict(obj)
            # A search response is a scoped observation, not all records in a global index.
            if "hits" in obj:
                if obj["hits"].get("total",0)==0: vals["rows"]=0
                elif obj["hits"].get("documents"): vals.update(obj["hits"]["documents"][0])
            self.add(m,obj["resource_id"],system or default_sys,category,vals,observed,state=obj.get("result",""),location=location,provenance=collection)
            return
        for k,v in obj.items():
            if k=="service_exports":
                for sys,groups in v.items():
                    for group,rr in groups.items():
                        catgroup="customer_analytics_profiles" if group=="profiles" and "analytics" in sys else group
                        self.json_records(rr,m,sys,catgroup,observed,location)
            elif isinstance(v,(list,dict)):
                self.json_records(v,m,system,collection,observed,location)

    def sql(self,path,m):
        text=path.read_text(encoding="utf8")
        db=sqlite3.connect(":memory:")
        # No external databases, filesystem access, extensions, or unbounded queries.
        allowed={getattr(sqlite3,n) for n in ["SQLITE_CREATE_TABLE","SQLITE_INSERT","SQLITE_READ","SQLITE_SELECT","SQLITE_TRANSACTION","SQLITE_FUNCTION","SQLITE_UPDATE","SQLITE_CREATE_INDEX","SQLITE_REINDEX"] if hasattr(sqlite3,n)}
        def auth(action,a,b,c,d):
            if action==sqlite3.SQLITE_PRAGMA and a.lower()=="foreign_keys": return sqlite3.SQLITE_OK
            if action==sqlite3.SQLITE_FUNCTION and (b or a or "").lower()=="load_extension": return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY
        db.set_authorizer(auth)
        budget=[0]
        def progress():
            budget[0]+=1
            return int(budget[0]>20000)
        db.set_progress_handler(progress,1000)
        try: db.executescript(text)
        finally: db.set_authorizer(None)
        db.row_factory=sqlite3.Row
        schema={}
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        scope_rows=[dict(r) for r in db.execute('SELECT * FROM snapshot_scope')] if 'snapshot_scope' in tables else []
        def observation_time(system,table):
            candidates={r['captured_at'] for r in scope_rows if r.get('origin_system')==system and r.get('captured_at') and (not r.get('table_name') or r['table_name']==table)}
            return next(iter(candidates)) if len(candidates)==1 else m['captured_at']
        for table in tables:
            quoted='"'+table.replace('"','""')+'"'
            records=[dict(r) for r in db.execute("SELECT * FROM "+quoted)]
            schema[table]=[r[1] for r in db.execute("PRAGMA table_info("+quoted+")")]
            self.coverage.append({'evidence_id':m['file_id'],'table':table,'rows':len(records),'captured_at':m['captured_at'],'completeness':'unspecified; absence not inferred'})
            default_system,default_category=COLLECTIONS.get(table,('',''))
            for scope in scope_rows:
                if scope.get('origin_system')!=default_system or not default_category:continue
                if scope.get('table_name') and scope['table_name']!=table:continue
                self.coverage_proofs.append(Coverage(default_system,default_category,scope.get('captured_at',m['captured_at']),m['captured_at'],m['file_id'],explicit_complete(scope),
                    tuple(str(r['resource_id']) for r in records if r.get('resource_id')),tuple(self.identifiers(scope)),
                    table if 'replica' in table else 'primary','SQL snapshot_scope/table '+table))
            for r in records:
                if "record_json" in r:
                    val=json.loads(r["record_json"])
                    val['_record_updated_at']=r.get('updated_at')
                    system,category=COLLECTIONS.get(r["collection_name"],(r["origin_system"],""))
                    self.add(m,r["resource_id"],r["origin_system"],category,val,r.get("observed_at",observation_time(r['origin_system'],table)),location=table if 'replica' in table else 'primary',provenance="SQL table "+table)
                elif table != 'snapshot_scope':
                    system,category=COLLECTIONS.get(table,("",""))
                    if not category and "tombstone" in table: system,category="identity_service","ACCOUNT_TOMBSTONE"
                    self.add(m,r.get("resource_id",r.get("id")),system,category,r,r.get('observed_at',observation_time(system,table)),location=table if 'replica' in table else 'primary',provenance="SQL table "+table)
        db.close()
        # Missing rows are deliberately not turned into absence observations.
        return schema

    def logs(self,path,m):
        contexts={}; fields=set(); events=set()
        for number,line in enumerate(path.read_text(encoding="utf8").splitlines(),1):
            tm=re.search(ISO,line)
            if not tm: continue
            if re.match(ISO+r" \{",line): r=json.loads(line[line.index("{"):])
            else:
                r=parse_kv(line)
                if "message" in r:
                    inner=r["message"].replace('\\"','"'); r.update(parse_kv(inner))
                if " | " in line:
                    parts=line.split(" | ")
                    if len(parts)>=6: r.update(service=parts[2],trace_id=parts[3],event=parts[4])
                b=re.match(ISO+r" \[\w+\] \[([^]]+)\] \[([^]]+)\] (\w+):",line)
                if b: r.update(service=b[1],trace_id=b[2],event=b[3])
                s=re.match(ISO+r" <\d+>1 \S+ (\S+) (\S+) - -",line)
                if s: r.update(service=s[1],trace_id=s[2])
                if r.get("function"): r["service"]=r["function"]; r["trace_id"]=r.get("requestId","")
            fields.update(r); event=r.get("event",""); events.add(event)
            trace=r.get("trace_id","")
            ctx=contexts.setdefault(trace,{}) if trace else {}
            if event.endswith("_started"): ctx.update(r); continue
            resource=r.get("resource_id")
            if not resource: continue
            # Lookup parameters link a readback to a subject but are not returned PII.
            values={**r,'_request_context':dict(ctx)} if ctx else dict(r)
            category=r.get("record_type",next((cat for token,cat in EVENT_CATEGORIES if token in event),""))
            if not category: continue
            # Only actual reads, observed hits and identifier scans establish state.
            if not any(t in event for t in ["completed","pii_scan","identity_scan","heartbeat","config_loaded","profile_read","message_read","candidate_evaluated","contact_lookup","record_lookup"]): continue
            sys=r.get("system",r.get("service",""))
            if sys=="support_replica": sys="support_platform"
            self.add(m,resource,sys,category,values,tm.group(),r.get("result",""),provenance=f"line {number}; trace {trace}")
        return {"fields":sorted(fields),"events":sorted(events)}

    def text_records(self,text,m):
        for n,line in enumerate(text.splitlines(),1):
            parts=[s.strip() for s in line.lstrip("- ").split("|")]
            if len(parts)>=6 and re.fullmatch(ISO,parts[0]):
                self.add(m,parts[2],parts[1],parts[3],{"subject_reference":parts[5],"record_type":parts[3],"result":parts[4]},parts[0],parts[4],provenance=f"line {n}")

    def known_in_text(self,text,items):
        # OCR sometimes substitutes spaces for underscores; only exact known IDs can be repaired.
        items=tuple(sorted(items))
        if not items: return []
        if items not in self._text_patterns:
            self._text_patterns[items]=re.compile(r"(?<![\w])(?:"+'|'.join(re.escape(item).replace('_',r'[_ ]') for item in items)+r")(?![\w])",re.I)
        return sorted({m.group().replace(' ','_').lower() for m in self._text_patterns[items].finditer(text)})

    def document(self,text,m):
        resources=self.known_in_text(text,self.known_resources)
        # A business document can introduce its own resource reference. Its label,
        # rather than its identifier's spelling, determines category and system.
        support_ref=re.search(r'Support reference[^\n]*/\s*([\w.-]+)',text,re.I)
        if support_ref and support_ref[1] not in resources: resources.append(support_ref[1])
        vals={"document_text":text}
        for a in self.activities:
            if a['event_type']!='LINK_RESOURCE_IDENTITY': continue
            ref=re.search(r'\(([^)]+)\)',a['details'])
            if ref and ref[1] in text and a['target_system']=='export_service':
                self.add(m,a['resource_id'],a['target_system'],'USER_EXPORT',{**vals,'catalog_association':a['details']},provenance='PDF content joined to '+a['activity_id'],available_at=a['event_time'])
        for resource in resources:
            systems=self.resource_systems[resource]
            system=systems.most_common(1)[0][0] if systems else ""
            category=""
            if "attachment" in text.casefold() and "support reference" in text.casefold(): category="SUPPORT_ATTACHMENT"; system='support_platform'
            elif "retain until" in text.casefold() and "journal" in text.casefold():
                category="SECURITY_AUDIT_LOG"; system="security_service"
                until=re.search(r"retain until (\d{2} \w{3} \d{4})",text,re.I)
                if until: vals["retention_until"]=__import__('datetime').datetime.strptime(until[1],"%d %b %Y").strftime("%Y-%m-%dT23:59:59Z")
            if category: self.add(m,resource,system,category,vals,provenance="PDF text",confidence=.95)
        if not resources:
            self.diagnostics.append({"evidence_id":m["file_id"],"reason":"document contains business references but no grounded canonical resource ID","extracted_characters":len(text)})

    def screenshot(self,data,m):
        text=data["text"]
        lines=[]
        words=[w for line in data.get("lines",[]) for w in line["words"]]
        # Recover horizontal table rows from OCR coordinates, rather than OCR reading order.
        groups=[]
        for w in sorted(words,key=lambda w:(w["y"],w["x"])):
            group=next((g for g in groups if abs(g[0]["y"]-w["y"])<7),None)
            if group is None: groups.append([w])
            else: group.append(w)
        lines=[(" ".join(w["text"] for w in sorted(g,key=lambda w:w["x"])),min(w["y"] for w in g)) for g in groups]
        low=text.casefold()
        context=""
        for token,cat in [("customer reference registry","ACCOUNT_TOMBSTONE"),("audience operations","MARKETING_PROFILE"),("customer operations","USER_PROFILE"),("pulse analytics","ANALYTICS_PROFILE"),("helpline console","SUPPORT_MESSAGE"),("search console","SEARCH_INDEX_ENTRY"),("bridgeops","DATA_FLOW"),("download center","USER_EXPORT"),("recovery manager","BACKUP_ARCHIVE"),("signed events","SECURITY_AUDIT_LOG")]:
            if token in low: context=cat; break
        matched=0
        for line,y in lines:
            candidates=self.known_in_text(line,self.known_resources)
            for resource in candidates:
                # Header identifies a selected record, table rows identify individual copies.
                if y>650: continue
                existing=[o for o in self.observations if o.resource==resource and o.available(m["captured_at"])]
                system=self.resource_systems[resource].most_common(1)[0][0] if self.resource_systems[resource] else ""
                category=context or (existing[-1].category if existing else "")
                if not category: continue
                vals={"screen_row":line}
                stable_ids=self.known_in_text(line,[p['user_id'] for p in self.identities])
                if stable_ids:vals['observed_identifiers']=stable_ids
                if y<180 or y<360 and "raw" in line.casefold():
                    vals["screen_text"]=text
                if category=="DATA_FLOW": vals["enabled"]=True if "continuous" in low else None
                if category=="BACKUP_ARCHIVE": vals["archive_present"]=True
                self.add(m,resource,system,category,vals,state="PRESENT",provenance=f"OCR row y={y}",confidence=.8)
                matched+=1
        if context=="ACCOUNT_TOMBSTONE":
            subjects=self.known_in_text(text,[r["user_id"] for r in self.identities])
            for a in self.activities:
                if a["event_type"]!="LINK_RESOURCE_IDENTITY": continue
                if any(s in self.identifiers(a["details"]) for s in subjects):
                    self.add(m,a["resource_id"],a["target_system"],context,{"subject_reference":subjects[0],"screen_text":text},state="REDACTED",provenance="OCR reference registry joined to "+a['activity_id'],confidence=.8,available_at=a['event_time']); matched+=1
        for a in self.activities:
            if a['event_type']!='LINK_RESOURCE_IDENTITY' or 'belongs only' not in a['details']: continue
            ref=re.search(r'\(([^)]+)\)',a['details'])
            if ref and ref[1] in text:
                self.add(m,a['resource_id'],a['target_system'],'SUPPORT_ATTACHMENT',{'filename':ref[1],'catalog_association':a['details'],'subject_reference':a['details']},provenance='OCR object row joined to '+a['activity_id'],confidence=.8,available_at=a['event_time']);matched+=1
        if not matched: self.diagnostics.append({"evidence_id":m["file_id"],"reason":"OCR extracted text but no explicit canonical resource association","extracted_characters":len(text)})
