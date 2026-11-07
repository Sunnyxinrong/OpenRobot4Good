---
license: mit
pretty_name: OpenRobot4Good robot configuration catalog
language:
- en
- zh
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

# OpenRobot4Good

This metadata catalog describes 22 acquisition configurations in 13 release records. It covers the eleven releases in the initial screening frame and two targeted additions. A release can have several configurations. Release IDs and family IDs are available for rollups.

## Use

The configurations view exposes the robot platform, locomotion, humanoid size, effector, acquisition method and observed input terminal. Sources are linked per configuration. The releases view provides the original publisher, version and data terms. The sources view provides the locator used to code each observation.

LeKiwi records a mobile base, arm and gripper. The D’Kitty record describes a simulated quadruped standing task. Separate GR00T rows document a Panda with parallel grippers, a Panda with dexterous hands, the GR-1 CanSort task and a G1 loco-manipulation task. FastUMI records the gripper's role as a handheld acquisition tool.

## Interpretation

The catalog assigns height-based search labels using 110–150 cm for half-size and 160–180 cm for full-size, inclusive. The corresponding heights refer to documented physical reference platforms. Controlled joints and task scope have separate fields.

Seven configurations each have one fully retrieved Parquet file. One quadruped configuration has a 512-byte HDF5 header check. Fourteen configurations are documented from release materials. The actual terminal for a given MolmoAct2 shard remains unresolved even though the collection software supports multiple devices.

## Provenance and access

The catalog follows the MIT license already attached to the OpenRobot4Good project. The data tables contain descriptive metadata and source links. Researchers obtain robot trajectories directly from their original publishers under the terms in each release record. The upstream data_license column describes those original artifacts. The snapshot date is November 7, 2026. Source and verification scripts are available in the project repository. [OpenRobot4Good on GitHub](https://github.com/Sunnyxinrong/OpenRobot4Good)
