---
license: mit
pretty_name: OpenRobot4Good robot configuration catalog
language:
- en
tags:
- robotics
- metadata
- robot-learning
- data-governance
configs:
- config_name: configurations
  default: true
  data_files:
  - split: catalog
    path: data/configurations.csv
- config_name: releases
  data_files:
  - split: catalog
    path: data/releases.csv
- config_name: sources
  data_files:
  - split: catalog
    path: data/sources.csv
---

> November 10, 2026 revision: the public GitHub artifact includes a scoped audit and query prototype. The legacy humanoid height bands are unvalidated browsing labels with no demonstrated value for adaptation decisions. Finite, correctly sized arrays do not establish units, frames, timing or successful adaptation. The 5,085 rows are correlated observations in seven files from four pinned releases. This file is a Hub export template; it does not establish a separate Hub publication.

# OpenRobot4Good

This metadata catalog describes 22 acquisition configurations in 13 release records. It covers the eleven releases in the initial screening frame and two targeted additions. A release can have several configurations. Release IDs and family IDs are available for rollups.

## Use

The configurations view exposes the robot platform, locomotion, humanoid size, effector, acquisition method and observed input terminal. Sources are linked per configuration. The releases view provides the original publisher, version and data terms. The sources view provides the locator used to code each observation.

LeKiwi records a mobile base, arm and gripper. The D’Kitty record describes a simulated quadruped standing task. Separate GR00T rows document a Panda with parallel grippers, a Panda with dexterous hands, the GR-1 CanSort task and a G1 loco-manipulation task. FastUMI records the gripper's role as a handheld acquisition tool.

## Interpretation

The catalog assigns height-based search labels using 110–150 cm for half-size and 160–180 cm for full-size, inclusive. The corresponding heights refer to documented physical reference platforms. Controlled joints and task scope have separate fields.

Seven configurations each have one fully retrieved Parquet file. One quadruped configuration has a 512-byte HDF5 header check. Fourteen configurations are documented from release materials. The actual terminal for a given MolmoAct2 shard remains unresolved even though the collection software supports multiple devices.

## Provenance and access

On November 8, 2026, the seven complete files from four releases yielded 5,085 decoded action rows. The observed widths matched the published widths in every row. There were no null vectors, null elements or non-finite action values in these samples. The real RoboSet release has a blank `data_license` field and MIT is retained in `candidate_license` pending scope resolution.

The catalog follows the MIT license already attached to the OpenRobot4Good project. The data tables contain descriptive metadata and source links. Researchers obtain robot trajectories directly from their original publishers under the terms in each release record. The upstream data_license column describes those original artifacts. Configuration observations date to November 7, action-array receipts to November 8, and the query and documentation revision to November 10, 2026. Readable catalog labels are in English. Source and verification scripts are available in the project repository. [OpenRobot4Good on GitHub](https://github.com/Sunnyxinrong/OpenRobot4Good)
