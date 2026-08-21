from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from hxg.graph import GUIDED_PATHWAYS
from hxg.io import GRAPH_DIR, PUBLIC_DIR, REPORT_DIR, ROOT, load_records, read_json, write_json
from hxg.models import Claim, RunManifest
from hxg.validation import validate_public_release

W, H = 1080, 1350
POSTER_W, POSTER_H = 1800, 2700
BG = "#061522"
SURFACE = "#0a1d2c"
SURFACE_2 = "#10283a"
INK = "#f7f3ea"
MUTED = "#9eb0bc"
FAINT = "#6f8492"
LINE = "#244156"
CYAN = "#4cc4d9"
BLUE = "#4baeff"
GREEN = "#79d35c"
AMBER = "#f5bc31"
VIOLET = "#aa87ee"
ORANGE = "#f28e37"
RED = "#ff786c"
RELEASE = "hxg-v0.3.0"
LIVE_URL = "https://lohanstruwig.github.io/hxg/"
FONT_REGULAR = "HXG-Regular"
FONT_BOLD = "HXG-Bold"

PATHWAY_COLORS = {
    "home": BLUE,
    "control": GREEN,
    "recognized": AMBER,
    "included": VIOLET,
    "secure": CYAN,
    "supported": ORANGE,
}


def _font_path(bold: bool = False) -> Path | None:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ),
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _register_fonts() -> None:
    regular = _font_path()
    bold = _font_path(True)
    if regular and FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular)))
    if bold and FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold)))


def _font(bold: bool = False) -> str:
    preferred = FONT_BOLD if bold else FONT_REGULAR
    if preferred in pdfmetrics.getRegisteredFontNames():
        return preferred
    return "Helvetica-Bold" if bold else "Helvetica"


def _color(value: str) -> HexColor:
    return HexColor(value)


def _wrap_lines(text: str, font_name: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            proposal = f"{line} {word}"
            if pdfmetrics.stringWidth(proposal, font_name, size) <= width:
                line = proposal
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _text(
    pdf: canvas.Canvas,
    page_height: float,
    x: float,
    top: float,
    text: str,
    *,
    size: float,
    width: float,
    color: str = MUTED,
    bold: bool = False,
    leading: float | None = None,
    max_lines: int | None = None,
) -> float:
    font_name = _font(bold)
    line_height = leading or size * 1.34
    lines = _wrap_lines(text, font_name, size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and pdfmetrics.stringWidth(f"{last}...", font_name, size) > width:
            last = last[:-1]
        lines[-1] = f"{last.rstrip()}..."
    text_object = pdf.beginText(x, page_height - top - size)
    text_object.setFont(font_name, size)
    text_object.setFillColor(_color(color))
    text_object.setLeading(line_height)
    for line in lines:
        text_object.textLine(line)
    pdf.drawText(text_object)
    return top + len(lines) * line_height


def _rect(
    pdf: canvas.Canvas,
    page_height: float,
    x: float,
    top: float,
    width: float,
    height: float,
    *,
    fill: str | None = None,
    stroke: str | None = None,
    radius: float = 0,
    line_width: float = 1,
) -> None:
    pdf.setLineWidth(line_width)
    pdf.setFillColor(_color(fill or BG))
    pdf.setStrokeColor(_color(stroke or fill or BG))
    draw = pdf.roundRect if radius else pdf.rect
    draw(x, page_height - top - height, width, height, radius, fill=bool(fill), stroke=bool(stroke)) if radius else draw(
        x, page_height - top - height, width, height, fill=bool(fill), stroke=bool(stroke)
    )


def _line(
    pdf: canvas.Canvas,
    page_height: float,
    x1: float,
    top1: float,
    x2: float,
    top2: float,
    *,
    color: str = LINE,
    width: float = 1,
    dash: tuple[int, ...] | None = None,
) -> None:
    pdf.setStrokeColor(_color(color))
    pdf.setLineWidth(width)
    pdf.setDash(dash or ())
    pdf.line(x1, page_height - top1, x2, page_height - top2)
    pdf.setDash()


def _dot(pdf: canvas.Canvas, page_height: float, x: float, top: float, radius: float, color: str) -> None:
    pdf.setFillColor(_color(color))
    pdf.circle(x, page_height - top, radius, fill=1, stroke=0)


def _arrow(pdf: canvas.Canvas, page_height: float, x1: float, x2: float, top: float, color: str) -> None:
    _line(pdf, page_height, x1, top, x2, top, color=color, width=1.4, dash=(8, 6))
    _line(pdf, page_height, x2 - 9, top - 6, x2, top, color=color, width=1.4)
    _line(pdf, page_height, x2 - 9, top + 6, x2, top, color=color, width=1.4)


def _header(pdf: canvas.Canvas, slide: dict[str, Any]) -> None:
    _text(pdf, H, 64, 43, "HXG", size=30, width=80, color=INK, bold=True)
    _text(pdf, H, 146, 52, "HOSPITALITY EXPERIENCE GRAPH", size=12, width=380, color=MUTED, bold=True)
    _text(pdf, H, 950, 52, f"{slide['number']:02d} / 08", size=13, width=70, color=MUTED, bold=True)
    _line(pdf, H, 64, 98, 1016, 98, width=1.4)
    _text(pdf, H, 64, 126, slide["eyebrow"], size=13, width=900, color=CYAN, bold=True)


def _footer(pdf: canvas.Canvas, slide: dict[str, Any]) -> None:
    _line(pdf, H, 64, 1248, 1016, 1248, width=1.2)
    _text(pdf, H, 64, 1260, "  |  ".join(slide["evidence_ids"]), size=14, width=820, color=CYAN, bold=True, leading=17, max_lines=3)
    _text(pdf, H, 930, 1262, RELEASE, size=13, width=86, color=FAINT, bold=True)


def _title(pdf: canvas.Canvas, text: str, *, top: float = 180, size: float = 64, width: float = 950) -> float:
    return _text(pdf, H, 64, top, text, size=size, width=width, color=INK, bold=True, leading=size * 1.02)


def _pathway_row(
    pdf: canvas.Canvas,
    page_height: float,
    *,
    top: float,
    left: float,
    width: float,
    height: float,
    capability: str,
    outcome: str,
    color: str,
    relationship_id: str | None = None,
    summary: str | None = None,
    compact: bool = False,
) -> None:
    gap = width * 0.19
    card_width = (width - gap) / 2
    _rect(pdf, page_height, left, top, card_width, height, fill=SURFACE, stroke=LINE, radius=5)
    _rect(pdf, page_height, left + card_width + gap, top, card_width, height, fill=SURFACE, stroke=color, radius=5)
    _dot(pdf, page_height, left + 24, top + height / 2, 6 if compact else 8, color)
    text_size = 14 if compact else 18
    _text(pdf, page_height, left + 43, top + (height - text_size) / 2 - 2, capability, size=text_size, width=card_width - 58, color=INK, bold=True, leading=text_size * 1.2, max_lines=2)
    _dot(pdf, page_height, left + card_width + gap + 24, top + height / 2, 6 if compact else 8, color)
    _text(pdf, page_height, left + card_width + gap + 43, top + (height - text_size) / 2 - 2, outcome, size=text_size, width=card_width - 58, color=INK, bold=True, leading=text_size * 1.2, max_lines=2)
    arrow_y = top + height / 2 + 4
    _text(pdf, page_height, left + card_width + 8, top + 14, "can support", size=11 if compact else 12, width=gap - 16, color=MUTED, bold=True)
    _arrow(pdf, page_height, left + card_width + 12, left + card_width + gap - 12, arrow_y, MUTED)
    if relationship_id:
        id_size = 12 if page_height > H else 9
        _text(pdf, page_height, left + 8, top + height + 5, relationship_id, size=id_size, width=260, color=FAINT, bold=True)
    if summary:
        _text(pdf, page_height, left + card_width + gap + 43, top + height - 27, summary, size=9, width=card_width - 58, color=MUTED, max_lines=1)


def _draw_slide(pdf: canvas.Canvas, slide: dict[str, Any], manifest: RunManifest, url: str) -> None:
    pdf.setFillColor(_color(BG))
    pdf.rect(0, 0, W, H, fill=1, stroke=0)
    _header(pdf, slide)
    number = slide["number"]

    if number == 1:
        y = _title(pdf, slide["title"], top=185, size=104, width=820)
        y = _text(pdf, H, 64, y + 20, slide["subtitle"], size=29, width=850, color=INK, bold=True, leading=37)
        _text(pdf, H, 64, y + 22, slide["body"], size=18, width=850, color=MUTED, leading=27)
        _text(pdf, H, 64, 570, "SIX GUIDED PATHWAYS", size=12, width=320, color=CYAN, bold=True)
        for index, pathway in enumerate(GUIDED_PATHWAYS):
            _pathway_row(
                pdf,
                H,
                top=605 + index * 95,
                left=64,
                width=952,
                height=66,
                capability=pathway.capability_label,
                outcome=pathway.outcome_label,
                color=PATHWAY_COLORS[pathway.lane],
                compact=True,
            )
        _text(pdf, H, 64, 1190, "Independent research. Rights-aware under the HXG source policy.", size=13, width=760, color=AMBER, bold=True)

    elif number == 2:
        y = _title(pdf, slide["title"], top=185, size=62, width=930)
        _text(pdf, H, 64, y + 16, slide["subtitle"], size=16, width=930, color=MUTED)
        for x, stat in zip((64, 382, 700), slide["stats"], strict=True):
            _rect(pdf, H, x, 430, 286, 250, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, x + 22, 464, stat["value"], size=58, width=240, color=CYAN, bold=True)
            _text(pdf, H, x + 22, 555, stat["label"], size=20, width=238, color=INK, bold=True, leading=27, max_lines=3)
            _text(pdf, H, x + 22, 642, stat["evidence_id"], size=10, width=240, color=CYAN, bold=True)
        _rect(pdf, H, 64, 730, 952, 145, fill=SURFACE_2, stroke=LINE, radius=5)
        _text(pdf, H, 88, 760, "FRAMEWORK SCOPE", size=11, width=220, color=CYAN, bold=True)
        _text(pdf, H, 88, 794, slide["scope"], size=18, width=880, color=INK, leading=27)
        _rect(pdf, H, 64, 925, 952, 170, fill=SURFACE, stroke=AMBER, radius=5)
        _text(pdf, H, 88, 955, "INTERPRETATION CAVEAT", size=11, width=260, color=AMBER, bold=True)
        _text(pdf, H, 88, 994, slide["body"], size=24, width=875, color=INK, bold=True, leading=33)

    elif number == 3:
        _title(pdf, slide["title"], top=185, size=61, width=930)
        _text(pdf, H, 64, 324, slide["body"], size=17, width=900, color=MUTED, leading=25)
        for index, pathway in enumerate(GUIDED_PATHWAYS):
            _pathway_row(
                pdf,
                H,
                top=390 + index * 132,
                left=64,
                width=952,
                height=96,
                capability=pathway.capability_label,
                outcome=pathway.outcome_label,
                color=PATHWAY_COLORS[pathway.lane],
                relationship_id=pathway.relationship_id,
            )

    elif number == 4:
        _title(pdf, slide["title"], top=185, size=58, width=930)
        labels = [("Human outcomes", CYAN), ("Measurement", VIOLET), ("Property scenarios", AMBER)]
        for index, (label, color) in enumerate(labels):
            x = 64 + index * 318
            _rect(pdf, H, x, 375, 286, 130, fill=SURFACE, stroke=color, radius=5)
            _text(pdf, H, x + 22, 410, label, size=23, width=240, color=INK, bold=True, leading=28)
            if index < 2:
                _arrow(pdf, H, x + 286, x + 318, 440, MUTED)
        _text(pdf, H, 64, 545, "PROPERTY-SPECIFIC VALUE MODELS", size=12, width=440, color=CYAN, bold=True)
        for index, formula in enumerate(slide["formulae"]):
            top = 585 + index * 158
            _rect(pdf, H, 64, top, 952, 130, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, 88, top + 24, formula["heading"], size=22, width=280, color=INK, bold=True)
            _text(pdf, H, 380, top + 23, formula["body"], size=17, width=590, color=MUTED, leading=25)
        _rect(pdf, H, 64, 1082, 952, 106, fill=SURFACE_2, stroke=LINE, radius=5)
        _text(pdf, H, 88, 1109, slide["context"], size=15, width=875, color=MUTED, leading=22)

    elif number == 5:
        _title(pdf, slide["title"], top=185, size=58, width=930)
        for index, group in enumerate(slide["groups"]):
            row, col = divmod(index, 2)
            x, top = 64 + col * 486, 420 + row * 310
            _rect(pdf, H, x, top, 458, 276, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, x + 24, top + 25, group["heading"], size=13, width=400, color=CYAN if index < 2 else AMBER, bold=True)
            _text(pdf, H, x + 24, top + 68, group["title"], size=25, width=400, color=INK, bold=True, leading=30)
            for item_index, item in enumerate(group["items"]):
                _dot(pdf, H, x + 31, top + 133 + item_index * 38, 4, CYAN if index < 2 else AMBER)
                _text(pdf, H, x + 48, top + 120 + item_index * 38, item, size=16, width=365, color=MUTED, leading=21, max_lines=2)
        _rect(pdf, H, 64, 1066, 952, 116, fill=SURFACE_2, stroke=LINE, radius=5)
        _text(pdf, H, 88, 1094, slide["context"], size=16, width=875, color=INK, bold=True, leading=23)

    elif number == 6:
        _title(pdf, slide["title"], top=185, size=54, width=930)
        _rect(pdf, H, 64, 330, 952, 74, fill=AMBER, radius=4)
        _text(pdf, H, 86, 350, "METADATA-ONLY OUTBOUND LINKS", size=13, width=700, color=BG, bold=True)
        for index, item in enumerate(slide["links"]):
            row, col = divmod(index, 2)
            x, top = 64 + col * 486, 450 + row * 246
            _rect(pdf, H, x, top, 458, 214, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, x + 22, top + 26, f"0{index + 1}", size=12, width=40, color=CYAN, bold=True)
            _text(pdf, H, x + 22, top + 62, item["product"], size=22, width=410, color=INK, bold=True, leading=28)
            _text(pdf, H, x + 22, top + 118, item["url"], size=11, width=410, color=MUTED, leading=16, max_lines=3)
        _rect(pdf, H, 64, 992, 952, 176, fill=SURFACE_2, stroke=AMBER, radius=5)
        _text(pdf, H, 86, 1018, "INDEPENDENCE DISCLOSURE", size=11, width=260, color=AMBER, bold=True)
        _text(pdf, H, 86, 1056, slide["disclosure"], size=17, width=890, color=INK, bold=True, leading=25)

    elif number == 7:
        _title(pdf, slide["title"], top=185, size=62, width=930)
        for index, state in enumerate(slide["states"]):
            x = 64 + index * 318
            color = (CYAN, VIOLET, AMBER)[index]
            _rect(pdf, H, x, 350, 286, 238, fill=SURFACE, stroke=color, radius=5)
            _text(pdf, H, x + 22, 380, state["name"], size=22, width=240, color=INK, bold=True)
            _line(pdf, H, x + 22, 430, x + 130, 430, color=color, width=4, dash=None if index == 0 else (10, 7) if index == 1 else (2, 8))
            _text(pdf, H, x + 22, 466, state["example"], size=15, width=240, color=MUTED, leading=22)
        _text(pdf, H, 64, 640, "CONTRADICTIONS AND LIMITATIONS", size=12, width=420, color=RED, bold=True)
        for index, item in enumerate(slide["contradictions"]):
            row, col = divmod(index, 2)
            x, top = 64 + col * 486, 685 + row * 140
            _rect(pdf, H, x, top, 458, 112, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, x + 22, top + 25, item, size=17, width=410, color=INK, bold=True, leading=23)
        _rect(pdf, H, 64, 1000, 952, 160, fill=SURFACE_2, stroke=LINE, radius=5)
        _text(pdf, H, 88, 1027, "MAJOR LIMIT", size=11, width=180, color=AMBER, bold=True)
        _text(pdf, H, 88, 1064, slide["limitations"], size=19, width=875, color=MUTED, leading=27)

    elif number == 8:
        _title(pdf, slide["title"], top=185, size=62, width=930)
        for index, step in enumerate(slide["method"]):
            row, col = divmod(index, 4)
            x, top = 64 + col * 238, 355 + row * 78
            _text(pdf, H, x, top, f"{index + 1:02d}", size=11, width=30, color=CYAN, bold=True)
            _text(pdf, H, x + 34, top - 1, step, size=16, width=182, color=INK, bold=True)
        counts = manifest.generated_counts
        for index, key in enumerate(slide["counts"]):
            row, col = divmod(index, 3)
            x, top = 64 + col * 318, 550 + row * 128
            _rect(pdf, H, x, top, 286, 104, fill=SURFACE, stroke=LINE, radius=5)
            _text(pdf, H, x + 18, top + 17, str(counts[key]), size=38, width=120, color=INK, bold=True)
            _text(pdf, H, x + 18, top + 72, key.upper(), size=10, width=220, color=MUTED, bold=True)
        _rect(pdf, H, 64, 835, 952, 244, fill=SURFACE_2, stroke=LINE, radius=5)
        _text(pdf, H, 88, 866, "LIVE EVIDENCE EXPLORER", size=11, width=320, color=CYAN, bold=True)
        _text(pdf, H, 88, 913, url, size=21, width=650, color=INK, bold=True)
        _text(pdf, H, 88, 960, slide["body"], size=14, width=650, color=MUTED, leading=21)
        pdf.drawImage(_qr_reader(url), 790, H - 1049, 190, 190, preserveAspectRatio=True, mask="auto")
        _text(pdf, H, 64, 1120, "Evidence cutoff: 2026-08-19  |  Audit the IDs, sources, limitations, and code.", size=14, width=930, color=AMBER, bold=True)

    _footer(pdf, slide)
    pdf.showPage()


def _qr_reader(url: str) -> ImageReader:
    code = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=4)
    code.add_data(url)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white")
    stream = BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    return ImageReader(stream)


def _create_carousel(path: Path, content: dict[str, Any], manifest: RunManifest, url: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1, invariant=1)
    pdf.setTitle("From Screen to Stay - HXG LinkedIn Carousel")
    pdf.setSubject("A rights-aware, evidence-audited framework for connected hospitality experiences")
    pdf.setAuthor("Hospitality Experience Graph (HXG)")
    pdf.setCreator("HXG deterministic Python publication pipeline")
    for slide in content["slides"]:
        _draw_slide(pdf, slide, manifest, url)
    pdf.save()


def _create_poster(path: Path, manifest: RunManifest, url: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(POSTER_W, POSTER_H), pageCompression=1, invariant=1)
    pdf.setTitle("From Screen to Stay - HXG Research Poster")
    pdf.setSubject("Six rights-aware capability-to-outcome pathways for connected hospitality")
    pdf.setAuthor("Hospitality Experience Graph (HXG)")
    pdf.setCreator("HXG deterministic Python publication pipeline")
    pdf.setFillColor(_color(BG))
    pdf.rect(0, 0, POSTER_W, POSTER_H, fill=1, stroke=0)

    _text(pdf, POSTER_H, 90, 72, "HXG", size=54, width=180, color=INK, bold=True)
    _text(pdf, POSTER_H, 275, 91, "HOSPITALITY EXPERIENCE GRAPH", size=18, width=520, color=MUTED, bold=True)
    _text(pdf, POSTER_H, 90, 178, "From Screen to Stay", size=78, width=1500, color=INK, bold=True, leading=86)
    _text(pdf, POSTER_H, 90, 286, "A rights-aware, evidence-audited framework for connected hospitality experiences.", size=34, width=1510, color=CYAN, bold=True, leading=44)
    _text(pdf, POSTER_H, 90, 360, "Working proposition: the in-room display can be treated as an orchestration layer connecting guest-facing capabilities, operational systems, and property-specific value questions.", size=25, width=1510, color=MUTED, leading=36)

    _text(pdf, POSTER_H, 90, 510, "FRAMEWORK AT A GLANCE", size=16, width=400, color=CYAN, bold=True)
    evidence = [
        ("6", "experience pathways", "CLM-HXG-PROPOSITION-01"),
        ("3", "evidence states", "CLM-GRAPHRAG-METHOD-01"),
        ("1", "auditable framework", "CLM-HXG-PROPOSITION-01"),
    ]
    for index, (value, label, claim_id) in enumerate(evidence):
        x = 90 + index * 540
        _rect(pdf, POSTER_H, x, 558, 500, 220, fill=SURFACE, stroke=LINE, radius=7)
        _text(pdf, POSTER_H, x + 28, 593, value, size=54, width=430, color=CYAN, bold=True)
        _text(pdf, POSTER_H, x + 28, 672, label, size=22, width=430, color=INK, bold=True)
        _text(pdf, POSTER_H, x + 28, 730, claim_id, size=16, width=430, color=MUTED, bold=True)
    _text(pdf, POSTER_H, 90, 812, "The six pathways are analytical propositions for testing - not empirical guest preferences, causal findings, or universal product claims.", size=20, width=1550, color=AMBER, bold=True)
    _line(pdf, POSTER_H, 90, 878, 1710, 878, width=2)

    _text(pdf, POSTER_H, 90, 925, "SIX GUIDED PATHWAYS", size=16, width=420, color=CYAN, bold=True)
    _text(pdf, POSTER_H, 90, 968, "Capabilities can support guest outcomes; they do not prove perception or value.", size=23, width=1450, color=INK, bold=True)
    for index, pathway in enumerate(GUIDED_PATHWAYS):
        _pathway_row(
            pdf,
            POSTER_H,
            top=1040 + index * 180,
            left=90,
            width=1620,
            height=126,
            capability=pathway.capability_label,
            outcome=pathway.outcome_label,
            color=PATHWAY_COLORS[pathway.lane],
            relationship_id=pathway.relationship_id,
        )

    _line(pdf, POSTER_H, 90, 2140, 1710, 2140, width=2)
    _rect(pdf, POSTER_H, 90, 2190, 760, 310, fill=SURFACE, stroke=LINE, radius=7)
    _text(pdf, POSTER_H, 120, 2225, "VALUE WITH DIFFERENT PROOF BURDENS", size=15, width=660, color=CYAN, bold=True)
    _text(pdf, POSTER_H, 120, 2272, "Human value", size=26, width=260, color=INK, bold=True)
    _text(pdf, POSTER_H, 120, 2315, "Comfort, control, familiarity, inclusion, security, and support.", size=18, width=660, color=MUTED, leading=27)
    _text(pdf, POSTER_H, 120, 2390, "Property value", size=26, width=260, color=INK, bold=True)
    _text(pdf, POSTER_H, 120, 2433, "Energy, support, and ancillary scenarios require local baselines, attribution, and verification.", size=18, width=660, color=MUTED, leading=27)

    _rect(pdf, POSTER_H, 890, 2190, 500, 310, fill=SURFACE, stroke=LINE, radius=7)
    _text(pdf, POSTER_H, 920, 2225, "EVIDENCE STATES", size=15, width=400, color=CYAN, bold=True)
    for index, (label, color, description) in enumerate(
        [
            ("Direct fact", CYAN, "Solid"),
            ("Supported inference", VIOLET, "Dashed"),
            ("Modeled scenario", AMBER, "Dotted"),
        ]
    ):
        top = 2280 + index * 66
        _line(pdf, POSTER_H, 920, top + 12, 1040, top + 12, color=color, width=5, dash=None if index == 0 else (12, 8) if index == 1 else (2, 10))
        _text(pdf, POSTER_H, 1070, top, label, size=18, width=270, color=INK, bold=True)
        _text(pdf, POSTER_H, 1070, top + 29, description, size=12, width=200, color=MUTED)

    counts = manifest.generated_counts
    count_text = "  |  ".join(f"{counts[key]} {key}" for key in ("sources", "claims", "entities", "relationships", "contradictions", "countries"))
    _text(pdf, POSTER_H, 90, 2540, count_text, size=17, width=1300, color=INK, bold=True)
    _text(pdf, POSTER_H, 90, 2590, url, size=22, width=1260, color=CYAN, bold=True)
    _text(pdf, POSTER_H, 90, 2630, "Independent research  |  Evidence cutoff 2026-08-19  |  Rights-aware under the HXG source policy", size=15, width=1300, color=FAINT, bold=True)
    pdf.drawImage(_qr_reader(url), 1460, POSTER_H - 2630, 190, 190, preserveAspectRatio=True, mask="auto")
    pdf.save()


def _verify_live_url(url: str) -> None:
    response = httpx.get(url, follow_redirects=True, timeout=20)
    response.raise_for_status()
    if "Hospitality Experience Graph" not in response.text:
        raise RuntimeError("Live URL did not return the HXG explorer")


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def build_publication(*, verified_url: str | None = None) -> None:
    validate_public_release()
    url = verified_url or LIVE_URL
    if verified_url:
        _verify_live_url(verified_url)
    _register_fonts()
    manifest_path = PUBLIC_DIR / "run-manifest.json"
    manifest_data = read_json(manifest_path)
    manifest = RunManifest.model_validate(manifest_data)
    claims = {record.id for record in load_records(PUBLIC_DIR / "claims.json", Claim)}
    content = read_json(ROOT / "reports" / "content" / "carousel.json")
    if content["release"] != RELEASE:
        raise RuntimeError(f"Publication content release must be {RELEASE}")
    for slide in content["slides"]:
        missing = set(slide["evidence_ids"]) - claims
        if missing:
            raise RuntimeError(f"Slide {slide['number']} has missing evidence IDs: {sorted(missing)}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    carousel_path = REPORT_DIR / "linkedin-carousel.pdf"
    poster_path = REPORT_DIR / "hxg-poster.pdf"
    _create_carousel(carousel_path, content, manifest, url)
    _create_poster(poster_path, manifest, url)

    output_paths = {
        "carousel_pdf": carousel_path,
        "poster_pdf": poster_path,
        "graph_json": GRAPH_DIR / "hospitality-experience-graph.json",
        "graph_graphml": GRAPH_DIR / "hospitality-experience-graph.graphml",
        "guided_map_svg": GRAPH_DIR / "hospitality-experience-map.svg",
    }
    output_hashes = {name: _sha256(path) for name, path in output_paths.items()}
    manifest_data["output_hashes"] = output_hashes
    write_json(manifest_path, manifest_data)
    write_json(
        REPORT_DIR / "publication-manifest.json",
        {
            "release": content["release"],
            "verified_url": url,
            "qr_included": True,
            "carousel_pages": len(content["slides"]),
            "carousel_size": [W, H],
            "poster_size": [POSTER_W, POSTER_H],
            "evidence_cutoff": manifest.cutoff_date.isoformat(),
            "generated_counts": manifest.generated_counts,
            "output_hashes": output_hashes,
            "alt_text": {str(slide["number"]): slide["alt_text"] for slide in content["slides"]},
        },
    )
