# Semantic root-cause investigation

All 25 baseline mismatched public cases were investigated against participant-facing evidence. Expected rows are used only in this evaluation module; no associations or labels from this report enter production inference.

## Root causes grouped across cases

| Cause | Baseline cases |
|---|---:|
| ADDITIONAL_GROUNDED_RESOURCES | 2 |
| CONSERVATIVE_STATUS_CHANGES_CITATION_MODE | 1 |
| MISSING_GROUNDED_IDENTITY_EDGE | 8 |
| NO_RESOURCE_STATE_OBSERVATION | 15 |
| ONLY_LATE_CAPTURE_OR_OBSERVATION | 5 |
| SEQUENCE_CASCADE | 20 |
| UNPROVEN_POLICY_CONDITION | 1 |

Missing identity edges and unavailable observations are different failures. A zero-row read cannot be attached to a person by numeric suffix; an anonymized row cannot be assigned by list position or nearby activity. A later-captured bundle cannot prove earlier availability. Empty snapshot tables without an explicit exhaustive declaration are not global absence proofs.

## General fixes and evidence supporting them

- Relationship discovery: participant SQL search documents contain explicit source_resource_id references. Traverse typed same-subject resource references transitively, require an unambiguous timely system address, and reject contradictory owners. An edge proves association only, never state. Independent cleared-analytics and missing-profile fixtures exercise both outcomes.
- Scope interpretation: participant SQL contains snapshot_scope(origin_system,captured_at), but no complete/exhaustive declaration. Preserve these scope times and keep completeness unspecified. Implement absence proofs only for explicitly complete JSON/SQL scopes with matching subject/category/location and a previously known resource. Test partial, wrong-subject, future and replica counterexamples.
- State interpretation: correlated readback logs carry lookup parameters separately from returned fields. Preserve request context for identity, exclude it from returned-PII tests. Do not treat email_opt_in or generic non-empty message_text as identifiers; include tombstone name fields. Tests isolate these failure modes.
- Support policy: real excerpts describe order/delivery queries; those establish business context. A bare message_pii_scan does not establish shared/agent/order context. Retain proven prior context with provenance without carrying historical PII into current state. An already-redacted record can be verified as redacted without asserting the condition that makes retention necessary; caveats remain explicit.
- Retention/exclusivity: security record presence does not establish a supplied retention interval. Support intervals, aliases and explicit start/duration without inventing defaults. An uploader identity alone does not establish an attachment has only one subject. A retention date alone does not establish an active legal hold. These stricter checks can reduce agreement with underspecified sample annotations.
- Multimodal scoping: screenshots contain selected records, other rows and unrelated history. Retain whole-screen text as provenance but do not assign every identifier on the screen to each selected resource. Only row-level identifiers and explicit catalog associations contribute identity edges.
- Optional model: no provider endpoint/model/credentials are configured. Mocked transport tests exercise grounded-output validation, caching, model revision, missing usage and accounting for invalid outputs. Mock outputs are not real-model predictions or accuracy measurements. No real-model accuracy/cost effect is claimed.

## Positive-state citation gaps in public annotations

No unsupported positive-state citations were found. Some missing future verification targets have empty evidence IDs by contract; these are association/coverage gaps, not incorrect citations.

| Case | Operation | Resource | Cited artifact |
|---|---|---|---|

## Each baseline mismatch

### case_01

Groups: NO_RESOURCE_STATE_OBSERVATION.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_001. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
Baseline policy/evidence gaps: No resource has a grounded association available by audit_at.

### case_02

Groups: NO_RESOURCE_STATE_OBSERVATION.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_002. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
Baseline policy/evidence gaps: No resource has a grounded association available by audit_at.

### case_03

Groups: MISSING_GROUNDED_IDENTITY_EDGE.

- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_9406. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_94 (line 43; trace rb-095409-021): state=ANONYMIZED, observed=2026-09-26T09:54:09Z, captured=2026-09-26T10:38:56Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.

### case_04

Groups: MISSING_GROUNDED_IDENTITY_EDGE, NO_RESOURCE_STATE_OBSERVATION.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_004. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_901. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_56 (customer_analytics_reports): state=ANONYMIZED, observed=2026-09-07T09:45:00Z, captured=2026-09-07T09:45:00Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
Baseline policy/evidence gaps: No resource has a grounded association available by audit_at.

### case_06

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_006. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.

### case_07

Groups: ADDITIONAL_GROUNDED_RESOURCES, NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_007. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Additional supported step: REPORT_REMAINING_RECORD / object_19 / evidence=evidence_46. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.
- Additional supported step: DELETE_RECORD / object_19 / evidence=future check/action. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.
- Additional supported step: VERIFY_RECORD_ABSENT / object_19 / evidence=future check/action. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.

### case_08

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_008. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.

### case_09

Groups: ONLY_LATE_CAPTURE_OR_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_3960. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_06: observed=2026-09-16T08:57:34Z, captured=2026-09-18T11:55:24Z; cutoff=2026-09-16T09:00:00Z.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_4902. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_06: observed=2026-09-16T08:52:59Z, captured=2026-09-18T11:55:24Z; cutoff=2026-09-16T09:00:00Z.

### case_10

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_010. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.

### case_11

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE, UNPROVEN_POLICY_CONDITION.

- Missing logical step: REPORT_EXPOSED_PII / support_platform / support_864. Cause: UNPROVEN_POLICY_CONDITION.
  Evidence evidence_03 (line 46): state=PRESENT, observed=2026-10-01T12:00:00Z, captured=2026-10-01T12:00:00Z, explicit identifier matches=['novak.tomasz@icloud.com']. An unlinked cleared record remains unassigned.
- Missing logical step: REDACT_RECORD / support_platform / support_864. Cause: UNPROVEN_POLICY_CONDITION.
  Evidence evidence_03 (line 46): state=PRESENT, observed=2026-10-01T12:00:00Z, captured=2026-10-01T12:00:00Z, explicit identifier matches=['novak.tomasz@icloud.com']. An unlinked cleared record remains unassigned.
- Missing logical step: VERIFY_RECORD_REDACTED / support_platform / support_864. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_03 (line 46): state=PRESENT, observed=2026-10-01T12:00:00Z, captured=2026-10-01T12:00:00Z, explicit identifier matches=['novak.tomasz@icloud.com']. An unlinked cleared record remains unassigned.
Baseline policy/evidence gaps: ('security_service', 'audit_record_9394'): no condition is established by available evidence; ('support_platform', 'support_864'): no condition is established by available evidence.

### case_17

Groups: ADDITIONAL_GROUNDED_RESOURCES, SEQUENCE_CASCADE.

- Additional supported step: VERIFY_RECORD_ABSENT / account_6523 / evidence=future check/action. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.
- Additional supported step: VERIFY_RECORD_REDACTED / tombstone_17 / evidence=future check/action. Do not suppress a separately catalog-linked copy or historical resource merely to match a shorter sample array.
Baseline policy/evidence gaps: ('security_service', 'audit_record_1797'): no condition is established by available evidence.

### case_18

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_5521. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_6645. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.

### case_20

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_5037. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_5569. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.

### case_21

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_6440. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (profile_lookups): state=ABSENT, observed=2026-09-15T09:31:19Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_5335. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (customer_analytics_profiles): state=ANONYMIZED, observed=2026-09-15T09:34:42Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_22

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_4990. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
Baseline policy/evidence gaps: ('security_service', 'audit_record_3482'): no condition is established by available evidence; ('security_service', 'audit_record_3482'): no condition is established by available evidence.

### case_23

Groups: NO_RESOURCE_STATE_OBSERVATION, ONLY_LATE_CAPTURE_OR_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_410. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_4128. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_24

Groups: ONLY_LATE_CAPTURE_OR_OBSERVATION.

- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_7095. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_25

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_3136. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (profile_lookups): state=ABSENT, observed=2026-09-15T09:31:40Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_1895. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (customer_analytics_profiles): state=ANONYMIZED, observed=2026-09-15T09:58:44Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_26

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_5684. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (profile_lookups): state=ABSENT, observed=2026-09-15T09:01:48Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-09T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4566. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (customer_analytics_profiles): state=ANONYMIZED, observed=2026-09-15T11:29:16Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_27

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_3866. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (profile_lookups): state=ABSENT, observed=2026-09-15T09:59:48Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-17T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4574. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (customer_analytics_profiles): state=ANONYMIZED, observed=2026-09-15T10:07:38Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_28

Groups: MISSING_GROUNDED_IDENTITY_EDGE, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_5482. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (profile_lookups): state=ABSENT, observed=2026-09-15T11:07:16Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
- Missing logical step: VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_6077. Cause: MISSING_GROUNDED_IDENTITY_EDGE.
  Evidence evidence_92 (customer_analytics_profiles): state=ANONYMIZED, observed=2026-09-15T11:44:55Z, captured=2026-09-15T11:44:55Z, explicit identifier matches=none. An unlinked cleared record remains unassigned.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_29

Groups: NO_RESOURCE_STATE_OBSERVATION, ONLY_LATE_CAPTURE_OR_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_7012. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_3954. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_30

Groups: NO_RESOURCE_STATE_OBSERVATION, ONLY_LATE_CAPTURE_OR_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_4163. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
- Missing logical step: VERIFY_RECORD_PRESENT / security_service / audit_record_1707. Cause: ONLY_LATE_CAPTURE_OR_OBSERVATION.
  Excluded evidence_02: observed=2026-09-15T12:00:00Z, captured=2026-09-17T12:00:00Z; cutoff=2026-09-15T12:00:00Z.

### case_31

Groups: CONSERVATIVE_STATUS_CHANGES_CITATION_MODE, NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_4857. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
Baseline policy/evidence gaps: ('security_service', 'audit_record_6909'): no condition is established by available evidence.

### case_32

Groups: NO_RESOURCE_STATE_OBSERVATION, SEQUENCE_CASCADE.

- Missing logical step: VERIFY_RECORD_ABSENT / account_service / account_8858. Cause: NO_RESOURCE_STATE_OBSERVATION.
  No state observation of this resource was found. An operation claim or an empty undeclared scope is insufficient.
Baseline policy/evidence gaps: ('security_service', 'audit_record_7068'): no condition is established by available evidence.

