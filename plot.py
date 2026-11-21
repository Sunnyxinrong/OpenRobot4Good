"""Create publication-size vector figures from the evaluation CSV files."""

import argparse
import csv
import json
import math
from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


INFRA = HexColor("#D5DFE8")
INK = HexColor("#182938")
QUIET = HexColor("#516271")
TEAL = HexColor("#007B80")
BLUE = HexColor("#3158A5")
AMBER = HexColor("#A95011")
PLUM = HexColor("#825B91")
GREEN = HexColor("#136445")
WIDTH, HEIGHT = 267, 209


def register_fonts():
    fonts = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("ChartSans", str(fonts / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("ChartBold", str(fonts / "VeraBd.ttf")))


def label(c, x, y, value, size=8, color=INK, align="left", bold=False):
    c.setFont("ChartBold" if bold else "ChartSans", size)
    c.setFillColor(color)
    method = {"center": c.drawCentredString, "right": c.drawRightString}.get(align, c.drawString)
    method(x, y, value)


def line(c, xy, color, width=0.8, dash=()):
    c.setStrokeColor(color)
    c.setDash(dash)
    c.setLineWidth(width)
    path = c.beginPath()
    path.moveTo(*xy[0])
    for point in xy[1:]:
        path.lineTo(*point)
    c.drawPath(path)
    c.setDash(())


def point(c, x, y, color, shape="circle", size=2.5, open_center=False):
    c.setStrokeColor(color)
    c.setFillColor(white if open_center else color)
    c.setLineWidth(1)
    if shape == "square":
        c.rect(x-size, y-size, 2*size, 2*size, fill=1)
    elif shape in ("diamond", "triangle"):
        angles = (90, 180, 270, 0) if shape == "diamond" else (90, 210, 330)
        poly = c.beginPath()
        for index, angle in enumerate(angles):
            pos = (x + size * math.cos(math.radians(angle)), y + size * math.sin(math.radians(angle)))
            (poly.moveTo if index == 0 else poly.lineTo)(*pos)
        poly.close()
        c.drawPath(poly, fill=1)
    else:
        c.circle(x, y, size, fill=1)


def canvas(path):
    c = Canvas(str(path), pagesize=(WIDTH, HEIGHT), invariant=1, initialFontName="ChartSans")
    c.setAuthor("")
    return c


def frontier(path, plans, summary):
    c = canvas(path)
    label(c, 3, 196, "Sampling cost and change-event retention", 9.2, bold=True)
    label(c, 3, 184, "Macro-average over seven configurations", 7.5, QUIET)
    x0, x1, y0, y1 = 35, 258, 47, 171

    def x(value):
        a, b = math.log10(50_000), math.log10(3_200_000)
        return x0 + (math.log10(value)-a) / (b-a) * (x1-x0)

    def y(value):
        return y0 + value * (y1-y0)

    for tick in (0., .25, .50, .75, 1.):
        line(c, [(x0, y(tick)), (x1, y(tick))], INFRA, 0.65)
        label(c, x0-6, y(tick)-2.5, f"{tick:.0%}", 7.1, QUIET, "right")
    for tick, name in ((60_000, "0.06"), (100_000, "0.1"), (200_000, "0.2"),
                       (500_000, "0.5"), (1_000_000, "1"), (2_500_000, "2.5")):
        line(c, [(x(tick), y0), (x(tick), y1)], INFRA, 0.55)
        label(c, x(tick), y0-10, name, 7.0, QUIET, "center")
    line(c, [(x0, y1), (x0, y0), (x1, y0)], QUIET, 0.65)
    line(c, [(x0, y(.95)), (x1, y(.95))], QUIET, 0.65, (2, 2))
    label(c, 38, y(.95)-9, "95% target", 6.7, QUIET)

    palette = {
        "prefix": ("Prefix", BLUE, "circle"),
        "center": ("Center", AMBER, "square"),
        "two_windows": ("Two windows", TEAL, "diamond"),
        "stride": ("Stride", PLUM, "triangle"),
        "full": ("Full reference", QUIET, "square"),
    }
    vis = []
    # Large budgets can reproduce the full file byte-for-byte. Draw those ties once.
    for row in plans:
        b, score = int(row["bytes"]), float(row["macro_q90"])
        if b == summary["footprint"] and row["policy"] != "full":
            continue
        vis.append((row, b, score))
    nondominated = [(b, s) for row, b, s in vis if row["pareto"] == "True"]
    nondominated = sorted(set(nondominated))
    front = [(x(nondominated[0][0]), y(nondominated[0][1]))]
    for (b, prev), (right, score) in zip(nondominated, nondominated[1:]):
        front += [(x(right), y(prev)), (x(right), y(score))]
    front.append((x1, front[-1][1]))
    line(c, front, GREEN, 1.1)
    for row, footprint, score in vis:
        _, color, shape = palette[row["policy"]]
        point(c, x(footprint), y(score), color, shape, 2.5, True)
    selected = summary["selected"]
    px, py = x(selected["bytes"]), y(selected["macro_q90"])
    point(c, px, py, GREEN, "diamond", 4.1)
    line(c, [(px, py-6.2), (px, y(.78)), (px-10, y(.78)-6)], GREEN, 0.65)
    label(c, px-12, y(.78)-8, "Core", 7.6, GREEN, "right", bold=True)
    label(c, px-12, y(.78)-18, f"{selected['macro_q90']:.1%} / {selected['bytes']/1e6:.2f} MB",
          6.8, GREEN, "right")
    label(c, (x0+x1)/2, 26, "Compressed frame table (MB, log scale)", 7.8, align="center")
    start = (8, 49, 94, 167, 207)
    for xx, (name, color, shape) in zip(start, palette.values()):
        point(c, xx, 11, color, shape, 2.1, True)
        label(c, xx+5, 8.7, name, 6.8, QUIET)
    c.save()


def radar(path, matrix):
    c = canvas(path)
    label(c, 3, 196, "Action evidence profiles", 9.2, bold=True)
    label(c, 3, 184, "Four configurations, six percentages", 7.5, QUIET)
    cx, cy, radius = 133.5, 100, 55.5
    axis = [("On-clock", "time pairs"), ("Changed", "action pairs"), ("Active", "action slots"),
            ("Named", "action slots"), ("Grouped", "action slots"), ("Absolute flag", "recorded")]

    def dot(index, value):
        angle = math.radians(90-index*60)
        return (cx + radius * value * math.cos(angle), cy + radius * value * math.sin(angle))

    for rung in (.25, .50, .75, 1.0):
        poly = [dot(index, rung) for index in range(6)]
        line(c, poly + [poly[0]], INFRA, 0.7)
    for index in range(6):
        line(c, [(cx, cy), dot(index, 1)], INFRA, 0.55)

    anchored = [(133.5, 169, "center"), (187, 133, "left"), (187, 77, "left"),
                (133.5, 34, "center"), (80, 77, "right"), (80, 133, "right")]
    for (left, right), (x, y, align) in zip(axis, anchored):
        label(c, x, y, left, 7.6, INK, align)
        label(c, x, y-9, right, 7.2, QUIET, align)
    for rung in (.25, .50, .75, 1.0):
        x, y = dot(0, rung)
        label(c, x+1.8, y-4.9, f"{rung:.0%}", 5.9, QUIET)

    selected = [
        ("fastumi.dual", "FastUMI", BLUE, "circle", ()),
        ("grootsim.threading", "Panda Threading", TEAL, "diamond", (4, 1.8)),
        ("grootsim.gr1", "GR-1 CanSort", PLUM, "triangle", (1.3, 1.8)),
        ("lekiwi.cubes", "LeKiwi", AMBER, "square", (3, 2, 1, 2)),
    ]
    rows = {row["configuration_id"]: row for row in matrix}
    for index, (key, name, color, shape, dash) in enumerate(selected):
        row = rows[key]
        values = [int(row[a])/int(row[b]) for a, b in (
                  ("clock_10_pairs", "time_pairs"), ("changed_pairs", "action_pairs"),
                  ("active_slots", "width"), ("named_slots", "width"),
                  ("grouped_slots", "width"), ("absolute_flag_slots", "width"))]
        xy = [dot(axis, value) for axis, value in enumerate(values)]
        line(c, xy+[xy[0]], color, 1.26, dash)
        for px, py in xy:
            point(c, px, py, color, shape, 1.9, True)
        x = (17, 129, 17, 129)[index]
        y = (16, 16, 6, 6)[index]
        line(c, [(x, y), (x+13, y)], color, 1.1, dash)
        point(c, x+6.5, y, color, shape, 1.9, True)
        label(c, x+18, y-2.5, name, 7.1, INK)
    c.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.results / "matrix.csv").open(encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))
    with (args.results / "sampling_plans.csv").open(encoding="utf-8") as handle:
        plans = list(csv.DictReader(handle))
    summary = json.loads((args.results / "summary.json").read_text(encoding="utf-8"))
    register_fonts()
    frontier(args.output / "pareto.pdf", plans, summary)
    radar(args.output / "radar.pdf", matrix)


if __name__ == "__main__":
    main()
