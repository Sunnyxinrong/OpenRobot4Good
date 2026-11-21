# Robot action corpus and evaluation

A small, source-pinned corpus of numerical robot commands for data-integrity,
temporal sampling, and action-schema experiments. It draws on FastUMI,
MolmoAct2-BimanualYAM, NVIDIA GR00T X-Embodiment Sim, and LeKiwi Sort Cubes.
The reference has 64,076 rows from 35 files across seven configurations and
56 distinct configuration/episode keys. The 14,068-row core uses two windows
per file-local episode segment. Native coordinates are preserved.

## Reproduce

Use Python 3.12 with the versions in requirements.txt. From this directory:

    python -m pip install -r requirements.txt
    python run.py --out build
    python plot.py build/results build/figures

The first invocation retrieves the exact upstream Parquet files in
inputs/files.csv. It checks every byte length and SHA-256 before decoding.
For a local copy, name each original file <file_id>.parquet and pass
--upstream-dir PATH. The first run is approximately 14 MB of upstream
Parquet downloads. An HTTPS mirror can be supplied with --source-base;
SHA-256 checks apply to every download. Videos and image data are outside
this corpus.

## Inputs and outputs

- inputs/files.csv maps each local file ID to one source revision, path,
  license, size, row count and SHA-256. For each configuration, it fixes the
  first five numbered files in chunk 000. The sample is purposive.
- inputs/configs.json and inputs/metadata contain the pinned schemas and
  manual evidence annotations, with upstream locators and metadata hashes.
- data/core.parquet and data/extension.parquet partition the reference.
  Combine both and sort by file_id then source_row to recover file order.
- metadata/source_files.csv joins each frame to source and projection digests.
  metadata/action_slots.csv describes original index names, group bounds, and
  publisher absolute/relative metadata when explicitly present.
- results/matrix.csv contains counts before division, including time-band
  and action-quality denominators. results/scope_pairs.csv lists all
  configuration pairs. The sampling table, per-configuration retention file
  and summary provide the basis for both figures.

## Evaluation definitions

An action row is structurally valid if its width matches the pinned schema
and every element is finite. Compare consecutive source rows within the
same file and episode only when native frame indices, or native row indices
where frame indices are absent, differ by one. An on-clock interval is
positive and within ±10% of the nominal sampling period. The matrix also
includes ±5% and ±20% cutoffs. Logged spacing does not measure sensor or
controller synchronization. Named slots exclude generic motor_N names.
Grouped slots come from the publisher's modality map when it refers to the
retained action vector. The absolute flag count measures documentation of
both true and false values.

For each configuration/slot, the event vocabulary records signs of nonzero
adjacent differences whose absolute value is at least that slot's empirical
90th percentile among nonzero changes (inverted CDF). A sample retains an
event if it retains both adjacent source rows in at least one occurrence.
Scores are the unweighted mean of the per-configuration event fractions.
The pipeline also repeats the evaluation with 75th and 95th-percentile
event thresholds. This measures retained evidence of change rather than
policy accuracy, dynamic feasibility, or safety.

The four position-only plans keep up to k rows in each file-local episode
segment. Prefix takes the first k, center takes a middle block, two windows
center one block in each half, and stride uses an evenly spaced index grid.
All plans use the same budgets and Zstandard level-3 frame serialization.
The reported footprint excludes metadata and license documents. The core
is the smallest file among evaluated plans with at least 95% macro-average
retention. Neither the target nor the core size is a deployment standard.
The evaluation is descriptive on the pinned reference sample.

Worker-welfare and environmental entries are coded within the inspected
source scope. A false flag means the required evidence was not located.
It does not assign a measured zero to a worker or environmental outcome.
Use this corpus for data and schema research. A transfer to a robot still
requires a verified adapter, units, frames and a controller evaluation.

## Attribution and licensing

The original reproduction code is available under the MIT license. Sampled data
and publisher metadata retain the licenses of their respective sources.
See LICENSES.md for the data attributions and changes. All rows can be
joined to their license in metadata/source_files.csv after building.
