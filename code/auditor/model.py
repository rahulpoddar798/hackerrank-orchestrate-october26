from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASES = {
    "FINDING": ["REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"],
    "REMEDIATION": ["DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"],
    "VERIFICATION": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED", "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"],
}
STATES = dict(zip(sum(PHASES.values(), []), ["PRESENT", "PRESENT", "ACTIVE", "ACTIVE", "DISABLED", "BLOCKED", "ABSENT", "REDACTED", "ANONYMIZED", "ABSENT", "PRESENT", "REDACTED", "ANONYMIZED", "DISABLED", "BLOCKED"]))
STEP_FIELDS = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}

def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def normalize(value: Any) -> str:
    s = str(value).strip().casefold()
    if re.fullmatch(r"\+?[\d ()-]{8,}", s):
        return re.sub(r"\D", "", s)
    return s

def leaves(obj: Any, path: str = ""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, obj

@dataclass
class Observation:
    system: str
    resource: str
    category: str
    state: str
    observed_at: str
    captured_at: str
    evidence_id: str
    values: dict[str, Any] = field(default_factory=dict)
    identifiers: list[str] = field(default_factory=list)
    origin: str = ""
    coverage: str = "explicit_record"
    location: str = "primary"
    confidence: float = 1.0
    ambiguity: list[str] = field(default_factory=list)
    provenance: str = ""
    claim: bool = False
    available_at: str = ""

    @property
    def key(self):
        return self.system, self.resource

    def available(self, at: str) -> bool:
        return timestamp(self.captured_at) <= timestamp(at) and timestamp(self.observed_at) <= timestamp(at) and (not self.available_at or timestamp(self.available_at)<=timestamp(at))

    def to_dict(self):
        return asdict(self)

def step_sort(s):
    return list(PHASES).index(s["phase"]), PHASES[s["phase"]].index(s["operation"]), s["system_id"], s["resource_id"]
