# Scoped evidence coding manual v0.2

Frozen for the November 10, 2026 revision. Changes after coding starts require a new version and a documented recoding decision. This manual specifies prospective validation; it does not retroactively establish the quality of the original audit.

## Unit and packet

One judgment is one indicator at one `(dataset_id, revision, subset, context_id)` scope. The original 33 judgments concern three selected release-documentation scopes. `query_scopes.json` fixes these. Revisions must be immutable repository identifiers where available; mutable pages require a retrieval timestamp and content hash. A date alone is not a version.

The packet includes pinned cards, info metadata and file receipts; GR00T also includes its companion modality map. `file_probes.json` records original hashes and URLs. `structures.json` records initial footer observations; `results/action_array_checks.csv` in the catalog records the later action-column check. These are different passes. File receipts do not establish video, state-channel or full-loader validity.

## States and decision rules

| State | Rule | Example / exclusion |
|---|---|---|
| documented | A source explicitly establishes the narrowly named indicator in this scope; record its value and locator. | `shape: [14]` establishes declared width, not units or transfer. |
| partial | Some required components are explicit, others unresolved. | Ordered motor names without representation or units; a combined contract remains partial. |
| not_located | No qualifying evidence was located within a completed, recorded artifact search. Value remains null. | No meter-linked physical-energy record in the listed card/info/schema. Do not infer publisher-wide absence. |
| conflicting | Two applicable sources disagree and no source-grounded resolution has been established. | Different data terms for the same exact scope; retain both locators. |
| not_applicable | A reason grounded in the indicator definition rules it out. | Non-humanoid height band, if retained as a legacy catalog field. Simulation alone does not make all governance indicators inapplicable. |
| not_assessed | Search or interpretation was not completed, or required context is absent. | No target-controller trial; unknown CARE rightsholder context. |

Keep unknown values null. Do not turn absence into zero. A measured zero is valid evidence of a measurement; it does not make a zero-denominator ratio defined. Do not upgrade a combined field from partial because one component is documented.

## Scope and applicability

All four scope fields must match for executable queries. Root terms may be transcribed into a selected subset only when their applicability is explicitly reviewed and its rationale recorded. Do not automatically inherit a parent license, use a mirror tag to override original data terms, or pool different revisions. The current original-pilot assignments are an explicitly dated migration, not a fresh legal or human review.

`context_id=release_documentation` is a documentation boundary, not a deployment. For a deployment, specify the target platform, run/study identifier, interval and task distribution in an associated context record. Evidence from multiple studies must not be relabeled with a common context merely to satisfy a query. The exact-match code checks identity assertions; a human must validate that the assertions describe compatible evidence. The prototype does not validate study design, license interpretation, causal identification or the truth of a publisher statement.

## Indicator groups

* Access: data-specific license, exact revision and selected retrieved file. Permission screening is separate from broad legal clearance.
* Semantics: component order, representation, units, frame, temporal convention, gripper convention, normalization and calibration. Source-declared interpretation is distinct from an independently validated target mapping.
* Transfer: complete semantic mapping, implemented adapter, target evaluation. Declared action meaning does not satisfy this combined claim.
* Welfare: stakeholder, exposure link, worker outcome and comparison in the same reviewed study context.
* Energy: meter boundary, power interval, success rule, attempt accounting and successful-output count in the same reviewed measurement context.
* Carbon: measured energy, time/location and electricity factor matched to that energy.

`worker_outcome_chain` and `physical_energy_chain` are retained legacy composite observations; the query does not automatically decompose them into positive atomic premises. Explicit atomic records are required. The original legacy absence codes remain descriptions of that bounded review, not assessments of publisher obligations.

## Prospective search protocol

For each indicator inspect the frozen card, matching info and configuration/modality files, explicit linked documentation and the recorded file/schema receipt. Search indicator names and synonyms: action/absolute/delta/velocity, units/frame/coordinate, license/data terms/restrictions, stakeholder/exposure/comparison, meter/power/energy/success/attempt. Record each inspected artifact, locator or query, elapsed time, result and access failure in `search_log_template.csv`.

Set the search budget before a new round (suggested feasibility starting point: 20 active minutes per release packet, then revise and freeze before confirmatory coding). A budget exhaustion or unavailable necessary artifact is `not_assessed` or `partial` as appropriate, with a reason; do not silently label it absence. Historical search durations were not recorded and must remain unknown. A completed bounded search can support `not_located` only within its explicit boundary.

## Independent validation procedure — not yet executed

1. A human coordinator freezes the manual, source packet, indicators, query scopes and search budget.
2. A second human codes the packet without seeing the first labels. `second_coder_template.csv` omits first-coder labels and values; the coordinator must also withhold `evidence.json` and state-bearing summaries until the independent pass is complete. Source locators identify what to inspect and are not independent evidence of a code.
3. Preserve both initial labels and values before discussion. Record every discrepancy in `disagreement_register.csv`, including source locators, reason, resolution and adjudicator.
4. An appropriately qualified expert checks the key data-terms applicability and all action-map slices, units, frames, gripper conventions and timing. Expert review is not a robot-control validation.
5. Report coded-item denominators, category frequencies, raw agreement and an appropriate chance-corrected statistic with its limits. With few categories/items, inspect disagreements directly. Do not invent a reliability number from blank sheets or automated tests.

Current status: zero independent human coders; no expert sign-off; no inter-rater reliability result.
