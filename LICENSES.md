# Upstream data and metadata attribution

The corpus aggregates projections from four sources. Copyright and any
licensor notices remain with the original publishers. The repository MIT
license applies to the original code. It does not relicense the sampled
data, publisher schemas, or publisher action maps.

| Publisher and source | Fixed revision | Original terms |
|---|---|---|
| [IPEC-COMMUNITY, FastUMI_100k_lerobot](https://huggingface.co/datasets/IPEC-COMMUNITY/FastUMI_100k_lerobot/blob/4cf7cca8fdc15d6f71ee0055553ce8a5e78aa9a0/README.md) | 4cf7cca8fdc15d6f71ee0055553ce8a5e78aa9a0 | [Apache-2.0](licenses/Apache-2.0.txt) |
| [Allen Institute for AI, MolmoAct2-BimanualYAM-Dataset](https://huggingface.co/datasets/allenai/MolmoAct2-BimanualYAM-Dataset/blob/e9f21ae15074330839f2ac25ed4b49d76dfa1f9c/README.md) | e9f21ae15074330839f2ac25ed4b49d76dfa1f9c | [Apache-2.0](licenses/Apache-2.0.txt) |
| [NVIDIA, PhysicalAI-Robotics-GR00T-X-Embodiment-Sim](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim/blob/ea7ac0b68f87da62f1e726771bba0fe74300802f/README.md) | ea7ac0b68f87da62f1e726771bba0fe74300802f | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| [oumeanin, lekiwi-study-sort-cubes](https://huggingface.co/datasets/oumeanin/lekiwi-study-sort-cubes/blob/3846537301e907917478d4afb1c54fd28eac4fed/README.md) | 3846537301e907917478d4afb1c54fd28eac4fed | [Apache-2.0](licenses/Apache-2.0.txt) |

**Changes to the upstream files.** We select and project tabular rows from
the fixed paths in the source manifest. We retain commands, timestamps and
source indices, add join keys, and encode the commands as variable-length
float64 lists without rescaling them. We omit image, video, observation,
free-text, simulator-state and reward columns. The core subsamples the
reference. The action-slot table derives annotations from publisher schemas
and modality maps. Any separate analysis annotations are provided with
their evidence scope. This compilation does not imply publisher endorsement.

Credit the applicable original source on redistribution. The manifest
identifies each row's upstream attribution via its file_id. The selected
source cards provide original version and citation details. Companion
papers include [FastUMI-100K](https://arxiv.org/abs/2510.08022),
[MolmoAct2](https://arxiv.org/abs/2605.02881v2), and
[GR00T N1](https://arxiv.org/abs/2503.14734).
