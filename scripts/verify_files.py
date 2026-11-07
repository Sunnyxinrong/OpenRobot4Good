"""Recheck pinned public access receipts using temporary local files."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

from catalog import DATA, load_catalog
from parquet_footer import inspect

def verified_bytes(record, range_only=False):
    headers = {"User-Agent":"OpenRobot4Good-receipt-check/0.2"}
    expected_size = record["bytes"]
    if range_only:
        headers["Range"] = f"bytes=0-{expected_size-1}"
    with urlopen(Request(record["url"],headers=headers),timeout=45) as response:
        if range_only and response.status != 206:
            raise ValueError(f"Expected HTTP 206 for range receipt: {record['url']}")
        content = response.read(expected_size+1)
    if len(content) != expected_size or hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise ValueError(f"Receipt mismatch: {record['url']}")
    return content

def verify(probe, folder):
    verified_bytes(probe["data_terms"])
    for key in ("metadata","modality"):
        if key in probe:
            verified_bytes(probe[key])
    header_only = probe["scope"] == "header_only"
    payload=verified_bytes(probe["file"], header_only)
    if probe["format"] == "parquet":
        path=folder/(probe["configuration_id"]+".parquet")
        path.write_bytes(payload)
        if inspect(path)["rows"] != probe["footer_rows"]:
            raise ValueError("Parquet footer row count changed")
    elif not payload.startswith(b"\x89HDF\r\n\x1a\n"):
        raise ValueError("Expected HDF5 signature")
    return {"configuration_id":probe["configuration_id"], "scope":probe["scope"], "verified":True}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration",help="Check a single configuration ID")
    args=parser.parse_args()
    load_catalog()
    probes=json.loads((DATA/"probe_receipts.json").read_text(encoding="utf-8"))
    if args.configuration:
        probes=[p for p in probes if p["configuration_id"]==args.configuration]
        if not probes:
            parser.error("No access receipt for that configuration")
    with tempfile.TemporaryDirectory(prefix="openrobot4good-") as temporary:
        for probe in probes:
            print(json.dumps(verify(probe,Path(temporary))))

if __name__ == "__main__":
    main()
