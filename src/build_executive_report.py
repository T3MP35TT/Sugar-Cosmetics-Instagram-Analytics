"""Build a self-contained DOCX executive report from the current analysis artifacts."""

from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
import tempfile
import zipfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

PINK = "E84F87"
PLUM = "35232F"
INK = "302630"
MUTED = "6D626B"
PALE = "F7EDF2"
GRID = "E8DDE4"
WHITE = "FFFFFF"
PAGE_WIDTH_IN = 7.1


def tag(name: str) -> str:
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value, default=0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def fmt_int(value) -> str:
    return f"{safe_float(value):,.0f}"


def fmt_pct(value, digits=2) -> str:
    return f"{safe_float(value) * 100:.{digits}f}%"


def weighted_summary(frame: pd.DataFrame) -> dict:
    interactions = frame[["likes", "comments", "shares", "saves"]].sum(axis=1, min_count=4)
    valid = interactions.notna() & frame["reach"].gt(0)
    total_engagements = interactions.sum(min_count=1)
    total_reach = frame.loc[valid, "reach"].sum(min_count=1)
    return {
        "engagements": total_engagements,
        "reach": total_reach,
        "weighted_rate": total_engagements / total_reach if total_reach else np.nan,
        "row_engagements": interactions,
    }


def category_table(frame: pd.DataFrame, dimension: str, engagement: pd.Series) -> pd.DataFrame:
    data = frame.assign(_engagement=engagement)
    grouped = data.groupby(dimension, dropna=False).agg(
        records=(dimension, "size"), reach=("reach", "sum"), engagements=("_engagement", "sum")
    )
    grouped["rate"] = grouped["engagements"] / grouped["reach"].where(grouped["reach"] > 0)
    return grouped.reset_index()


def build_charts(frame: pd.DataFrame, artifacts: dict, tempdir: Path) -> dict[str, Path]:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 12,
        "axes.labelcolor": f"#{INK}", "text.color": f"#{INK}",
        "xtick.color": f"#{MUTED}", "ytick.color": f"#{MUTED}",
        "axes.edgecolor": f"#{GRID}", "figure.facecolor": "white", "axes.facecolor": "white",
    })
    charts = {}
    eng = frame[["likes", "comments", "shares", "saves"]].sum(axis=1, min_count=4)

    # Format and campaign weighted rates with simultaneous date-block intervals.
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), constrained_layout=True)
    inf = artifacts["inference"]["results"]
    for ax, dim, title in zip(axes, ["post_type", "campaign_type"], ["By post format", "By campaign"]):
        rows = sorted(inf[dim], key=lambda x: x["weighted_rate"])
        labels = [str(row[dim]) for row in rows]
        rates = [row["difference_pp"] for row in rows]
        lower = [row["difference_pp"] - row["simultaneous_ci_low_pp"] for row in rows]
        upper = [row["simultaneous_ci_high_pp"] - row["difference_pp"] for row in rows]
        colors = [f"#{PINK}" if row["simultaneous_ci_low_pp"] > 0 or row["simultaneous_ci_high_pp"] < 0 else "#B89EAC" for row in rows]
        y = np.arange(len(rows))
        ax.barh(y, rates, color=colors, height=0.62, zorder=2)
        ax.errorbar(rates, y, xerr=[lower, upper], fmt="none", ecolor=f"#{PLUM}", capsize=3, lw=1, zorder=3)
        ax.set_yticks(y, labels)
        ax.axvline(0, color=f"#{PLUM}", lw=1, ls="--", alpha=0.65)
        ax.set_xlabel("Weighted-rate difference vs all other categories (pp)")
        ax.set_title(title, loc="left", fontweight="bold", color=f"#{PLUM}")
        ax.grid(axis="x", color=f"#{GRID}", lw=0.8, zorder=0)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(min(row["simultaneous_ci_low_pp"] for row in rows) - 0.05, max(row["simultaneous_ci_high_pp"] for row in rows) + 0.05)
    charts["category"] = tempdir / "category_comparison.png"
    fig.savefig(charts["category"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Monthly record volume and weighted rate.
    dated = frame.assign(_eng=eng, _date=pd.to_datetime(frame["post_date"], errors="coerce")).dropna(subset=["_date"])
    monthly = dated.assign(month=dated["_date"].dt.to_period("M")).groupby("month").agg(
        records=("month", "size"), engagements=("_eng", "sum"), reach=("reach", "sum")
    )
    monthly["rate"] = monthly["engagements"] / monthly["reach"].where(monthly["reach"] > 0)
    fig, ax = plt.subplots(figsize=(11.8, 3.7), constrained_layout=True)
    x = np.arange(len(monthly))
    ax.bar(x, monthly["records"], color="#E7CBD8", width=0.7, label="Records")
    ax.set_ylabel("Records in supplied data", color=f"#{MUTED}")
    ax.set_xticks(x, [str(item) for item in monthly.index], rotation=45, ha="right")
    ax.grid(axis="y", color=f"#{GRID}", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    rate_ax = ax.twinx()
    rate_ax.plot(x, monthly["rate"] * 100, color=f"#{PINK}", marker="o", lw=2.4, ms=4, label="Weighted engagement rate")
    rate_ax.set_ylabel("Weighted engagement rate (%)", color=f"#{PINK}")
    rate_ax.spines[["top", "left"]].set_visible(False)
    ax.set_title("Monthly data volume and weighted engagement rate", loc="left", color=f"#{PLUM}", fontweight="bold")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = rate_ax.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, frameon=False, loc="upper left", ncol=2)
    charts["monthly"] = tempdir / "monthly_trend.png"
    fig.savefig(charts["monthly"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Weekday rates.
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_frame = dated.assign(weekday=dated["_date"].dt.day_name(), _eng=eng.loc[dated.index])
    weekday = weekday_frame.groupby("weekday").agg(records=("weekday", "size"), engagements=("_eng", "sum"), reach=("reach", "sum")).reindex(weekday_order)
    weekday["rate"] = weekday["engagements"] / weekday["reach"]
    fig, ax = plt.subplots(figsize=(10.8, 3.4), constrained_layout=True)
    colors = [f"#{PINK}" if val == weekday["rate"].max() else "#B99BAA" for val in weekday["rate"]]
    ax.bar(weekday_order, weekday["rate"] * 100, color=colors, width=0.68)
    ax.set_ylabel("Weighted engagement rate (%)")
    ax.set_title("Weekday patterns in the supplied records", loc="left", color=f"#{PLUM}", fontweight="bold")
    ax.grid(axis="y", color=f"#{GRID}", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(weekday["rate"].min() * 100 - 0.06, weekday["rate"].max() * 100 + 0.06)
    for idx, row in enumerate(weekday.itertuples()):
        ax.text(idx, row.rate * 100 + 0.012, f"{row.rate:.2%}", ha="center", va="bottom", fontsize=8)
    charts["weekday"] = tempdir / "weekday_rates.png"
    fig.savefig(charts["weekday"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Top hashtag usage and weighted engagement rate.
    tag_rows = []
    for idx, row in frame[["hashtags", "reach"]].assign(_eng=eng).iterrows():
        if pd.isna(row["hashtags"]):
            continue
        for hashtag in set(re.findall(r"#\w+", str(row["hashtags"]).lower())):
            tag_rows.append((hashtag, row["reach"], row["_eng"]))
    tag_data = pd.DataFrame(tag_rows, columns=["hashtag", "reach", "engagements"])
    tag_summary = tag_data.groupby("hashtag").agg(records=("hashtag", "size"), reach=("reach", "sum"), engagements=("engagements", "sum"))
    tag_summary["rate"] = tag_summary["engagements"] / tag_summary["reach"].where(tag_summary["reach"] > 0)
    tag_summary = tag_summary.sort_values("records", ascending=False).head(10).sort_values("records")
    fig, ax = plt.subplots(figsize=(10.8, 4.0), constrained_layout=True)
    y = np.arange(len(tag_summary))
    ax.barh(y, tag_summary["records"], color="#E7CBD8", height=0.62)
    ax.set_yticks(y, tag_summary.index)
    ax.set_xlabel("Records containing hashtag (overlap allowed)")
    ax.set_title("Ten most-used hashtags and their weighted rates", loc="left", color=f"#{PLUM}", fontweight="bold")
    ax.grid(axis="x", color=f"#{GRID}", lw=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    rate_ax = ax.twiny()
    rate_ax.plot(tag_summary["rate"] * 100, y, color=f"#{PINK}", marker="o", lw=0, ms=6)
    rate_ax.set_xlabel("Weighted engagement rate (%)", color=f"#{PINK}")
    rate_ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    charts["hashtags"] = tempdir / "hashtag_usage.png"
    fig.savefig(charts["hashtags"], dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Conditional engagement volume calibration by actual decile.
    pred_path = ROOT / "reports" / "conditional_engagement_volume_predictions.csv"
    pred = pd.read_csv(pred_path)
    pred["actual_decile"] = pd.qcut(pred["actual_engagements"], q=10, labels=False, duplicates="drop")
    deciles = pred.groupby("actual_decile", observed=True).agg(actual=("actual_engagements", "mean"), predicted=("predicted_engagements", "mean"))
    fig, ax = plt.subplots(figsize=(7.4, 4.3), constrained_layout=True)
    max_value = max(deciles["actual"].max(), deciles["predicted"].max()) * 1.04
    ax.plot([0, max_value], [0, max_value], "--", color="#A89AA3", lw=1.4, label="Perfect calibration")
    ax.plot(deciles["actual"], deciles["predicted"], color=f"#{PINK}", marker="o", lw=2.5, label="Ridge prediction")
    ax.set_xlim(0, max_value)
    ax.set_ylim(0, max_value)
    ax.set_xlabel("Actual engagements per record (decile mean)")
    ax.set_ylabel("Predicted engagements per record")
    ax.set_title("Exposure-conditional volume model calibration", loc="left", color=f"#{PLUM}", fontweight="bold")
    ax.grid(color=f"#{GRID}", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    charts["calibration"] = tempdir / "conditional_calibration.png"
    fig.savefig(charts["calibration"], dpi=180, bbox_inches="tight")
    plt.close(fig)
    return charts


def add_run(parent, text: str, *, bold=False, italic=False, color=None, size=None):
    run = ET.SubElement(parent, tag("w:r"))
    props = ET.SubElement(run, tag("w:rPr"))
    if bold:
        ET.SubElement(props, tag("w:b"))
    if italic:
        ET.SubElement(props, tag("w:i"))
    if color:
        ET.SubElement(props, tag("w:color"), {tag("w:val"): color})
    if size:
        ET.SubElement(props, tag("w:sz"), {tag("w:val"): str(size)})
        ET.SubElement(props, tag("w:szCs"), {tag("w:val"): str(size)})
    rfonts = ET.SubElement(props, tag("w:rFonts"))
    rfonts.set(tag("w:ascii"), "Aptos")
    rfonts.set(tag("w:hAnsi"), "Aptos")
    text_node = ET.SubElement(run, tag("w:t"))
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_node.text = str(text)
    return run


class ReportDocument:
    def __init__(self):
        self.root = ET.Element(tag("w:document"))
        self.body = ET.SubElement(self.root, tag("w:body"))
        self.relationships = []
        self.media = {}
        self.next_rid = 1

    def paragraph(self, text="", style="Normal", *, bold=False, italic=False, color=None, size=None, align=None, before=None, after=None):
        p = ET.SubElement(self.body, tag("w:p"))
        ppr = ET.SubElement(p, tag("w:pPr"))
        if style:
            ET.SubElement(ppr, tag("w:pStyle"), {tag("w:val"): style})
        if align:
            ET.SubElement(ppr, tag("w:jc"), {tag("w:val"): align})
        if before is not None or after is not None:
            ET.SubElement(ppr, tag("w:spacing"), {tag("w:before"): str(before or 0), tag("w:after"): str(after or 0)})
        if text:
            add_run(p, text, bold=bold, italic=italic, color=color, size=size)
        return p

    def heading(self, text, level=1):
        return self.paragraph(text, f"Heading{level}")

    def bullet(self, text, *, level=0):
        p = self.paragraph(style="Normal")
        ppr = p.find(tag("w:pPr"))
        ET.SubElement(ppr, tag("w:ind"), {tag("w:left"): str(360 + level * 240), tag("w:hanging"): "180"})
        add_run(p, "•  ", bold=True, color=PINK)
        add_run(p, text)
        return p

    def callout(self, text, *, accent=PINK, fill=PALE):
        p = ET.SubElement(self.body, tag("w:p"))
        ppr = ET.SubElement(p, tag("w:pPr"))
        ET.SubElement(ppr, tag("w:spacing"), {tag("w:before"): "120", tag("w:after"): "160"})
        pborder = ET.SubElement(ppr, tag("w:pBdr"))
        ET.SubElement(pborder, tag("w:left"), {tag("w:val"): "single", tag("w:sz"): "22", tag("w:space"): "8", tag("w:color"): accent})
        ET.SubElement(ppr, tag("w:shd"), {tag("w:fill"): fill, tag("w:val"): "clear"})
        add_run(p, text, color=PLUM, size=21)
        return p

    def table(self, headers, rows, widths=None):
        table = ET.SubElement(self.body, tag("w:tbl"))
        props = ET.SubElement(table, tag("w:tblPr"))
        ET.SubElement(props, tag("w:tblW"), {tag("w:w"): "10200", tag("w:type"): "dxa"})
        ET.SubElement(props, tag("w:tblLayout"), {tag("w:type"): "fixed"})
        borders = ET.SubElement(props, tag("w:tblBorders"))
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            ET.SubElement(borders, tag(f"w:{edge}"), {tag("w:val"): "single", tag("w:sz"): "5", tag("w:space"): "0", tag("w:color"): GRID})
        cell_margins = ET.SubElement(props, tag("w:tblCellMar"))
        for edge, val in (("top", 90), ("start", 110), ("bottom", 90), ("end", 110)):
            ET.SubElement(cell_margins, tag(f"w:{edge}"), {tag("w:w"): str(val), tag("w:type"): "dxa"})
        count = len(headers)
        if widths is None:
            widths = [10200 // count] * count
            widths[-1] += 10200 - sum(widths)
        grid = ET.SubElement(table, tag("w:tblGrid"))
        for width in widths:
            ET.SubElement(grid, tag("w:gridCol"), {tag("w:w"): str(width)})
        for row_idx, row in enumerate([headers, *rows]):
            tr = ET.SubElement(table, tag("w:tr"))
            if row_idx == 0:
                trpr = ET.SubElement(tr, tag("w:trPr"))
                ET.SubElement(trpr, tag("w:tblHeader"))
            for col_idx, value in enumerate(row):
                tc = ET.SubElement(tr, tag("w:tc"))
                tcpr = ET.SubElement(tc, tag("w:tcPr"))
                ET.SubElement(tcpr, tag("w:tcW"), {tag("w:w"): str(widths[col_idx]), tag("w:type"): "dxa"})
                if row_idx == 0:
                    ET.SubElement(tcpr, tag("w:shd"), {tag("w:fill"): PLUM, tag("w:val"): "clear"})
                elif row_idx % 2 == 0:
                    ET.SubElement(tcpr, tag("w:shd"), {tag("w:fill"): "FAF6F8", tag("w:val"): "clear"})
                p = ET.SubElement(tc, tag("w:p"))
                ppr = ET.SubElement(p, tag("w:pPr"))
                ET.SubElement(ppr, tag("w:spacing"), {tag("w:after"): "0", tag("w:before"): "0"})
                add_run(p, str(value), bold=(row_idx == 0), color=(WHITE if row_idx == 0 else INK), size=18 if row_idx == 0 else 17)
        self.paragraph("", after=60)
        return table

    def image(self, path: Path, width_in=6.8, alt="Executive report chart"):
        rid = f"rId{self.next_rid}"
        media_name = f"image{self.next_rid:02d}.png"
        self.relationships.append((rid, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"media/{media_name}"))
        self.media[media_name] = path.read_bytes()
        self.next_rid += 1
        from PIL import Image
        with Image.open(path) as im:
            ratio = im.height / im.width
        cx = int(width_in * 914400)
        cy = int(width_in * ratio * 914400)
        p = ET.SubElement(self.body, tag("w:p"))
        ppr = ET.SubElement(p, tag("w:pPr"))
        ET.SubElement(ppr, tag("w:jc"), {tag("w:val"): "center"})
        run = ET.SubElement(p, tag("w:r"))
        drawing = ET.SubElement(run, tag("w:drawing"))
        inline = ET.SubElement(drawing, tag("wp:inline"), {"distT": "0", "distB": "0", "distL": "0", "distR": "0"})
        ET.SubElement(inline, tag("wp:extent"), {"cx": str(cx), "cy": str(cy)})
        ET.SubElement(inline, tag("wp:effectExtent"), {"l": "0", "t": "0", "r": "0", "b": "0"})
        docpr = ET.SubElement(inline, tag("wp:docPr"), {"id": str(self.next_rid), "name": media_name, "descr": alt})
        frame = ET.SubElement(inline, tag("wp:cNvGraphicFramePr"))
        ET.SubElement(frame, tag("a:graphicFrameLocks"), {"noChangeAspect": "1"})
        graphic = ET.SubElement(inline, tag("a:graphic"))
        graphic_data = ET.SubElement(graphic, tag("a:graphicData"), {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"})
        pic = ET.SubElement(graphic_data, tag("pic:pic"))
        nv = ET.SubElement(pic, tag("pic:nvPicPr"))
        ET.SubElement(nv, tag("pic:cNvPr"), {"id": str(self.next_rid), "name": media_name, "descr": alt})
        ET.SubElement(nv, tag("pic:cNvPicPr"))
        fill = ET.SubElement(pic, tag("pic:blipFill"))
        ET.SubElement(fill, tag("a:blip"), {tag("r:embed"): rid})
        stretch = ET.SubElement(fill, tag("a:stretch"))
        ET.SubElement(stretch, tag("a:fillRect"))
        sppr = ET.SubElement(pic, tag("pic:spPr"))
        transform = ET.SubElement(sppr, tag("a:xfrm"))
        ET.SubElement(transform, tag("a:off"), {"x": "0", "y": "0"})
        ET.SubElement(transform, tag("a:ext"), {"cx": str(cx), "cy": str(cy)})
        geometry = ET.SubElement(sppr, tag("a:prstGeom"), {"prst": "rect"})
        ET.SubElement(geometry, tag("a:avLst"))
        return p

    def page_break(self):
        p = ET.SubElement(self.body, tag("w:p"))
        r = ET.SubElement(p, tag("w:r"))
        ET.SubElement(r, tag("w:br"), {tag("w:type"): "page"})

    def xml(self) -> bytes:
        sect = self.body.find(tag("w:sectPr"))
        if sect is None:
            sect = ET.SubElement(self.body, tag("w:sectPr"))
            ET.SubElement(sect, tag("w:pgSz"), {tag("w:w"): "12240", tag("w:h"): "15840"})
            ET.SubElement(sect, tag("w:pgMar"), {tag("w:top"): "900", tag("w:right"): "900", tag("w:bottom"): "900", tag("w:left"): "900", tag("w:header"): "420", tag("w:footer"): "420", tag("w:gutter"): "0"})
        return ET.tostring(self.root, encoding="utf-8", xml_declaration=True)


def make_styles() -> bytes:
    root = ET.Element(tag("w:styles"))
    default = ET.SubElement(root, tag("w:docDefaults"))
    rpr_default = ET.SubElement(ET.SubElement(default, tag("w:rPrDefault")), tag("w:rPr"))
    fonts = ET.SubElement(rpr_default, tag("w:rFonts"))
    fonts.set(tag("w:ascii"), "Aptos")
    fonts.set(tag("w:hAnsi"), "Aptos")
    ET.SubElement(rpr_default, tag("w:sz"), {tag("w:val"): "21"})
    ET.SubElement(rpr_default, tag("w:color"), {tag("w:val"): INK})
    definitions = [
        ("Normal", "Normal", 21, INK, False, 120, 100),
        ("Title", "Title", 52, PLUM, True, 100, 180),
        ("Subtitle", "Subtitle", 26, MUTED, False, 0, 220),
        ("Heading1", "Heading 1", 32, PLUM, True, 340, 140),
        ("Heading2", "Heading 2", 25, PINK, True, 220, 90),
        ("Heading3", "Heading 3", 22, PLUM, True, 170, 70),
        ("Caption", "Caption", 17, MUTED, False, 40, 100),
    ]
    for sid, name, size, color, bold, before, after in definitions:
        style = ET.SubElement(root, tag("w:style"), {tag("w:type"): "paragraph", tag("w:styleId"): sid})
        ET.SubElement(style, tag("w:name"), {tag("w:val"): name})
        if sid == "Normal":
            style.set(tag("w:default"), "1")
        ppr = ET.SubElement(style, tag("w:pPr"))
        ET.SubElement(ppr, tag("w:spacing"), {tag("w:before"): str(before), tag("w:after"): str(after), tag("w:line"): "280", tag("w:lineRule"): "auto"})
        if sid.startswith("Heading"):
            ET.SubElement(ppr, tag("w:keepNext"))
        rpr = ET.SubElement(style, tag("w:rPr"))
        ET.SubElement(rpr, tag("w:color"), {tag("w:val"): color})
        ET.SubElement(rpr, tag("w:sz"), {tag("w:val"): str(size)})
        ET.SubElement(rpr, tag("w:szCs"), {tag("w:val"): str(size)})
        if bold:
            ET.SubElement(rpr, tag("w:b"))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def make_header_footer():
    header = ET.Element(tag("w:hdr"))
    p = ET.SubElement(header, tag("w:p"))
    ppr = ET.SubElement(p, tag("w:pPr"))
    ET.SubElement(ppr, tag("w:jc"), {tag("w:val"): "right"})
    add_run(p, "SUGAR COSMETICS  |  INSTAGRAM ANALYTICS", bold=True, color=MUTED, size=16)
    footer = ET.Element(tag("w:ftr"))
    p = ET.SubElement(footer, tag("w:p"))
    ppr = ET.SubElement(p, tag("w:pPr"))
    ET.SubElement(ppr, tag("w:tabs"))
    ET.SubElement(ppr, tag("w:jc"), {tag("w:val"): "center"})
    add_run(p, f"Executive report  •  {date.today():%d %B %Y}     |     Page ", color=MUTED, size=16)
    r = ET.SubElement(p, tag("w:r"))
    fld = ET.SubElement(r, tag("w:fldSimple"), {tag("w:instr"): "PAGE"})
    add_run(fld, "1", color=MUTED, size=16)
    return ET.tostring(header, encoding="utf-8", xml_declaration=True), ET.tostring(footer, encoding="utf-8", xml_declaration=True)


def add_report_content(doc: ReportDocument, data: pd.DataFrame, reports: dict, input_path: Path, charts: dict, input_sha: str):
    quality = reports["quality"]
    model = reports["model"]
    conditional = reports["conditional"]
    portfolio = reports["portfolio"]
    summary = weighted_summary(data)
    engagement = summary["row_engagements"]
    total_reach = summary["reach"]
    total_engagements = summary["engagements"]
    date_start = pd.to_datetime(data["post_date"], errors="coerce").min().date()
    date_end = pd.to_datetime(data["post_date"], errors="coerce").max().date()
    total_visits = data["profile_visits"].sum()
    total_follows = data["follows"].sum()
    visits_rate = total_visits / total_reach
    follow_visit_rate = total_follows / total_visits
    follow_reach_rate = total_follows / total_reach

    # Cover page.
    logo = ROOT / "images" / "sugar_logo.png"
    if logo.is_file():
        doc.image(logo, width_in=0.9, alt="SUGAR Cosmetics logo")
    doc.paragraph("INSTAGRAM PERFORMANCE ANALYTICS", "Normal", bold=True, color=PINK, size=18, align="center", before=500, after=180)
    doc.paragraph("Executive Report", "Title", align="center")
    doc.paragraph("Performance, audience, content strategy, and model validation", "Subtitle", align="center")
    doc.paragraph(f"Prepared {date.today():%d %B %Y}", "Normal", color=MUTED, align="center", after=260)
    doc.table(
        ["REPORT SCOPE", "DETAIL"],
        [
            ["Dataset", input_path.name],
            ["Records and period", f"{len(data):,} records · {date_start:%d %b %Y} to {date_end:%d %b %Y}"],
            ["Evidence basis", "Descriptive analysis of the supplied dataset; source authenticity is not independently verified."],
        ],
        widths=[2600, 7600],
    )
    doc.callout(
        "Executive readout: recorded engagement is about 18.55% of summed post-level reach. Observed format and campaign gaps are small; the primary pre-publication model does not outperform a median baseline by a measurable amount. Use these patterns to design controlled tests, not as causal proof or verified business impact."
    )
    doc.paragraph("Prepared from the interactive Streamlit dashboard, its current analysis outputs, and the supplied source data.", "Caption", align="center", before=220)
    doc.page_break()

    # Section 1: decision summary.
    doc.heading("1. Executive summary", 1)
    doc.paragraph(
        f"The current file contains {len(data):,} rows and 14 source columns spanning {date_start:%d %B %Y}–{date_end:%d %B %Y}. "
        f"It records {fmt_int(total_engagements)} likes, comments, shares, and saves over {fmt_int(total_reach)} summed post-level reach, "
        f"for an overall weighted engagement rate of {fmt_pct(summary['weighted_rate'])}. The sum of reach is not unique account reach."
    )
    doc.table(
        ["Headline measure", "Observed value", "Interpretation"],
        [
            ["Records analyzed", f"{len(data):,}", "A dataset row is not confirmed to equal a unique post."],
            ["Weighted engagement rate", fmt_pct(summary["weighted_rate"]), "Total engagements ÷ summed positive reach."],
            ["Total engagements", fmt_int(total_engagements), "Likes + comments + shares + saves."],
            ["Summed reach", fmt_int(total_reach), "Post-level reach summed across records; not unique people."],
            ["Impressions", fmt_int(data["impressions"].sum()), "Recorded impressions; paid/organic split is unavailable."],
            ["Likes / comments", f"{fmt_int(data['likes'].sum())} / {fmt_int(data['comments'].sum())}", "Recorded interaction totals."],
            ["Shares / saves", f"{fmt_int(data['shares'].sum())} / {fmt_int(data['saves'].sum())}", "Recorded interaction totals."],
            ["Profile visits / summed reach", fmt_pct(visits_rate), "Aggregate proxy; no person-level linkage."],
            ["Follows / profile visits", fmt_pct(follow_visit_rate), "Aggregate proxy, not attributed conversion."],
            ["Follows / summed reach", fmt_pct(follow_reach_rate), "Aggregate proxy; not an incremental lift."],
        ],
        widths=[2800, 1800, 5600],
    )
    doc.heading("What matters for decisions", 2)
    doc.bullet("Stories have the highest observed format weighted rate (18.63%); Images have the lowest (18.42%). The estimated Story-versus-other gap is +0.101 percentage points with a simultaneous 95% interval that includes zero. The Image gap is −0.179 points and its interval is below zero; this is still observational and requires a comparable test before changing strategy.")
    doc.bullet("Campaign rates are tightly clustered: Influencer Collab is highest at 18.63%, while Festive Offer is lowest at 18.45%. Their simultaneous intervals versus other campaigns include zero.")
    doc.bullet("Friday is the highest weekday rate at 18.61%, but weekday rates differ by only about 0.14 percentage points from low to high. Treat this as a weak scheduling hypothesis.")
    doc.bullet("Across 58 configurations and 18 model families, Poisson regression is the leading ML candidate by temporal cross-validation. On the untouched future holdout its MAE is effectively identical to the median baseline; the one-standard-error rule selects the baseline.")
    doc.bullet("An exposure-conditional Ridge model predicts engagement volume more accurately when observed reach and impressions are known. Its result is exploratory, not a pre-publication forecast or causal estimate.")
    doc.callout("Recommendation: preserve the current mix while prioritizing powered, randomized format and message tests with attributed conversion and contribution outcomes.", accent="B66B91")

    # Section 2: scope and data.
    doc.heading("2. Dataset provenance and data quality", 1)
    doc.paragraph(
        "The dashboard uses the project CSV by default and falls back to the supplied workbook if the CSV is unavailable. "
        "A cell-by-cell normalized comparison found the CSV and workbook match across all 50,000 rows and 14 columns. "
        f"CSV SHA-256: {input_sha}. The reproducibility manifest records both file fingerprints and the environment."
    )
    doc.paragraph(
        "The file likely matches a public Instagram analytics project identified in DATA_PROVENANCE.md. The local filename, date span, and rounded aggregates support that file match; the account identity, collection method, and historical integrity were not independently verified. Results therefore describe this supplied dataset, not verified official Sugar Cosmetics account performance."
    )
    doc.table(
        ["Quality check", "Result", "Meaning"],
        [
            ["Missing cells after standardization", fmt_int(quality["dataset_summary"]["missing_cells_after_standardization"]), "No missing values detected in the standardized source."],
            ["Exact duplicate rows", fmt_int(quality["dataset_summary"]["exact_duplicate_rows"]), "No exact row duplicates; without a post ID, repeated posts cannot be ruled out."],
            ["Invalid dates", fmt_int(quality["dataset_summary"]["invalid_dates"]), "All rows have parseable dates."],
            ["Outlier review", "IQR flags in interaction metrics", "Flags are retained for source review; no rows were automatically dropped."],
            ["Collection / row grain", "Not documented", "Record counts are not confirmed unique-post counts."],
            ["Financial attribution", "Not supplied", "Revenue, spend, cost, and linked purchase outcomes are unavailable."],
        ],
        widths=[3000, 2200, 5000],
    )
    doc.paragraph(
        "Category counts are unusually balanced: formats range from 12,399 to 12,599 rows, and campaigns from 9,903 to 10,186. This pattern may reflect a sampling or data-generation process; it does not establish representativeness. The data include no caption, stable post ID, exact publication time, follower count, demographic attributes, spend, or sales attribution."
    )
    doc.paragraph(
        "IQR review flagged 674 likes rows (1.35%), 1,836 comments (3.67%), 2,180 shares (4.36%), 2,101 saves (4.20%), 635 profile visits (1.27%), 2,152 follows (4.30%), and 689 total-engagement rows (1.38%). These are distribution flags, not confirmed errors."
    )

    # Section 3: category comparisons.
    doc.heading("3. Content and campaign performance", 1)
    doc.paragraph(
        "Weighted engagement rate is total eligible interactions divided by total eligible reach within each category. The uncertainty analysis compares each category with all remaining categories using simultaneous 95% date-block bootstrap intervals (5,000 resamples; seven-day blocks; three- and fourteen-day sensitivity checks)."
    )
    doc.image(charts["category"], width_in=6.9, alt="Format and campaign weighted engagement rates with simultaneous confidence intervals")
    doc.paragraph("Observed weighted rates and difference-versus-rest results", "Caption")
    inf_rows = []
    for dimension, name in [("post_type", "Format"), ("campaign_type", "Campaign")]:
        for row in reports["inference"]["results"][dimension]:
            inf_rows.append([
                f"{name}: {row[dimension]}",
                f"{row['weighted_rate']:.2%}",
                f"{row['difference_pp']:+.3f} pp",
                f"[{row['simultaneous_ci_low_pp']:+.3f}, {row['simultaneous_ci_high_pp']:+.3f}] pp",
                f"{row['records']:,}",
            ])
    doc.table(["Category", "Weighted rate", "Difference vs rest", "95% simultaneous interval", "Rows"], inf_rows, widths=[2400, 1450, 1700, 3000, 1650])
    doc.paragraph(
        "The differences are relative to the other categories in the same dimension, not randomized estimates. The intervals account for sampled date blocks under the stated resampling assumption, but do not correct confounding. An interval excluding zero is a test hypothesis, not proof that the category caused the difference."
    )

    # Section 4: time and publishing.
    doc.heading("4. Posting cadence and timing", 1)
    doc.paragraph(
        "The 50,000 records span 366 calendar dates. December 2024 has the highest observed record volume (4,296 rows); April 2024 has the lowest (1,626), and the partial-month coverage makes volume comparisons sensitive to date-window boundaries. January 2025 has the highest monthly weighted rate (18.75%) and April 2024 the lowest (18.23%). These are records in the supplied file, not verified publishing frequency."
    )
    doc.image(charts["monthly"], width_in=6.9, alt="Monthly records in data and weighted engagement rate")
    doc.paragraph("Bars show record counts; the line shows weighted engagement rate. Volume and performance use separate vertical scales.", "Caption")
    doc.image(charts["weekday"], width_in=6.5, alt="Weighted engagement rates by weekday")
    doc.paragraph(
        "Friday has the highest observed weighted weekday rate (18.61%); Sunday is lowest (18.47%). The small spread and unverified record sampling make this directional evidence only. The source lacks exact publication time, so time-of-day optimization cannot be assessed."
    )

    # Section 5: hashtags.
    doc.heading("5. Hashtag intelligence", 1)
    doc.paragraph(
        "Hashtag analysis canonicalizes tags by case and counts each hashtag at most once per record. A record with multiple hashtags contributes to multiple tag groups, so usage counts and summed reach overlap and must not be added across tags as if independent audiences."
    )
    doc.image(charts["hashtags"], width_in=6.7, alt="Most used hashtags and weighted engagement rates")
    doc.paragraph(
        "Hashtag rate rankings can be affected by support size and content selection. Compare tag records and reach, and use these patterns to formulate a controlled creative test; they do not estimate the causal effect of adding a hashtag."
    )

    # Section 6: audience funnel.
    doc.heading("6. Audience and conversion proxies", 1)
    doc.table(
        ["Aggregate step / proxy", "Observed total", "Rate"],
        [
            ["Summed post-level reach", fmt_int(total_reach), "Reference denominator"],
            ["Profile visits", fmt_int(total_visits), fmt_pct(visits_rate)],
            ["Follows", fmt_int(total_follows), fmt_pct(follow_reach_rate)],
            ["Follows per profile visit", "Aggregate ratio", fmt_pct(follow_visit_rate)],
        ],
        widths=[3400, 3000, 3800],
    )
    doc.paragraph(
        "These values are aggregate proxies. The dataset does not connect an individual reach event to a profile visit, follow, or purchase; ratios cannot be interpreted as person-level funnel conversion or attributed business results. No demographic fields are available for fairness or subgroup analysis."
    )

    # Section 7: decision portfolio.
    doc.heading("7. Business decisions and recommended tests", 1)
    doc.paragraph(
        "Use observational analytics to prioritize experiments. The dashboard’s three decision tests use assumed baselines, minimum lifts, opportunity volumes, margins, and costs. The following economics are hypothetical illustrations, not measured project impact. The sample-size calculations assume independent binary outcomes, equal assignment, no clustering, no attrition, 80% power, and Bonferroni-adjusted two-sided alpha across three tests."
    )
    decision_rows = []
    for item in portfolio["decisions"]:
        econ = item["impact_scenario"]
        decision_rows.append([
            f"{item['sequence']}. {item['decision']}",
            f"{item['sample_size']['total']:,} total ({item['sample_size']['per_arm']:,}/arm)",
            f"{item['estimated_months_at_assumed_volume']} months",
            f"{portfolio['currency']} {econ['net_contribution_after_cost']:,.0f}",
        ])
    doc.table(["Decision test", "Estimated sample", "Illustrative duration", "Scenario net contribution"], decision_rows, widths=[3600, 2600, 1600, 2400])
    for item in portfolio["decisions"]:
        doc.heading(f"Test {item['sequence']} · {item['decision']}", 2)
        doc.paragraph(f"Sponsor: {item['sponsor']}  |  Primary outcome: {item['primary_outcome']}")
        doc.bullet(f"Design: {item['comparison']}")
        doc.bullet(f"Success gate: {item['success_action']}")
        doc.bullet(f"Hold / stop: {item['inconclusive_action']} {item['harm_action']}")
        econ = item["impact_scenario"]
        doc.paragraph(
            f"Scenario assumptions: baseline conversion {item['baseline_conversion_rate']:.2%}; minimum detectable lift {item['minimum_detectable_lift'] * 100:.2f} percentage points; "
            f"{item['monthly_opportunities']:,} monthly opportunities; net revenue per conversion {portfolio['currency']} {item['net_revenue_per_conversion']:,.0f}; "
            f"contribution margin {item['contribution_margin']:.0%}; incremental cost {portfolio['currency']} {item['incremental_campaign_cost']:,.0f}. "
            f"Illustrative net contribution after cost: {portfolio['currency']} {econ['net_contribution_after_cost']:,.0f}.",
            "Caption",
        )
    doc.callout(
        "Finance gate: reconcile attributed conversions, net revenue, variable margin, and media cost. Scale only if the pre-registered lift, net-contribution uncertainty interval, and guardrails all pass; replace every assumed scenario input with approved source values."
    )

    # Section 8: predictive evaluation.
    doc.heading("8. Predictive model validation", 1)
    doc.heading("Pre-publication engagement-rate prediction", 2)
    doc.paragraph(
        f"The model target is total engagements divided by positive reach. Pre-publication features include format, campaign, their interaction, canonical hashtag set/count, and calendar terms. Reach, impressions, engagement counts, visits, follows, and post-outcome annotations are excluded to limit leakage. Four expanding-window temporal folds with a seven-day gap tune on development dates; the final 20% of unique dates (" 
        f"{model['holdout_evaluation']['start_date']} to {model['holdout_evaluation']['end_date']}, {model['split']['holdout_records']:,} rows) remain an untouched future holdout."
    )
    doc.table(
        ["Candidate", "Temporal CV MAE", "Future holdout MAE", "Holdout R-squared"],
        [
            ["Median baseline (one-SE selected)", f"{model['baseline']['temporal_cv_mae_mean'] * 100:.6f} pp", f"{model['holdout_evaluation']['median_baseline']['mae'] * 100:.6f} pp", f"{model['holdout_evaluation']['median_baseline']['r2']:.4f}"],
            [f"Best ML: {model['tuning']['best_ml_candidate_estimator']}", f"{model['tuning']['best_ml_candidate_cv_mae'] * 100:.6f} pp", f"{model['holdout_evaluation']['best_ml_candidate']['mae'] * 100:.6f} pp", f"{model['holdout_evaluation']['best_ml_candidate']['r2']:.4f}"],
        ],
        widths=[3400, 2200, 2800, 1800],
    )
    diff_pp = model["holdout_evaluation"]["mae_difference_model_minus_baseline"] * 100
    interval = model["holdout_evaluation"]["date_block_bootstrap_mae_difference_interval"]
    doc.paragraph(
        f"The 58-configuration search covered {len(model['tuning']['model_families_tested'])} families: {', '.join(model['tuning']['model_families_tested'])}. "
        "Kernel SVR was excluded because quadratic training cost is impractical at this dataset size. Poisson regression had the lowest ML temporal-CV MAE, but its holdout MAE improvement over the median baseline was only "
        f"{diff_pp:+.8f} percentage points. The date-block 95% interval for the MAE difference was [{interval['lower_95'] * 100:+.6f}, {interval['upper_95'] * 100:+.6f}] percentage points and includes zero. "
        "The ML candidate’s holdout R² is approximately zero; a data-supported improvement is not established. The median baseline remains the selected reference, not a useful ranking model."
    )
    doc.heading("Exploratory volume prediction conditional on observed exposure", 2)
    cv = conditional["holdout"]
    doc.table(
        ["Model", "Holdout MAE", "Holdout R²", "MAE change vs baseline"],
        [
            ["Median baseline", f"{cv['median_baseline']['mae']:,.1f} engagements", f"{cv['median_baseline']['r2']:.3f}", "Reference"],
            ["Ridge regression", f"{cv['ridge']['mae']:,.1f} engagements", f"{cv['ridge']['r2']:.3f}", f"{cv['relative_mae_reduction']:.1%} lower"],
        ],
        widths=[2700, 2500, 1600, 3400],
    )
    doc.image(charts["calibration"], width_in=5.8, alt="Engagement volume model calibration by actual engagement decile")
    c_interval = cv["daily_bootstrap_mae_difference_interval"]
    doc.paragraph(
        f"The Ridge estimate conditions on observed reach and impressions to predict interaction volume for existing records; holdout R² is {cv['ridge']['r2']:.3f}, and paired daily bootstrap MAE difference is [{c_interval['lower_95']:,.1f}, {c_interval['upper_95']:,.1f}] engagements. "
        "This secondary model was selected after reviewing the dataset and uses realized exposure. Treat the performance as exploratory and do not interpret it as a pre-publication forecast, causal effect, or evidence that changing reach will cause more engagement."
    )

    # Section 9: conclusions and reproducibility.
    doc.heading("9. Recommended next steps", 1)
    for text in [
        "Keep category conclusions descriptive. Do not shift budgets or claim causal wins from these observational rates.",
        "Prioritize a format test and a message test with mutually exclusive audience assignment, comparable offers and delivery, pre-registered outcomes, and Finance-approved guardrails.",
        "Use attributed purchases and net contribution per assigned audience member as business outcomes; record cost and attribution windows consistently.",
        "Confirm row grain, stable post identity, collection method, and source ownership before describing records as official posts or generalizing beyond this file.",
        "Retain the time-forward holdout design. Re-evaluate candidate models only on a new future period; do not tune against the current holdout.",
        "Agree on operational monitoring, drift limits, and retraining triggers before considering any deployment.",
    ]:
        doc.bullet(text)

    doc.heading("Reproducibility record", 2)
    manifest = reports["manifest"]
    versions = manifest["runtime"]
    doc.table(
        ["Item", "Recorded value"],
        [
            ["Source file for dashboard/model", str(input_path.relative_to(ROOT)).replace("\\", "/")],
            ["Source CSV SHA-256", input_sha],
            ["Rows × source columns", f"{len(data):,} × {len(data.columns)}"],
            ["Python / platform", f"{versions['python']} / {versions['platform']}"],
            ["Key packages", ", ".join(f"{name} {version}" for name, version in versions["packages"].items() if version)],
            ["Model seed and splits", f"{model['tuning']['seed']}; chronological 80/20; 4 folds; 7-day gap"],
            ["Descriptive bootstrap", "5,000 draws; seed 42; 7-day blocks; 3/14-day sensitivity"],
            ["Model holdout uncertainty", f"{interval['repetitions']:,} date-block resamples; seed {model['tuning']['seed']}"],
        ],
        widths=[3000, 7200],
    )
    doc.paragraph("Reproduce from the repository root:", "Heading3")
    doc.paragraph("python -m pip install -r requirements-lock.txt", "Normal", color=PLUM, size=19)
    doc.paragraph("streamlit run app.py", "Normal", color=PLUM, size=19)
    doc.paragraph("python src/run_model_evaluation.py", "Normal", color=PLUM, size=19)
    doc.paragraph("python src/run_conditional_engagement_volume.py", "Normal", color=PLUM, size=19)
    doc.paragraph("python src/run_descriptive_inference.py", "Normal", color=PLUM, size=19)
    doc.paragraph("python src/run_decision_portfolio.py", "Normal", color=PLUM, size=19)
    doc.paragraph("python src/reproducibility_manifest.py", "Normal", color=PLUM, size=19)
    doc.paragraph("Open notebooks/01_data_validation_and_eda.ipynb and run cells in order to recreate the data-quality audit outputs.", "Normal")
    doc.paragraph("Full method and caveats are in README.md, DATA_PROVENANCE.md, BUSINESS_IMPACT_DATA_CONTRACT.md, and MODEL_MONITORING_PLAN.md.", "Caption")

    doc.heading("Appendix A. Metric definitions", 1)
    doc.table(
        ["Metric", "Definition"],
        [
            ["Total engagements", "Likes + comments + shares + saves."],
            ["Post engagement rate", "Total engagements divided by reach where reach is positive."],
            ["Weighted engagement rate", "Sum of eligible engagements divided by summed eligible post-level reach."],
            ["Profile-visit rate proxy", "Aggregate profile visits divided by summed reach; not person-level conversion."],
            ["Follow-per-visit proxy", "Aggregate follows divided by aggregate profile visits; no individual linkage."],
            ["MAE", "Mean absolute error; for the primary target it is reported in engagement-rate points."],
            ["CV-to-training gap", "Temporal-CV MAE minus training MAE; descriptive check for generalization differences."],
            ["Engagement-gap equivalent", "Observed category rate difference multiplied by that category’s summed reach; a scale translation, not incremental impact."],
        ],
        widths=[3000, 7200],
    )
    doc.paragraph(
        "Report limitations: every finding is conditional on the supplied dataset, the metric definitions available in it, and the described evaluation design. Data provenance, row grain, representativeness, and causal effects are not established by this report."
    )


def package_docx(doc: ReportDocument, output: Path):
    doc.xml()
    header_xml, footer_xml = make_header_footer()
    content_types = ET.Element("{http://schemas.openxmlformats.org/package/2006/content-types}Types")
    ct_ns = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    ET.SubElement(content_types, ct_ns + "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(content_types, ct_ns + "Default", {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(content_types, ct_ns + "Default", {"Extension": "png", "ContentType": "image/png"})
    for part, content in [
        ("word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("word/header1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"),
        ("word/footer1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"),
    ]:
        ET.SubElement(content_types, ct_ns + "Override", {"PartName": f"/{part}", "ContentType": content})
    relns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    root_rels = ET.Element(relns + "Relationships")
    ET.SubElement(root_rels, relns + "Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "word/document.xml"})
    doc_rels = ET.Element(relns + "Relationships")
    ET.SubElement(doc_rels, relns + "Relationship", {"Id": "rIdStyles", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "Target": "styles.xml"})
    ET.SubElement(doc_rels, relns + "Relationship", {"Id": "rIdHeader", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header", "Target": "header1.xml"})
    ET.SubElement(doc_rels, relns + "Relationship", {"Id": "rIdFooter", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer", "Target": "footer1.xml"})
    for rid, rel_type, target in doc.relationships:
        ET.SubElement(doc_rels, relns + "Relationship", {"Id": rid, "Type": rel_type, "Target": target})
    # Associate header/footer with the section properties.
    sect = doc.body.find(tag("w:sectPr"))
    sect.insert(0, ET.Element(tag("w:headerReference"), {tag("w:type"): "default", tag("r:id"): "rIdHeader"}))
    sect.insert(1, ET.Element(tag("w:footerReference"), {tag("w:type"): "default", tag("r:id"): "rIdFooter"}))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ET.tostring(content_types, encoding="utf-8", xml_declaration=True))
        zf.writestr("_rels/.rels", ET.tostring(root_rels, encoding="utf-8", xml_declaration=True))
        zf.writestr("word/document.xml", doc.xml())
        zf.writestr("word/styles.xml", make_styles())
        zf.writestr("word/header1.xml", header_xml)
        zf.writestr("word/footer1.xml", footer_xml)
        zf.writestr("word/_rels/document.xml.rels", ET.tostring(doc_rels, encoding="utf-8", xml_declaration=True))
        for name, image in doc.media.items():
            zf.writestr(f"word/media/{name}", image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sugar_cosmetics_instagram_data.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "Sugar_Cosmetics_Instagram_Executive_Report.docx")
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    reports_dir = ROOT / "reports"
    names = {
        "model": "model_evaluation.json",
        "conditional": "conditional_engagement_volume.json",
        "inference": "category_rate_inference.json",
        "portfolio": "assumed_decision_portfolio.json",
        "quality": "data_quality_report.json",
        "manifest": "reproducibility_manifest.json",
    }
    reports = {key: load_json(reports_dir / name) for key, name in names.items()}
    data = pd.read_csv(input_path)
    input_sha = reports["model"]["input"]["sha256"] if input_path.resolve() == (ROOT / "data" / "sugar_cosmetics_instagram_data.csv").resolve() else "Not present in the current evaluation report; regenerate the model report for this input."
    with tempfile.TemporaryDirectory(prefix="sugar-executive-report-") as temp:
        charts = build_charts(data, reports, Path(temp))
        document = ReportDocument()
        add_report_content(document, data, reports, input_path, charts, input_sha)
        package_docx(document, output_path)
    print(f"Created: {output_path.resolve()}")
    print(f"Size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
