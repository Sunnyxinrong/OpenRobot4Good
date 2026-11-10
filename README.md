# OpenRobot4Good

OpenRobot4Good provides a source-linked robot data catalog and a scoped evidence query prototype. The November 10, 2026 revision supports the working paper *Scope-Constrained Evidence for Robot Data Reuse: A File-Level Audit and Query Prototype*.

[Configuration catalog](results/catalog.csv) | [Coverage](results/coverage.csv) | [Scoped audit](audit/README.md) | [Claim matrix](audit/results/claim_matrix.csv) | [Coding manual](audit/docs/coding_manual_v0.2.md)

## November 10 revision

The public artifact now includes exact matching on dataset, revision, subset and use context; the original 33 evidence observations with explicit scope assignments; a configuration sampling ledger; and the scripts and records needed to reproduce the reported software checks.

Sixteen unit tests cover scope boundaries, incomplete and conflicting records, legitimate zero measurements and corrupt files. All seven constructed query cases match their expected outcomes. Three constructed action-map interpretation mutations are rejected against a pinned publisher map. These checks establish software behavior and transcription consistency. They do not measure real engineering error rates, validate physical control or establish a benefit over existing documentation.

The audit is a bounded convenience sample. No independent human double coding, expert sign-off, engineer comparison or physical deployment study has been completed. The prospective coding and utility-study materials are preparation documents, with empty logs.

## Quick start

Use Python 3.10 or later. These commands use only the standard library and run offline from the repository root:

~~~sh
python scripts/catalog.py
python audit/scripts/reproduce.py
python audit/scripts/test_audit.py
python audit/scripts/query_regressions.py
python audit/scripts/validate_semantics.py
~~~

The audit commands regenerate summaries and constructed-case results from the recorded observations. They do not repeat the original web search or decode the seven action files. See the [audit guide](audit/README.md) for optional pinned-file verification.

## Catalog coverage

The catalog has 22 selected configurations across 13 release records and 12 named families. Eleven release records come from the inherited screening frame; two are targeted additions. A release may appear in several configurations.

Seven configurations have one complete Parquet file checked, representing four pinned releases. One quadruped configuration has only a 512-byte HDF5 header check; fourteen configurations have publisher documentation only. The November 8 action-column receipts cover 5,085 correlated rows, with matching declared widths and no null vectors, null elements or non-finite values. These receipts are retained in this revision; array structure does not establish semantic correctness or successful adaptation.

| Category | Example | Recorded scope |
|---|---|---|
| Wheeled platform | LeKiwi sort cubes | Mobile base and arm; declared actions include gripper position, base velocity and yaw rate |
| Quadruped | RoboHive RoboSet Sim D'Kitty | Simulated standing task; only the original file header was checked |
| Humanoid | GR00T Unitree G1 and Fourier GR-1 | Reference platform and selected task control are recorded separately |
| Dexterous hand | GR00T Panda LiftTray, GR-1 CanSort and NJF Allegro | Effector type is separate from the robot body |
| Gripper | GR00T Panda Threading, LeKiwi and FastUMI | Robot end effectors are distinguished from handheld capture tools |

## Filter configurations

Filters can be combined:

~~~sh
python scripts/catalog.py --locomotion wheeled
python scripts/catalog.py --effector-group gripper --effector-role robot
python scripts/catalog.py --terminal spacemouse
python scripts/catalog.py --humanoid-size half_size
~~~

The legacy humanoid bands are inclusive 110-150 cm and 160-180 cm intervals for the physical reference platform. They are unvalidated browsing labels with no demonstrated value for adaptation decisions. Other heights remain unassigned. Height does not describe the joints active in a task. These labels are outside the working paper's scientific contribution.

Acquisition describes how a trajectory was produced; terminal describes the operator's control interface; observation channels describe sensors. Seed teaching, automatic replay and live teleoperation are distinct. The actual operator terminal of the selected MolmoAct2 file remains unresolved.

## Source verification

Catalog configurations were recorded on November 7 and action-array receipts on November 8. The November 10 revision changes query rules, reporting and English documentation; it does not imply a new sampling round.

Optional online checks download publisher records and pinned files, verify hashes and discard temporary data:

~~~sh
python scripts/verify_files.py
python scripts/verify_files.py --configuration grootsim.threading
~~~

Re-decoding all seven action columns additionally requires PyArrow. The recorded action pass used version 19.0.0:

~~~sh
python -m pip install pyarrow==19.0.0
python scripts/check_action_arrays.py
~~~

## Repository guide

| Path | Contents |
|---|---|
| [data/configurations.csv](data/configurations.csv) | Selected subsets, robot bodies, control scopes and evidence identifiers |
| [data/releases.csv](data/releases.csv) | Publisher URLs, versions and data terms |
| [data/sources.csv](data/sources.csv) | Sources and inspection locators |
| [data/taxonomy.json](data/taxonomy.json) | English labels, counting rules and legacy height conventions |
| [data/probe_receipts.json](data/probe_receipts.json) | Hash-bound complete-file or header receipts |
| [results/action_array_checks.csv](results/action_array_checks.csv) | Retained aggregate action checks without action values |
| [audit/](audit/) | Scoped records, query implementation, tests and prospective validation materials |
| [hub/README.md](hub/README.md) | English dataset-card template for a separate Hub export |

The English catalog export uses readable columns ending in _label in place of the former _zh translation columns. Category identifiers, filter values, source records and original observation dates are preserved.

## Licensing and upstream data

Project code and documentation follow the existing [MIT license](LICENSE). Upstream artifacts retain their publisher terms; see the [pinned metadata notice](audit/data/pinned/README.md). Original training trajectories, videos and robot action values are obtained from their publishers rather than redistributed here.

The data_license field records terms traced to the relevant upstream artifact. The real RoboSet subset remains unresolved: data_license is blank and MIT is retained only as candidate_license. Project licensing does not replace upstream data terms or establish legal clearance for a particular use.
