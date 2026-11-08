"""Decode the action column in each complete, checksum-pinned Parquet sample."""
import argparse
import csv
import hashlib
import math
from pathlib import Path

from catalog import RESULTS, load_catalog
from verify_files import verified_bytes


def local_payloads(directories):
    files = {}
    for directory in directories:
        for path in directory.glob("*.parquet"):
            payload = path.read_bytes()
            files[hashlib.sha256(payload).hexdigest()] = payload
    return files


def inspect_actions(probe, payload):
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pq.read_table(pa.BufferReader(payload), columns=["action"])
    actions = table["action"].to_pylist()
    present = [row for row in actions if row is not None]
    widths = [len(row) for row in present]
    expected = probe["action_width"]
    return {
        "configuration_id": probe["configuration_id"],
        "file_sha256": probe["file"]["sha256"],
        "decoded_rows": len(actions),
        "declared_width": expected,
        "minimum_width": min(widths, default=None),
        "maximum_width": max(widths, default=None),
        "null_vectors": len(actions) - len(present),
        "width_mismatches": sum(width != expected for width in widths),
        "null_elements": sum(v is None for row in present for v in row),
        "nonfinite_elements": sum(v is not None and not math.isfinite(v) for row in present for v in row),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", action="append", type=Path, default=[],
                        help="Use complete Parquet samples in this directory, matched by SHA-256. Repeat for more directories.")
    parser.add_argument("--output", type=Path, default=RESULTS / "action_array_checks.csv")
    args = parser.parse_args()
    rows, releases, probes, _ = load_catalog()
    configs = {row["configuration_id"]: row for row in rows}
    local = local_payloads(args.local_dir)
    records = []
    issues = []
    for configuration, probe in probes.items():
        if probe["scope"] != "complete_file_checked" or probe["format"] != "parquet":
            continue
        release = releases[configs[configuration]["release_id"]]
        if release["license_scope_status"] != "data_terms_documented":
            raise ValueError(f"Unresolved data terms for {configuration}")
        file = probe["file"]
        if args.local_dir:
            if file["sha256"] not in local:
                raise ValueError(f"Missing checksum-pinned local file for {configuration}")
            payload = local[file["sha256"]]
        else:
            verified_bytes(probe["data_terms"])
            payload = verified_bytes(file)
        record = inspect_actions(probe, payload)
        if record["decoded_rows"] != probe["footer_rows"] or any(
            record[key] for key in ("null_vectors", "width_mismatches", "null_elements", "nonfinite_elements")
        ):
            issues.append(configuration)
        records.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    print(f"Decoded {sum(row['decoded_rows'] for row in records):,} action rows from {len(records)} complete files.")
    if issues:
        raise SystemExit("Inspect discrepancies in: " + ", ".join(issues))


if __name__ == "__main__":
    main()
