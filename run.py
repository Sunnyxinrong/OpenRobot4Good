"""Build and evaluate a source-pinned robot-action data corpus."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
from urllib.request import urlopen

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent
SCHEMA = pa.schema([
    ("configuration_id", pa.string()),
    ("file_id", pa.string()),
    ("source_row", pa.int32()),
    ("episode_index", pa.int64()),
    ("frame_index", pa.int64()),
    ("source_index", pa.int64()),
    ("timestamp", pa.float64()),
    ("task_index", pa.int64()),
    ("action", pa.list_(pa.float64())),
])
SOURCE_COLUMNS = {
    "episode_index": "episode_index",
    "frame_index": "frame_index",
    "source_index": "index",
    "timestamp": "timestamp",
    "task_index": "task_index",
    "action": "action",
}
ACTION_QUANTILES = (0.75, 0.90, 0.95)
BUDGETS = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096)
POLICIES = ("prefix", "center", "two_windows", "stride")
TARGET = 0.95
MAX_DOWNLOAD = 8 * 1024 * 1024


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def file_digest(path):
    with path.open("rb") as handle:
        return sha256(handle.read()).hexdigest()


def frame_digest(table):
    payload = json.dumps(table.to_pylist(), separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("ascii")).hexdigest()


def fetch_source(url, path):
    with urlopen(url, timeout=60) as response:
        body = response.read(MAX_DOWNLOAD + 1)
    if not 0 < len(body) <= MAX_DOWNLOAD:
        raise ValueError(f"Unexpected download size: {url}")
    temporary = path.with_suffix(".part")
    temporary.write_bytes(body)
    temporary.replace(path)


def project_file(path, receipt):
    if path.stat().st_size != int(receipt["source_bytes"]) or file_digest(path) != receipt["source_sha256"]:
        raise ValueError(f"Source byte or SHA-256 mismatch: {path}")
    source = pq.ParquetFile(path)
    selected = [k for k in SOURCE_COLUMNS.values() if k in source.schema_arrow.names]
    for required in ("action", "episode_index", "timestamp"):
        if required not in selected:
            raise ValueError(f"Missing {required} in {path}")
    table = source.read(columns=selected, use_threads=False)
    n = table.num_rows
    if n != int(receipt["source_rows"]):
        raise ValueError(f"Unexpected row count in {path}")
    columns = {
        "configuration_id": [receipt["configuration_id"]] * n,
        "file_id": [receipt["file_id"]] * n,
        "source_row": range(n),
    }
    for column, native in SOURCE_COLUMNS.items():
        columns[column] = table[native].to_pylist() if native in selected else [None] * n
    return pa.Table.from_pydict(columns, schema=SCHEMA)


def load_frames(manifest, upstream_dir, snapshot_dir, source_base):
    base = urlsplit(source_base)
    if base.scheme != "https" or not base.hostname or base.username or base.query or base.fragment or base.path not in ("", "/"):
        raise ValueError("The source base must be an HTTPS origin without credentials or a path")
    if snapshot_dir is not None:
        parts = [pq.ParquetFile(snapshot_dir / "data" / name).read()
                 for name in ("core.parquet", "extension.parquet")]
        source = pa.concat_tables(parts).cast(SCHEMA)
        present = set(source["file_id"].to_pylist())
        expected = {receipt["file_id"] for receipt in manifest}
        if present != expected:
            raise ValueError("The snapshot file IDs do not match the pinned manifest")
        snapshot_manifest = read_csv(snapshot_dir / "metadata" / "source_files.csv")
        checks = {row["file_id"]: row["projection_sha256"] for row in snapshot_manifest}
        projected = []
        for receipt in manifest:
            file_id = receipt["file_id"]
            table = source.filter(pc.equal(source["file_id"], file_id))
            table = table.sort_by("source_row")
            if table["source_row"].to_pylist() != list(range(int(receipt["source_rows"]))):
                raise ValueError(f"Missing or duplicate row keys in the snapshot: {file_id}")
            if set(table["configuration_id"].to_pylist()) != {receipt["configuration_id"]}:
                raise ValueError(f"Configuration mismatch in snapshot: {file_id}")
            if frame_digest(table) != checks.get(file_id):
                raise ValueError(f"Projected snapshot digest mismatch: {file_id}")
            projected.append(table)
        return projected

    upstream_dir.mkdir(parents=True, exist_ok=True)
    projected = []
    for receipt in manifest:
        path = upstream_dir / (receipt["file_id"] + ".parquet")
        if not path.exists():
            source_path = urlsplit(receipt["source_url"]).path
            fetch_source(source_base.rstrip("/") + source_path, path)
        projected.append(project_file(path, receipt))
    return projected


def action_valid(action, width):
    return action is not None and len(action) == width and all(
        element is not None and math.isfinite(element) for element in action)


def pair_indices(rows):
    """Pairs are consecutive stored rows with verified adjacent native indices."""
    pairs = []
    for index, (left, right) in enumerate(zip(rows, rows[1:])):
        if left["episode_index"] is None or left["episode_index"] != right["episode_index"]:
            continue
        key = "frame_index" if left["frame_index"] is not None and right["frame_index"] is not None else "source_index"
        if left[key] is not None and right[key] is not None and right[key] - left[key] == 1:
            pairs.append(index)
    return np.array(pairs, dtype=np.int64)


def segments(rows):
    """Return file-local contiguous episode segments for frame-budget allocation."""
    boundaries = [0]
    boundaries.extend(i for i in range(1, len(rows))
                      if rows[i]["episode_index"] != rows[i - 1]["episode_index"])
    boundaries.append(len(rows))
    return [(start, end) for start, end in zip(boundaries, boundaries[1:]) if end > start]


def source_names(feature):
    names = feature.get("names") or []
    if isinstance(names, dict):
        names = names.get("motors", [])
    return names


def annotate_slots(config_id, spec):
    for resource in ("info", "modality"):
        if spec[resource] and file_digest(ROOT / spec[resource]) != spec[resource + "_sha256"]:
            raise ValueError(f"Metadata digest mismatch: {config_id}/{resource}")
    info = json.loads((ROOT / spec["info"]).read_text(encoding="utf-8"))
    feature = info["features"]["action"]
    width = int(feature["shape"][0])
    names = source_names(feature)
    slots = [{"configuration_id": config_id, "slot": i,
              "publisher_name": names[i] if i < len(names) else None,
              "group": None, "absolute": None, "rotation_type": None,
              "info_url": spec["info_url"], "modality_url": spec["modality_url"]}
             for i in range(width)]
    if spec["modality"]:
        groups = json.loads((ROOT / spec["modality"]).read_text(encoding="utf-8"))["action"]
        for group, details in groups.items():
            if details.get("original_key", "action") != "action":
                continue
            start, end = details["start"], details["end"]
            if not 0 <= start < end <= width:
                raise ValueError(f"Out-of-range action-map slice: {config_id}/{group}")
            for i in range(start, end):
                if slots[i]["group"] is not None:
                    raise ValueError(f"Overlapping action-map slices: {config_id}/{group}")
                slots[i].update(group=group, absolute=details.get("absolute"),
                                rotation_type=details.get("rotation_type"))
    return width, float(info["fps"]), slots


def has_label(slot):
    name = slot["publisher_name"]
    return name is not None and re.fullmatch(r"motor_\d+", name) is None


def profile_dataset(configs, manifest, projected):
    data = {}
    config_slots = []
    offset = 0
    for receipt, table in zip(manifest, projected):
        key = receipt["configuration_id"]
        if key not in data:
            width, hz, slots = annotate_slots(key, configs[key])
            config_slots.extend(slots)
            data[key] = {"width": width, "hz": hz, "slots": slots, "files": []}
        entry = data[key]
        rows = table.to_pylist()
        pairs = pair_indices(rows)
        valid = np.array([action_valid(row["action"], entry["width"]) for row in rows])
        good_pairs = pairs[valid[pairs] & valid[pairs + 1]]
        values = np.array([row["action"] if ok else [np.nan] * entry["width"]
                           for row, ok in zip(rows, valid)], dtype=float)
        times = np.array([row["timestamp"] if row["timestamp"] is not None else np.nan
                          for row in rows], dtype=float)
        entry["files"].append({
            "receipt": receipt, "episodes": {x["episode_index"] for x in rows if x["episode_index"] is not None},
            "tasks": {x["task_index"] for x in rows if x["task_index"] is not None},
            "segments": segments(rows), "valid_rows": int(valid.sum()),
            "offset": offset, "rows": len(rows), "elapsed": times[pairs + 1] - times[pairs],
            "pairs": good_pairs, "deltas": values[good_pairs + 1] - values[good_pairs],
        })
        offset += len(rows)
    return data, config_slots


def summarize(data, configs):
    rows = []
    for key, entry in data.items():
        files = entry["files"]
        n = sum(f["rows"] for f in files)
        slots = entry["slots"]
        width = entry["width"]
        step = 1 / entry["hz"]
        dt = np.concatenate([f["elapsed"] for f in files])
        deltas = np.concatenate([f["deltas"] for f in files])
        valid_time = dt[np.isfinite(dt) & (dt > 0)]
        evidence = configs[key]["evidence"]
        row = dict(
            configuration_id=key, release_id=configs[key]["release_id"], raw_files=len(files),
            episode_ids=len(set().union(*(f["episodes"] for f in files))),
            segments=sum(len(f["segments"]) for f in files),
            task_ids=len(set().union(*(f["tasks"] for f in files))), rows=n, width=width,
            declared_hz=entry["hz"], median_hz=float(1 / np.median(valid_time)) if valid_time.size else None,
            valid_action_rows=sum(f["valid_rows"] for f in files), time_pairs=len(dt),
            nonpositive_dt=int(np.sum(np.isfinite(dt) & (dt <= 0))),
            missing_dt=int(np.sum(~np.isfinite(dt))),
            action_pairs=len(deltas), changed_pairs=int(np.any(deltas != 0, axis=1).sum()),
            active_slots=int(np.any(deltas != 0, axis=0).sum()),
            named_slots=sum(has_label(s) for s in slots),
            grouped_slots=sum(s["group"] is not None for s in slots),
            absolute_flag_slots=sum(s["absolute"] is not None for s in slots),
            welfare_fields=sum(evidence["welfare"].values()),
            energy_fields=sum(evidence["energy"].values()),
            carbon_fields=sum(evidence["energy"].values()) + sum(evidence["carbon_extra"].values()),
        )
        for band in (5, 10, 20):
            row[f"clock_{band}_pairs"] = int(np.sum(np.isfinite(dt) & (dt > 0)
                                                   & (np.abs(dt / step - 1) <= band / 100)))
        rows.append(row)
    return rows


def reference_events(data):
    """Represent covered (configuration, action slot, sign) events as bit masks."""
    vocab_sizes = {q: {} for q in ACTION_QUANTILES}
    for config, entry in data.items():
        joined = np.concatenate([node["deltas"] for node in entry["files"]])
        for quantile in ACTION_QUANTILES:
            cursor = 0
            for node in entry["files"]:
                node.setdefault("events", {})[quantile] = np.zeros(node["pairs"].size, dtype=object)
            for slot in range(entry["width"]):
                nonzero = np.abs(joined[:, slot][joined[:, slot] != 0])
                if nonzero.size == 0:
                    continue
                cutoff = float(np.quantile(nonzero, quantile, method="inverted_cdf"))
                for sign in (-1, 1):
                    if not np.any(sign * joined[:, slot] >= cutoff):
                        continue
                    for node in entry["files"]:
                        selected = sign * node["deltas"][:, slot] >= cutoff
                        event_masks = node["events"][quantile]
                        event_masks[selected] = event_masks[selected] | (1 << cursor)
                    cursor += 1
            vocab_sizes[quantile][config] = cursor
    return vocab_sizes


def windows(start, end, budget, policy):
    size = end - start
    k = min(size, budget)
    if k == size or policy == "prefix":
        return np.arange(start, start + k)
    if policy == "center":
        first = start + (size - k) // 2
        return np.arange(first, first + k)
    if policy == "stride":
        return np.linspace(start, end - 1, k, dtype=np.int64)
    # Two disjoint windows centered in the first and second halves.
    midpoint = start + size // 2
    return np.concatenate([windows(start, midpoint, k // 2, "center"),
                           windows(midpoint, end, k - k // 2, "center")])


def parquet_bytes(table):
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink, compression="zstd", compression_level=3)
    return sink.getvalue().to_pybytes()


def evaluate_plans(full, data):
    sizes = reference_events(data)
    if any(size == 0 for size in sizes[0.90].values()):
        raise ValueError("Each configuration needs at least one measurable change event")
    plans = []
    for policy, budget in [(p, k) for p in POLICIES for k in BUDGETS] + [("full", full.num_rows)]:
        pieces = []
        covered = {q: defaultdict(int) for q in ACTION_QUANTILES}
        for config, entry in data.items():
            for source in entry["files"]:
                picked = np.concatenate([windows(start, end, budget, policy)
                                        for start, end in source["segments"]])
                pieces.append(picked + source["offset"])
                kept = np.zeros(source["rows"], dtype=bool)
                kept[picked] = True
                adjacent = kept[source["pairs"]] & kept[source["pairs"] + 1]
                for quantile in ACTION_QUANTILES:
                    marks = source["events"][quantile][adjacent]
                    covered[quantile][config] |= np.bitwise_or.reduce(marks, initial=0)
        indices = np.sort(np.concatenate(pieces))
        packed = parquet_bytes(full.take(indices))
        row = dict(policy=policy, budget=budget, bytes=len(packed), rows=len(indices))
        per_config = {}
        for quantile in ACTION_QUANTILES:
            pct = int(100 * quantile)
            values = {config: covered[quantile][config].bit_count() / n
                      for config, n in sizes[quantile].items() if n}
            row[f"macro_q{pct}"] = sum(values.values()) / len(values)
            row[f"worst_q{pct}"] = min(values.values())
            per_config[str(pct)] = values
        plans.append((row, indices, per_config))

    best_score = -1
    for row, _, _ in sorted(plans, key=lambda plan: (plan[0]["bytes"], -plan[0]["macro_q90"])):
        row["pareto"] = row["macro_q90"] > best_score + 1e-12
        best_score = max(best_score, row["macro_q90"])
    selected = min((plan for plan in plans if plan[0]["macro_q90"] >= TARGET),
                   key=lambda plan: (plan[0]["bytes"], -plan[0]["macro_q90"]))
    for row, _, _ in plans:
        row["selected"] = row is selected[0]
    return plans, selected, sizes


def scope_pairs(metrics, configs):
    pairs = []
    for left, right in combinations(metrics, 2):
        a, b = left["configuration_id"], right["configuration_id"]
        width_match = left["width"] == right["width"]
        signature_a = configs[a]["representation"]
        signature_b = configs[b]["representation"]
        pairs.append(dict(left=a, right=b, width_match=width_match,
                          left_publisher_representation=signature_a,
                          right_publisher_representation=signature_b,
                          documented_difference=width_match and bool(signature_a) and bool(signature_b)
                          and signature_a != signature_b))
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "build")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--upstream-dir", type=Path, default=ROOT / "cache")
    inputs.add_argument("--snapshot-dir", type=Path)
    parser.add_argument("--source-base", default="https://huggingface.co",
                        help="HTTPS origin for an optional read-only source mirror")
    args = parser.parse_args()
    configs = json.loads((ROOT / "inputs" / "configs.json").read_text(encoding="utf-8"))
    receipts = read_csv(ROOT / "inputs" / "files.csv")
    if len({r["source_sha256"] for r in receipts}) != len(receipts):
        raise ValueError("Source file receipts must be unique")
    frames = load_frames(receipts, args.upstream_dir, args.snapshot_dir, args.source_base)
    full = pa.concat_tables(frames).combine_chunks()
    data, slots = profile_dataset(configs, receipts, frames)
    metrics = summarize(data, configs)
    plans, selected, vocab_sizes = evaluate_plans(full, data)
    summary, indices, per_config = selected
    pairs = scope_pairs(metrics, configs)
    rest = np.ones(full.num_rows, dtype=bool)
    rest[indices] = False

    dest = args.out
    (dest / "data").mkdir(parents=True, exist_ok=True)
    (dest / "metadata").mkdir(exist_ok=True)
    (dest / "results").mkdir(exist_ok=True)
    shutil.copytree(ROOT / "inputs" / "metadata", dest / "inputs" / "metadata", dirs_exist_ok=True)
    (dest / "data" / "core.parquet").write_bytes(parquet_bytes(full.take(indices)))
    (dest / "data" / "extension.parquet").write_bytes(parquet_bytes(full.filter(rest)))
    published = [dict(r, projection_sha256=frame_digest(table))
                 for r, table in zip(receipts, frames)]
    write_csv(dest / "metadata" / "source_files.csv", published)
    write_csv(dest / "metadata" / "action_slots.csv", slots)
    write_json(dest / "metadata" / "configurations.json", configs)
    write_csv(dest / "results" / "matrix.csv", metrics)
    write_csv(dest / "results" / "sampling_plans.csv", [row for row, _, _ in plans])
    write_csv(dest / "results" / "scope_pairs.csv", pairs)
    write_json(dest / "results" / "retention_by_configuration.json",
               [dict(policy=r["policy"], budget=r["budget"], fraction_by_quantile=c) for r, _, c in plans])
    totals = dict(configurations=len(data), releases=len({r["release_id"] for r in metrics}),
                  files=len(frames), rows=full.num_rows,
                  episode_ids=sum(r["episode_ids"] for r in metrics),
                  segments=sum(r["segments"] for r in metrics),
                  bytes=sum(int(item["source_bytes"]) for item in receipts),
                  releases_to_files=dict(Counter(configs[r["configuration_id"]]["release_id"] for r in receipts)),
                  footprint=plans[-1][0]["bytes"],
                  width_matches=sum(item["width_match"] for item in pairs),
                  documented_differences=sum(item["documented_difference"] for item in pairs),
                  selected=summary, selected_by_quantile=per_config,
                  reference_support={str(q): n for q, n in vocab_sizes.items()},
                  equal_width_profiles=Counter(r["width"] for r in metrics).most_common(1)[0][0])
    write_json(dest / "results" / "summary.json", totals)
    print(json.dumps({k: totals[k] for k in ("files", "rows", "episode_ids", "selected")}, indent=2))


if __name__ == "__main__":
    main()
