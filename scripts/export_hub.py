"""Export the three catalog views and Hub card into a fresh upload directory."""
import argparse
from pathlib import Path
import shutil

from catalog import ROOT, DATA, RESULTS, build

def export(destination):
    build()
    destination=destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("Choose an empty export folder to keep the upload contents explicit.")
    (destination/"data").mkdir()
    for source, name in [(RESULTS/"catalog.csv","configurations.csv"), (DATA/"releases.csv","releases.csv"), (DATA/"sources.csv","sources.csv")]:
        shutil.copyfile(source,destination/"data"/name)
    shutil.copyfile(ROOT/"hub/README.md",destination/"README.md")
    shutil.copyfile(ROOT/"LICENSE",destination/"LICENSE")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination",type=Path)
    export(parser.parse_args().destination)
