# Evaluation report

**Quality gate: NOT acceptance-complete.** This implementation produces a validated conservative audit for every request, but unresolved evidence/policy conditions remain. No hidden evaluation labels were accessed. Structural validity is not deletion correctness.

## Public samples (measured)

| Metric | Result |
|---|---:|
| Status accuracy | 32/32 (100.00%) |
| Exact case including status and sequence | 14/32 (43.75%) |
| Exact sequence (array only) | 14/32 (43.75%) |
| Exact step precision | 122/171 (71.35%) |
| Exact step recall | 122/193 (63.21%) |
| Field accuracy | 1118/1386 (80.66%) |

Exact steps compare all seven fields, including step number and evidence ID, as multisets. Field comparison aligns by phase/system/resource/operation and counts each missing or extra step as seven incorrect fields. Exact case requires identical arrays and status; sequence accuracy compares arrays alone. sample_output.csv is read only by evaluation/main.py and evaluation-only forensic analysis, never by production inference.

## Full evaluation input run

Processed 518 requests in 21.735 seconds on this machine. Produced 2692 steps. Status counts: COMPLETE=146, INCOMPLETE=362, NOT_APPLICABLE=10.
Schema, unique case coverage, sorting, enum/state combinations, phase/operation order, step numbering, temporal evidence references, and observed citation state validation: True. Validation errors: 0.
Unresolved cases: **14**. Strict mode returns a nonzero exit code and explicitly rejects this run. Conservative mode maps unproven completeness to INCOMPLETE, records each uncertainty, and proposes only supported actions/non-destructive retention-presence safeguards. This mapping is an operational audit fallback, not proof of a policy violation. No hidden full-dataset accuracy can be measured.
Output SHA-256: `da9885bcc38fffc860e7760fb39734c07a5a551af2261c2f044bf53b8eed4476`.

## Additional independent fixtures and metamorphic tests

Ran 52 tests: 52 passed, 0 failures, 0 errors. Fixtures use fictional example.test identities and opaque resource IDs; they do not read the public sample answers.

| Independent scenario | Expected behavior tested |
|---|---|
| Historical identity and reassigned email | Resolve assignment at request time; reject a true simultaneous collision |
| Replica drift | Absent primary plus present regional replica is incomplete |
| Post-deletion recreation | Later observed presence overrides earlier absence |
| Backup and retention | Block restores before record changes; retain only with established supplied period |
| Account tombstones | Keep stable reference, redact exposed direct identifiers; recognize explicit null fields |
| Incomplete/conflicting evidence | Missing fields do not prove anonymization; simultaneous conflict prevents completeness |
| Multilingual/non-deletion | English, French, Japanese, Chinese deletion and access/correction negations |
| Permitted data flow | Explicit permitted retained-reference payload does not trigger disabling |
| Metamorphic transformations | Case ID changes, resource renaming, email case, and reversed observation order preserve logical decisions |
| Dynamic policy | Replacing a runtime DELETE rule with RETAIN changes treatment without code changes |

## Failures found and general improvements

- Fixed schema aliases for replica tables, tombstones, attachments, legal records, and generic lookup logs.
- Preserved explicit null values; missing fields and cleared fields are different states.
- Correlated started/completed reads by trace and parsed nested cloud JSON, syslog, pipe, bracketed, and key-value logs.
- Added three temporal gates: observation time, source capture time, and catalog-association availability.
- Added collision/reassignment safeguards, replica separation, conflict diagnostics, restore blocking and conditional policy checks.
- Fixed negated correction/information requests and French/Portuguese intent forms using general language rules.
- Added safe future presence checks for conditionally retained records while leaving the missing condition unresolved.
- Distinguished SQL record last-write time from the snapshot observation time, retaining both values.
- Refused destructive plans for ambiguous authorization or reassigned resources, and avoided false PII findings for missing records that must remain redacted/anonymized.
- Added an independent artifact checker that imports no inference code and verifies dataset preservation and packaging.

The semantic improvement pass adds typed temporal relationship traversal, explicitly declared scope proofs, request/record separation, row-scoped screenshot identities, condition-provenance tracking, nonblocking already-transformed-state caveats, and real-vs-mocked model usage accounting. See root_cause_investigation.md for all 25 baseline mismatches and semantic_regression_report.md for measured regressions and every unresolved full-dataset reason.

## Remaining limitations and minimal next actions

1. Many SECURITY_AUDIT_LOG artifacts prove that a record exists but supply no retention-until date. A verification of presence is safe; eligibility for retention remains unproven. Supply authoritative retention metadata before strict acceptance.
2. Some cleared resources have neither direct identifiers nor earlier timely associations. Joining nearby activity events or matching numeric suffixes would fabricate identity links. Supply explicit participant-visible associations for those resources.
3. The supplied SQL scope rows do not declare exhaustive coverage. Missing rows cannot establish absence. The implementation now supports explicit complete-scope proofs, while preserving source scope observation time separately from export capture time.
4. Natural-language extraction and screenshot interpretation are conservative schema adapters, not unrestricted document understanding. PDF business facts are preserved even if no canonical resource can be associated. OCR can misread small IDs; only exact known-ID repairs are permitted.
5. Explicit recreation/reference dependencies are recorded and all flow/restore guards precede record changes. Record serialization follows the public operation/system/resource ordering. More complex delete-after constraints require an explicit execution policy if they conflict with that contract.
6. The optional model fallback has mocked transport tests for schema/quote validation, caching, invalid-output accounting and missing usage. No live provider endpoint/model/credentials are configured, so live-model accuracy and cost effects were not measured. No claim of universal intent accuracy or complete policy-language understanding is made.
7. Independent review here is automated artifact/static verification, supplemented by separate fixture oracles. No independent human or second-agent semantic review was performed.

## Every remaining sample mismatch

| Case | Expected / predicted status | Expected / predicted steps |
|---|---|---:|
| case_03 | COMPLETE / COMPLETE | 3 / 2 |
| case_07 | INCOMPLETE / INCOMPLETE | 4 / 7 |
| case_09 | INCOMPLETE / INCOMPLETE | 5 / 3 |
| case_17 | INCOMPLETE / INCOMPLETE | 5 / 7 |
| case_18 | INCOMPLETE / INCOMPLETE | 14 / 12 |
| case_20 | INCOMPLETE / INCOMPLETE | 8 / 6 |
| case_21 | COMPLETE / COMPLETE | 3 / 1 |
| case_22 | INCOMPLETE / INCOMPLETE | 8 / 7 |
| case_23 | INCOMPLETE / INCOMPLETE | 8 / 6 |
| case_24 | INCOMPLETE / INCOMPLETE | 7 / 6 |
| case_25 | COMPLETE / COMPLETE | 3 / 1 |
| case_26 | COMPLETE / COMPLETE | 6 / 4 |
| case_27 | COMPLETE / COMPLETE | 6 / 4 |
| case_28 | COMPLETE / COMPLETE | 6 / 4 |
| case_29 | INCOMPLETE / INCOMPLETE | 14 / 12 |
| case_30 | INCOMPLETE / INCOMPLETE | 14 / 12 |
| case_31 | COMPLETE / COMPLETE | 3 / 2 |
| case_32 | INCOMPLETE / INCOMPLETE | 5 / 4 |

### Mismatch investigation details

These are evaluation-only expected-vs-observed differences. They are not inference rules or production lookups. Step numbers are included because sequence positions count toward exact matching.

**case_03**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 3:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_9406, evidence=evidence_94).
Predicted but unmatched: none.

**case_07**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:REPORT_REMAINING_RECORD(support_platform/support_001, evidence=evidence_58); 2:DELETE_RECORD(support_platform/support_001, evidence=future); 3:VERIFY_RECORD_ABSENT(account_service/account_007, evidence=future); 4:VERIFY_RECORD_ABSENT(support_platform/support_001, evidence=future).
Predicted but unmatched: 1:REPORT_REMAINING_RECORD(object_storage/object_19, evidence=evidence_46); 2:REPORT_REMAINING_RECORD(support_platform/support_001, evidence=evidence_58); 3:DELETE_RECORD(object_storage/object_19, evidence=future); 4:DELETE_RECORD(support_platform/support_001, evidence=future); 5:VERIFY_RECORD_ABSENT(account_service/account_007, evidence=future); 6:VERIFY_RECORD_ABSENT(object_storage/object_19, evidence=future); 7:VERIFY_RECORD_ABSENT(support_platform/support_001, evidence=future).

**case_09**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 3:VERIFY_RECORD_ABSENT(account_service/account_3960, evidence=future); 4:VERIFY_RECORD_PRESENT(security_service/audit_record_4902, evidence=future); 5:VERIFY_RESTORE_BLOCKED(backup_service/backup_4978, evidence=future).
Predicted but unmatched: 3:VERIFY_RESTORE_BLOCKED(backup_service/backup_4978, evidence=future).

**case_17**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 4:VERIFY_RECORD_PRESENT(security_service/audit_record_1797, evidence=future); 5:VERIFY_RESTORE_BLOCKED(backup_service/backup_3245, evidence=future).
Predicted but unmatched: 4:VERIFY_RECORD_ABSENT(account_service/account_6523, evidence=future); 5:VERIFY_RECORD_PRESENT(security_service/audit_record_1797, evidence=future); 6:VERIFY_RECORD_REDACTED(identity_service/tombstone_17, evidence=future); 7:VERIFY_RESTORE_BLOCKED(backup_service/backup_3245, evidence=future).

**case_18**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 9:VERIFY_RECORD_ABSENT(account_service/account_5521, evidence=future); 10:VERIFY_RECORD_ABSENT(search_service/search_4013, evidence=future); 11:VERIFY_RECORD_PRESENT(security_service/audit_record_6645, evidence=future); 12:VERIFY_RECORD_REDACTED(support_platform/support_5569, evidence=future); 13:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_037, evidence=future); 14:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_4890, evidence=future).
Predicted but unmatched: 9:VERIFY_RECORD_ABSENT(search_service/search_4013, evidence=future); 10:VERIFY_RECORD_REDACTED(support_platform/support_5569, evidence=future); 11:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_037, evidence=future); 12:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_4890, evidence=future).

**case_20**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 5:VERIFY_RECORD_ABSENT(account_service/account_5037, evidence=future); 6:VERIFY_RECORD_ABSENT(search_service/search_4262, evidence=future); 7:VERIFY_RECORD_PRESENT(security_service/audit_record_5569, evidence=future); 8:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_1770, evidence=future).
Predicted but unmatched: 5:VERIFY_RECORD_ABSENT(search_service/search_4262, evidence=future); 6:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_1770, evidence=future).

**case_21**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_6440, evidence=evidence_92); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_3737, evidence=evidence_92); 3:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_5335, evidence=evidence_92).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_3737, evidence=evidence_92).

**case_22**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 5:VERIFY_RECORD_ABSENT(account_service/account_4990, evidence=future); 6:VERIFY_RECORD_ABSENT(search_service/search_8911, evidence=future); 7:VERIFY_RECORD_PRESENT(security_service/audit_record_3482, evidence=future); 8:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_4440, evidence=future).
Predicted but unmatched: 5:VERIFY_RECORD_ABSENT(search_service/search_8911, evidence=future); 6:VERIFY_RECORD_PRESENT(security_service/audit_record_3482, evidence=future); 7:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_4440, evidence=future).

**case_23**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 5:VERIFY_RECORD_ABSENT(account_service/account_410, evidence=future); 6:VERIFY_RECORD_ABSENT(export_service/export_7364, evidence=future); 7:VERIFY_RECORD_ABSENT(search_service/search_898, evidence=future); 8:VERIFY_RECORD_PRESENT(security_service/audit_record_4128, evidence=future).
Predicted but unmatched: 5:VERIFY_RECORD_ABSENT(export_service/export_7364, evidence=future); 6:VERIFY_RECORD_ABSENT(search_service/search_898, evidence=future).

**case_24**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 7:VERIFY_RECORD_PRESENT(security_service/audit_record_7095, evidence=future).
Predicted but unmatched: none.

**case_25**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_3136, evidence=evidence_92); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_451, evidence=evidence_92); 3:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_1895, evidence=evidence_92).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_451, evidence=evidence_92).

**case_26**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_5684, evidence=evidence_92); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_5416, evidence=evidence_92); 3:VERIFY_RECORD_REDACTED(support_platform/support_4715, evidence=evidence_92); 4:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_4566, evidence=evidence_92); 5:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_6244, evidence=evidence_92); 6:VERIFY_RESTORE_BLOCKED(backup_service/backup_3120, evidence=evidence_92).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_5416, evidence=evidence_92); 2:VERIFY_RECORD_REDACTED(support_platform/support_4715, evidence=evidence_92); 3:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_6244, evidence=evidence_92); 4:VERIFY_RESTORE_BLOCKED(backup_service/backup_3120, evidence=evidence_92).

**case_27**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_3866, evidence=evidence_92); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_3830, evidence=evidence_92); 3:VERIFY_RECORD_REDACTED(support_platform/support_4707, evidence=evidence_92); 4:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_4574, evidence=evidence_92); 5:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_2295, evidence=evidence_92); 6:VERIFY_RESTORE_BLOCKED(backup_service/backup_5970, evidence=evidence_92).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_3830, evidence=evidence_92); 2:VERIFY_RECORD_REDACTED(support_platform/support_4707, evidence=evidence_92); 3:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_2295, evidence=evidence_92); 4:VERIFY_RESTORE_BLOCKED(backup_service/backup_5970, evidence=evidence_92).

**case_28**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_5482, evidence=evidence_92); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_9265, evidence=evidence_92); 3:VERIFY_RECORD_REDACTED(support_platform/support_2351, evidence=evidence_92); 4:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_6077, evidence=evidence_92); 5:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_2337, evidence=evidence_92); 6:VERIFY_RESTORE_BLOCKED(backup_service/backup_838, evidence=evidence_92).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_9265, evidence=evidence_92); 2:VERIFY_RECORD_REDACTED(support_platform/support_2351, evidence=evidence_92); 3:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_2337, evidence=evidence_92); 4:VERIFY_RESTORE_BLOCKED(backup_service/backup_838, evidence=evidence_92).

**case_29**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 9:VERIFY_RECORD_ABSENT(account_service/account_7012, evidence=future); 10:VERIFY_RECORD_ABSENT(search_service/search_1993, evidence=future); 11:VERIFY_RECORD_PRESENT(security_service/audit_record_3954, evidence=future); 12:VERIFY_RECORD_REDACTED(support_platform/support_5281, evidence=future); 13:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_5208, evidence=future); 14:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_3827, evidence=future).
Predicted but unmatched: 9:VERIFY_RECORD_ABSENT(search_service/search_1993, evidence=future); 10:VERIFY_RECORD_REDACTED(support_platform/support_5281, evidence=future); 11:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_5208, evidence=future); 12:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_3827, evidence=future).

**case_30**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 9:VERIFY_RECORD_ABSENT(account_service/account_4163, evidence=future); 10:VERIFY_RECORD_ABSENT(search_service/search_9359, evidence=future); 11:VERIFY_RECORD_PRESENT(security_service/audit_record_1707, evidence=future); 12:VERIFY_RECORD_REDACTED(support_platform/support_6477, evidence=future); 13:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_3697, evidence=future); 14:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_8524, evidence=future).
Predicted but unmatched: 9:VERIFY_RECORD_ABSENT(search_service/search_9359, evidence=future); 10:VERIFY_RECORD_REDACTED(support_platform/support_6477, evidence=future); 11:VERIFY_RECORD_ANONYMIZED(analytics_platform/analytics_3697, evidence=future); 12:VERIFY_DATA_FLOW_DISABLED(integration_service/data_flow_8524, evidence=future).

**case_31**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 1:VERIFY_RECORD_ABSENT(account_service/account_4857, evidence=evidence_51); 2:VERIFY_RECORD_PRESENT(security_service/audit_record_6909, evidence=evidence_51); 3:VERIFY_RECORD_REDACTED(identity_service/tombstone_440, evidence=evidence_51).
Predicted but unmatched: 1:VERIFY_RECORD_PRESENT(security_service/audit_record_6909, evidence=evidence_51); 2:VERIFY_RECORD_REDACTED(identity_service/tombstone_440, evidence=evidence_51).

**case_32**

The observed plan differs from expected coverage/citations/positions. Extra catalog-linked records are preserved when supported; missing cleared-resource associations are not filled using resource-name or event-time proximity.

Expected but unmatched: 3:VERIFY_RECORD_ABSENT(account_service/account_8858, evidence=future); 4:VERIFY_RECORD_PRESENT(security_service/audit_record_7068, evidence=future); 5:VERIFY_RECORD_REDACTED(identity_service/tombstone_9178, evidence=future).
Predicted but unmatched: 3:VERIFY_RECORD_PRESENT(security_service/audit_record_7068, evidence=future); 4:VERIFY_RECORD_REDACTED(identity_service/tombstone_9178, evidence=future).


Full missing/extra step details are reproducibly written to evaluation_artifacts/sample_metrics.json. Raw traces are outside code.zip; required metrics and limitations are contained directly in this Markdown report.

## Independent artifact review

Automated checks passed: True. Dataset files compared to committed Git blob hashes: 103. Empty deletion predictions: 0. Inference leakage scan matches: 0.

Independent semantic quality gate passed: False. Structural checks passing is not semantic acceptance.
