"""Build and filter the OpenRobot4Good configuration catalog using Python 3.10+."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
GRIPPERS = {"gripper", "parallel_gripper", "two_finger_gripper"}

def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def index(rows, key):
    mapped = {row[key]: row for row in rows}
    if len(mapped) != len(rows) or "" in mapped:
        raise ValueError(f"Duplicate or empty {key}")
    return mapped

def write_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def size_class(body, height, bands):
    if body != "humanoid":
        return "not_applicable"
    if height is None:
        return "other_or_unassigned"
    for label in ("half_size", "full_size"):
        low, high = bands[label + "_inclusive"]
        if low <= height <= high:
            return label
    return "other_or_unassigned"

def load_catalog():
    releases = index(read_rows(DATA / "releases.csv"), "release_id")
    sources = index(read_rows(DATA / "sources.csv"), "source_id")
    sizes = index(read_rows(DATA / "platform_sizes.csv"), "platform")
    configs = index(read_rows(DATA / "configurations.csv"), "configuration_id")
    probes = index(read_json(DATA / "probe_receipts.json"), "configuration_id")
    taxonomy = read_json(DATA / "taxonomy.json")
    vocabulary = taxonomy["dimensions"]
    if set(probes) - set(configs):
        raise ValueError("Probe without a corresponding configuration")
    rows = []
    for configuration_id, config in configs.items():
        release = releases[config["release_id"]]
        probe = probes.get(configuration_id)
        access = probe["scope"] if probe else "documentation_only"
        height_row = sizes.get(config["platform"])
        height = float(height_row["reference_height_cm"]) if height_row else None
        size = size_class(config["body"], height, taxonomy["height_coding"])
        identifiers = []
        for field in ("body_sources", "acquisition_sources", "size_sources"):
            identifiers.extend(value for value in config[field].split("|") if value)
        links = [sources[key]["url"] for key in dict.fromkeys(identifiers)]
        if not config["body_sources"] or not config["acquisition_sources"]:
            raise ValueError(f"Missing claim locator for {configuration_id}")
        if height_row and (config["body"] != "humanoid" or height_row["source_id"] != config["size_sources"]):
            raise ValueError(f"Height reference mismatch for {configuration_id}")
        if probe and (probe["revision"] != release["revision"] or not probe["file"].get("sha256")):
            raise ValueError(f"Probe linkage mismatch for {configuration_id}")
        if probe and probe["scope"] == "header_only" and probe.get("footer_rows") is not None:
            raise ValueError("Range receipt cannot carry a complete-file row count")
        row = {
            "configuration_id":configuration_id, "release_id":release["release_id"],
            "family_id":release["family_id"], "release_name":release["release_name"],
            "subset":config["subset"], "domain":config["domain"], "platform":config["platform"],
            "body":config["body"], "locomotion":config["locomotion"], "controlled_scope":config["controlled_scope"],
            "humanoid_size":size, "reference_height_cm":height_row["reference_height_cm"] if height_row else "",
            "size_basis":height_row["size_basis"] if height_row else ("unresolved" if config["body"]=="humanoid" else "not_applicable"),
            "effector":config["effector"], "effector_group":"gripper" if config["effector"] in GRIPPERS else config["effector"],
            "effector_role":config["effector_role"], "acquisition":config["acquisition"],
            "terminal":config["terminal"], "terminal_detail":config["terminal_detail"],
            "observation_channels":config["observation_channels"], "access":access,
            "declared_action_width":probe["action_width"] if probe else None,
            "parquet_footer_rows":probe["footer_rows"] if probe else None,
            "probe_bytes":probe["file"]["bytes"] if probe else None,
            "probe_sha256":probe["file"]["sha256"] if probe else "", "file_url":probe["file"]["url"] if probe else "",
            "data_license":release["data_license"], "license_scope_status":release["license_scope_status"],
            "upstream_revision":release["revision"], "publisher_url":release["publisher_url"],
            "data_terms_url":release["data_terms_url"], "source_ids":"|".join(dict.fromkeys(identifiers)),
            "source_urls":" | ".join(links), "scope_note":config["scope_note"],
            "configuration_checked_date":"2026-11-07",
        }
        for key in ("body","locomotion","humanoid_size","effector","effector_role","acquisition","terminal","access"):
            row[key+"_zh"] = vocabulary[key][row[key]]
        rows.append(row)
    if {row["release_id"] for row in rows} != set(releases):
        raise ValueError("Every indexed release must have a scoped configuration")
    return rows, releases, probes, taxonomy

def grouped_counts(rows, axis, label):
    subset = [row for row in rows if row[axis] == label]
    levels = Counter(row["access"] for row in subset)
    return {
        "axis":axis, "category":label, "configurations":len(subset),
        "release_ids":len({row["release_id"] for row in subset}),
        "family_ids":len({row["family_id"] for row in subset}),
        "complete_files":levels["complete_file_checked"], "header_only":levels["header_only"],
        "documentation_only":levels["documentation_only"],
    }

def build():
    rows, releases, probes, taxonomy = load_catalog()
    RESULTS.mkdir(exist_ok=True)
    write_rows(RESULTS/"catalog.csv",rows)
    counts = []
    for axis in ("body","locomotion","humanoid_size","effector","effector_group","acquisition","terminal"):
        labels = taxonomy["dimensions"].get(axis, {})
        values = sorted(set(labels) | {row[axis] for row in rows})
        counts.extend(grouped_counts(rows, axis, label) for label in values)
    write_rows(RESULTS/"coverage.csv",counts)
    summary={
        "checked":"2026-11-07", "configurations":len(rows), "release_records":len(releases),
        "named_families":len({row["family_id"] for row in rows}),
        "workbook_releases":sum(x["discovery_frame"]=="workbook" for x in releases.values()),
        "supplementary_releases":sum(x["discovery_frame"]=="morphology_extension" for x in releases.values()),
        "access_by_configuration":dict(sorted(Counter(row["access"] for row in rows).items())),
        "receipts_by_edition":dict(sorted(Counter(p["edition"] for p in probes.values()).items())),
    }
    (RESULTS/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return rows, summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    filters=("body","locomotion","humanoid_size","effector","effector_group","effector_role","terminal","access","release_id")
    for field in filters:
        parser.add_argument("--"+field.replace("_","-"),dest=field)
    args=parser.parse_args()
    rows, summary=build()
    selected={field:getattr(args,field) for field in filters if getattr(args,field)}
    if not selected:
        print(json.dumps(summary,indent=2))
        return
    matches=[row for row in rows if all(row[k]==v for k,v in selected.items())]
    print("configuration_id\trelease_id\tplatform\tterminal\taccess")
    for row in matches:
        print("\t".join(row[k] for k in ("configuration_id","release_id","platform","terminal","access")))
    print(f"{len(matches)} configurations; {len({row['release_id'] for row in matches})} releases")

if __name__ == "__main__":
    main()
