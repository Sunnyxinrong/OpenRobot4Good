# Scoped robot data evidence audit

This directory contains the public code and evidence records for the November 10, 2026 revision of *Scope-Constrained Evidence for Robot Data Reuse: A File-Level Audit and Query Prototype*.

The prototype accepts evidence only when dataset_id, revision, subset and context_id match exactly. It rejects missing or wildcard scope fields and keeps conflicts within the same scope from supplying a positive premise. A positive status means requirements_documented_within_scope; human scope assignments, source truth, license interpretation and deployment validity remain outside the executable check.

## Reproduce the recorded results

From the repository root, with Python 3.10 or later and the standard library:

~~~sh
python audit/scripts/reproduce.py
python audit/scripts/test_audit.py
python audit/scripts/query_regressions.py
python audit/scripts/validate_semantics.py
~~~

These commands regenerate the descriptive pilot summary, claim matrix, seven constructed query cases and pinned-map transcription checks. The sixteen unit tests cover incompatible versions, subsets and contexts, incomplete fields, source locators, conflicting records, zero measurements and malformed binary files. The constructed cases are software fixtures, not observed dataset defects or empirical false-positive rates.

The action-map check covers six components and all fourteen action indices of one pinned GR00T Panda Threading configuration. Three constructed interpretations are rejected: swapped arms, relative interpreted as absolute, and axis-angle interpreted as Euler angles. The original action array is unchanged in these examples. The reference and parser are AI-assisted; this is not independent expert or controller validation. Units, frame, scaling, gripper behavior and action-observation timing remain unresolved.

## Evidence scope

The initial screening frame has eleven resource names. The catalog extension covers 22 configurations across thirteen release records, including seven complete files from four pinned releases, one header-only check and fourteen documentation-only entries. The initial three probes and 33 original indicator observations are retained here. The [sampling ledger](data/sampling_ledger.csv) reports the extension's inspection depth and selection basis.

Original retrieval dates are preserved. Scope assignments were migrated on November 10; this is not a new search or an independent recoding pass. The separate catalog retains the November 8 aggregate receipts for 5,085 decoded rows in [../results/action_array_checks.csv](../results/action_array_checks.csv). These correlated rows do not establish semantic or transfer validity.

No independent human double coding, expert sign-off, engineer utility experiment, physical transfer, worker study or deployment energy measurement has been completed. The [coding manual](docs/coding_manual_v0.2.md), [second-coder sheet](docs/second_coder_template.csv) and [prospective utility protocol](docs/utility_study_protocol.md) prepare future work. Blank templates are not completed validation or a preregistration.

## Optional verification of original files

~~~sh
python audit/scripts/reproduce.py --verify-remote
python audit/scripts/reproduce.py --local-probes /path/to/original_downloads
~~~

The online option re-downloads the three original pinned pilot files, cards and info records, plus the companion GR00T map; it verifies SHA-256 values and Parquet footers. Temporary downloads are discarded and missing or changed artifacts fail explicitly. It does not repeat the original web search or the seven-file action decoding pass. Local files use fastumi, molmoact2 and grootsim names with .parquet, _readme.md and _info.json suffixes, plus grootsim_modality.json.

## Materials

| Path | Purpose |
|---|---|
| [data/evidence.json](data/evidence.json) and [data/query_scopes.json](data/query_scopes.json) | Source-linked observations and exact query scopes |
| [data/file_probes.json](data/file_probes.json) and [data/structures.json](data/structures.json) | Original hash and footer receipts |
| [data/sampling_ledger.csv](data/sampling_ledger.csv) | Selected configurations, inspection depth, dates and limits |
| [data/indicators.csv](data/indicators.csv) | Indicator definitions and evidence requirements |
| [results/claim_matrix.csv](results/claim_matrix.csv) | Scope, missing/conflicting premises and supporting links |
| [results/query_regressions.json](results/query_regressions.json) | Seven constructed cases, input records and before/after outcomes |
| [results/semantic_validation.json](results/semantic_validation.json) | Map hash, component coverage, mutations and unresolved checks |
| [docs/](docs/) | Coding rules and unexecuted validation protocols and templates |

The [project license](../LICENSE) applies to project-authored code and documentation. The unchanged publisher metadata map retains its [upstream attribution and terms](data/pinned/README.md).
