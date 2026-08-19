from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import httpx
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

from hxg.io import PUBLIC_DIR, REPORT_DIR, ROOT, load_records, read_json, write_json
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
COLORS = {"blue": BLUE, "green": GREEN, "amber": AMBER, "violet": VIOLET, "cyan": CYAN, "orange": ORANGE}


def _font_path(bold: bool = False) -> str:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(bold), size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            proposal = f"{line} {word}"
            if draw.textbbox((0, 0), proposal, font=face)[2] <= width:
                line = proposal
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def paragraph(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    width: int,
    color: str = MUTED,
    bold: bool = False,
    spacing: int | None = None,
) -> int:
    face = font(size, bold)
    line_spacing = spacing or int(size * 1.35)
    x, y = xy
    for line in wrap(draw, text, face, width):
        draw.text((x, y), line, font=face, fill=color)
        y += line_spacing
    return y


def header(draw: ImageDraw.ImageDraw, slide: dict[str, Any]) -> int:
    draw.text((64, 48), "HXG", font=font(30, True), fill=INK)
    draw.text((146, 57), "HOSPITALITY EXPERIENCE GRAPH", font=font(13, True), fill=MUTED)
    draw.text((952, 54), f"{slide['number']:02d} / 08", font=font(14, True), fill=MUTED)
    draw.line((64, 98, 1016, 98), fill=LINE, width=2)
    draw.text((64, 132), slide["eyebrow"], font=font(15, True), fill=CYAN)
    return 178


def footer(draw: ImageDraw.ImageDraw, slide: dict[str, Any]) -> None:
    evidence = " · ".join(slide["evidence_ids"])
    draw.line((64, 1250, 1016, 1250), fill=LINE, width=2)
    paragraph(draw, (64, 1268), evidence, size=14, width=820, color=CYAN, bold=True, spacing=18)
    draw.text((925, 1270), "hxg-v0.1.0", font=font(13, True), fill=FAINT)


def base_slide(slide: dict[str, Any]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    header(draw, slide)
    return image, draw


def title(draw: ImageDraw.ImageDraw, text: str, y: int, size: int = 70, width: int = 930) -> int:
    return paragraph(draw, (64, y), text, size=size, width=width, color=INK, bold=True, spacing=int(size * 1.02))


def _render_slide(slide: dict[str, Any], manifest: RunManifest, verified_url: str | None) -> Image.Image:
    image, draw = base_slide(slide)
    number = slide["number"]

    if number == 1:
        y = title(draw, slide["title"], 205, size=118, width=820)
        y += 36
        y = paragraph(draw, (64, y), slide["subtitle"], size=38, width=880, color=INK, spacing=48)
        y += 32
        paragraph(draw, (64, y), slide["body"], size=25, width=575, color=MUTED, spacing=36)
        cx, cy = 830, 880
        draw.ellipse((cx - 98, cy - 98, cx + 98, cy + 98), fill=INK)
        paragraph(draw, (cx - 65, cy - 34), "HUMAN\nEXPERIENCE", size=21, width=132, color=BG, bold=True, spacing=26)
        points = [(830, 650, BLUE), (1010, 770, GREEN), (1000, 995, AMBER), (830, 1105, VIOLET), (660, 995, CYAN), (650, 770, ORANGE)]
        for px, py, color in points:
            dx, dy = px - cx, py - cy
            distance = math.hypot(dx, dy)
            ux, uy = dx / distance, dy / distance
            draw.line((cx + ux * 98, cy + uy * 98, px - ux * 23, py - uy * 23), fill=LINE, width=3)
            draw.ellipse((px - 23, py - 23, px + 23, py + 23), fill=color, outline=BG, width=5)
        draw.text((64, 1134), "Independent research · No Samsung sponsorship or endorsement", font=font(18, True), fill=AMBER)

    elif number == 2:
        y = title(draw, slide["title"], 204, size=66, width=920)
        paragraph(draw, (64, y + 22), slide["subtitle"], size=18, width=900, color=MUTED)
        x_positions = [64, 378, 692]
        for x, stat in zip(x_positions, slide["stats"], strict=True):
            draw.rectangle((x, 520, x + 280, 870), fill=SURFACE, outline=LINE, width=2)
            draw.text((x + 24, 565), stat["value"], font=font(70, True), fill=CYAN)
            paragraph(draw, (x + 24, 670), stat["label"], size=25, width=230, color=INK, bold=True, spacing=32)
            draw.text((x + 24, 813), stat["evidence_id"], font=font(13, True), fill=CYAN)
        draw.rectangle((64, 930, 1016, 1122), fill=SURFACE_2)
        paragraph(draw, (92, 966), slide["body"], size=29, width=880, color=INK, bold=True, spacing=39)

    elif number == 3:
        title(draw, slide["title"], 204, size=70)
        cx, cy = 540, 740
        draw.ellipse((cx - 126, cy - 126, cx + 126, cy + 126), fill=INK)
        paragraph(draw, (cx - 86, cy - 38), "HUMAN\nEXPERIENCE", size=26, width=172, color=BG, bold=True, spacing=31)
        radius = 350
        for idx, outcome in enumerate(slide["outcomes"]):
            angle = -math.pi / 2 + idx * math.pi / 3
            ox = int(cx + math.cos(angle) * radius)
            oy = int(cy + math.sin(angle) * radius)
            color = COLORS[outcome["color"]]
            dx, dy = ox - cx, oy - cy
            distance = math.hypot(dx, dy)
            ux, uy = dx / distance, dy / distance
            draw.line((cx + ux * 126, cy + uy * 126, ox - ux * 76, oy - uy * 76), fill=LINE, width=4)
            draw.ellipse((ox - 76, oy - 76, ox + 76, oy + 76), fill=color, outline=BG, width=6)
            paragraph(draw, (ox - 59, oy - 31), outcome["name"], size=18, width=118, color=BG, bold=True, spacing=22)
            tx = max(45, min(835, ox - 90))
            ty = oy + 88 if oy <= cy else oy - 132
            paragraph(draw, (tx, ty), outcome["detail"], size=14, width=180, color=MUTED, spacing=19)

    elif number == 4:
        y = title(draw, slide["title"], 204, size=62)
        for idx, column in enumerate(slide["columns"]):
            x = 64 + idx * 486
            draw.rectangle((x, y + 28, x + 458, y + 300), fill=SURFACE, outline=LINE, width=2)
            draw.text((x + 26, y + 58), column["heading"], font=font(30, True), fill=CYAN if idx == 0 else AMBER)
            paragraph(draw, (x + 26, y + 118), column["body"], size=21, width=398, color=INK, spacing=31)
        fy = y + 350
        draw.text((64, fy), "PROPERTY-SPECIFIC MODELS", font=font(15, True), fill=CYAN)
        for formula in slide["formulae"]:
            draw.rectangle((64, fy + 42, 1016, fy + 118), fill=SURFACE_2)
            paragraph(draw, (88, fy + 62), formula, size=18, width=880, color=INK, bold=True, spacing=24)
            fy += 96
        paragraph(draw, (64, fy + 54), slide["context"], size=17, width=930, color=MUTED, spacing=24)

    elif number == 5:
        y = title(draw, slide["title"], 204, size=61)
        y += 32
        for idx, stakeholder in enumerate(slide["stakeholders"]):
            row, col = divmod(idx, 2)
            x, sy = 64 + col * 486, y + row * 176
            draw.rectangle((x, sy, x + 458, sy + 150), fill=SURFACE, outline=LINE, width=2)
            draw.text((x + 24, sy + 22), stakeholder["name"], font=font(25, True), fill=COLORS[list(COLORS)[idx]])
            paragraph(draw, (x + 24, sy + 68), stakeholder["value"], size=17, width=400, color=MUTED, spacing=23)
        draw.rectangle((64, 1050, 1016, 1178), fill=SURFACE_2)
        paragraph(draw, (88, 1080), slide["context"], size=20, width=880, color=INK, bold=True, spacing=28)

    elif number == 6:
        y = title(draw, slide["title"], 204, size=58)
        paragraph(draw, (64, y + 18), slide["body"], size=22, width=930, color=MUTED, spacing=31)
        ay = y + 164
        for idx, item in enumerate(slide["architecture"]):
            x = 64 + (idx % 2) * 486
            sy = ay + (idx // 2) * 112
            draw.rectangle((x, sy, x + 458, sy + 88), fill=SURFACE, outline=LINE, width=2)
            draw.text((x + 22, sy + 29), item, font=font(21, True), fill=INK)
        draw.rectangle((64, 1086, 1016, 1188), fill=SURFACE_2)
        paragraph(draw, (86, 1106), slide["limitations"], size=17, width=886, color=AMBER, bold=True, spacing=23)

    elif number == 7:
        y = title(draw, slide["title"], 204, size=70)
        sy = y + 38
        for state in slide["states"]:
            draw.rectangle((64, sy, 1016, sy + 142), fill=SURFACE, outline=LINE, width=2)
            if state["style"] == "solid":
                draw.line((90, sy + 46, 230, sy + 46), fill=CYAN, width=5)
            elif state["style"] == "dashed":
                for x in range(90, 230, 24):
                    draw.line((x, sy + 46, x + 12, sy + 46), fill=VIOLET, width=5)
            else:
                for x in range(90, 230, 18):
                    draw.ellipse((x, sy + 42, x + 7, sy + 49), fill=AMBER)
            draw.text((260, sy + 25), state["name"], font=font(25, True), fill=INK)
            paragraph(draw, (260, sy + 73), state["example"], size=18, width=720, color=MUTED, spacing=24)
            sy += 164
        draw.text((64, sy + 18), "CONTRADICTIONS RECORDED", font=font(15, True), fill=RED)
        for idx, item in enumerate(slide["contradictions"]):
            x = 64 + (idx % 2) * 486
            yy = sy + 62 + (idx // 2) * 88
            draw.text((x, yy), "×", font=font(24, True), fill=RED)
            paragraph(draw, (x + 34, yy + 2), item, size=18, width=404, color=INK, bold=True, spacing=24)

    elif number == 8:
        y = title(draw, slide["title"], 204, size=70)
        y += 28
        method_text = "  →  ".join(slide["method"])
        paragraph(draw, (64, y), method_text, size=18, width=930, color=CYAN, bold=True, spacing=27)
        counts = manifest.generated_counts
        cy = y + 112
        for idx, key in enumerate(slide["counts"]):
            row, col = divmod(idx, 3)
            x, sy = 64 + col * 318, cy + row * 142
            draw.rectangle((x, sy, x + 290, sy + 116), fill=SURFACE, outline=LINE, width=2)
            draw.text((x + 20, sy + 16), str(counts[key]), font=font(45, True), fill=INK)
            draw.text((x + 20, sy + 78), key.upper(), font=font(13, True), fill=MUTED)
        body_y = cy + 320
        paragraph(draw, (64, body_y), slide["body"], size=19, width=670, color=MUTED, spacing=27)
        if verified_url:
            qr = qrcode.make(verified_url).convert("RGB").resize((218, 218))
            image.paste(qr, (798, body_y))
            paragraph(draw, (64, body_y + 184), verified_url, size=20, width=700, color=CYAN, bold=True, spacing=27)
        else:
            draw.rectangle((798, body_y, 1016, body_y + 218), outline=LINE, width=2)
            paragraph(draw, (824, body_y + 50), "QR added only\nafter live URL\nverification", size=17, width=166, color=FAINT, bold=True, spacing=25)
            paragraph(draw, (64, body_y + 184), "Live explorer URL is inserted after deployment verification.", size=18, width=690, color=AMBER, bold=True, spacing=25)

    footer(draw, slide)
    return image


def _write_raster_pdf(images: list[Path], output: Path, size: tuple[int, int]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=size, pageCompression=1, invariant=1)
    for image_path in images:
        pdf.drawImage(str(image_path), 0, 0, width=size[0], height=size[1])
        pdf.showPage()
    pdf.save()


def _render_poster(manifest: RunManifest, verified_url: str | None) -> Image.Image:
    image = Image.new("RGB", (POSTER_W, POSTER_H), BG)
    draw = ImageDraw.Draw(image)
    draw.text((90, 80), "HXG", font=font(58, True), fill=INK)
    draw.text((90, 168), "FROM SCREEN TO STAY", font=font(30, True), fill=CYAN)
    paragraph(draw, (90, 245), "An AI-led, evidence-audited map of connected hospitality experiences.", size=62, width=1510, color=INK, bold=True, spacing=74)
    paragraph(draw, (90, 455), "The in-room display is becoming an experience-orchestration layer connecting guest comfort, property operations, and ecosystem value.", size=31, width=1510, color=MUTED, spacing=44)
    cx, cy = 900, 1160
    draw.ellipse((cx - 165, cy - 165, cx + 165, cy + 165), fill=INK)
    paragraph(draw, (cx - 115, cy - 55), "HUMAN\nEXPERIENCE", size=37, width=230, color=BG, bold=True, spacing=44)
    outcomes = [("FEEL AT HOME", BLUE), ("FEEL IN CONTROL", GREEN), ("FEEL RECOGNIZED", AMBER), ("FEEL INCLUDED", VIOLET), ("FEEL SECURE", CYAN), ("FEEL SUPPORTED", ORANGE)]
    for idx, (name, color) in enumerate(outcomes):
        angle = -math.pi / 2 + idx * math.pi / 3
        ox, oy = int(cx + math.cos(angle) * 470), int(cy + math.sin(angle) * 470)
        dx, dy = ox - cx, oy - cy
        distance = math.hypot(dx, dy)
        ux, uy = dx / distance, dy / distance
        draw.line((cx + ux * 165, cy + uy * 165, ox - ux * 108, oy - uy * 108), fill=LINE, width=6)
        draw.ellipse((ox - 108, oy - 108, ox + 108, oy + 108), fill=color, outline=BG, width=9)
        paragraph(draw, (ox - 78, oy - 28), name, size=23, width=156, color=BG, bold=True, spacing=28)
    draw.rectangle((90, 1770, 1710, 2070), fill=SURFACE, outline=LINE, width=3)
    metrics = [("74%", "smart-TV availability"), ("62%", "guest usage"), ("44,787", "survey respondents"), ("$805B", "2026 U.S. hotel guest spending context")]
    for idx, (value, label) in enumerate(metrics):
        x = 125 + idx * 400
        draw.text((x, 1830), value, font=font(56, True), fill=CYAN if idx < 3 else AMBER)
        paragraph(draw, (x, 1910), label, size=21, width=330, color=MUTED, spacing=29)
    counts = manifest.generated_counts
    draw.text((90, 2160), "FROZEN RELEASE", font=font(20, True), fill=CYAN)
    count_text = "  ·  ".join(f"{counts[key]} {key}" for key in ("sources", "claims", "entities", "relationships", "contradictions", "countries"))
    paragraph(draw, (90, 2204), count_text, size=28, width=1520, color=INK, bold=True, spacing=40)
    paragraph(draw, (90, 2324), "Solid = direct fact  ·  Dashed = supported inference  ·  Dotted = modeled scenario", size=25, width=1500, color=MUTED, spacing=34)
    if verified_url:
        qr = qrcode.make(verified_url).convert("RGB").resize((230, 230))
        image.paste(qr, (1450, 2370))
        paragraph(draw, (90, 2450), verified_url, size=28, width=1280, color=CYAN, bold=True, spacing=38)
    else:
        paragraph(draw, (90, 2450), "Public URL and QR are added only after live deployment verification.", size=28, width=1250, color=AMBER, bold=True, spacing=38)
    draw.text((90, 2630), "Independent research · No Samsung sponsorship or endorsement · Cutoff 2026-08-19", font=font(20, True), fill=FAINT)
    return image


def _verify_live_url(url: str) -> None:
    response = httpx.get(url, follow_redirects=True, timeout=20)
    response.raise_for_status()
    if "Hospitality Experience Graph" not in response.text:
        raise RuntimeError("Live URL did not return the HXG explorer")


def build_publication(*, verified_url: str | None = None) -> None:
    validate_public_release()
    if verified_url:
        _verify_live_url(verified_url)
    manifest = RunManifest.model_validate(read_json(PUBLIC_DIR / "run-manifest.json"))
    claims = {record.id for record in load_records(PUBLIC_DIR / "claims.json", Claim)}
    content = read_json(ROOT / "reports" / "content" / "carousel.json")
    for slide in content["slides"]:
        missing = set(slide["evidence_ids"]) - claims
        if missing:
            raise RuntimeError(f"Slide {slide['number']} has missing evidence IDs: {sorted(missing)}")

    rendered = REPORT_DIR / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    for slide in content["slides"]:
        page = rendered / f"carousel-{slide['number']:02d}.png"
        _render_slide(slide, manifest, verified_url).save(page, format="PNG", optimize=True)
        pages.append(page)
    _write_raster_pdf(pages, REPORT_DIR / "linkedin-carousel.pdf", (W, H))

    poster_path = rendered / "hxg-poster.png"
    _render_poster(manifest, verified_url).save(poster_path, format="PNG", optimize=True)
    _write_raster_pdf([poster_path], REPORT_DIR / "hxg-poster.pdf", (POSTER_W, POSTER_H))

    write_json(
        REPORT_DIR / "publication-manifest.json",
        {
            "release": content["release"],
            "verified_url": verified_url,
            "qr_included": bool(verified_url),
            "carousel_pages": len(pages),
            "carousel_size": [W, H],
            "poster_size": [POSTER_W, POSTER_H],
            "evidence_cutoff": manifest.cutoff_date.isoformat(),
            "generated_counts": manifest.generated_counts,
            "alt_text": {str(slide["number"]): slide["alt_text"] for slide in content["slides"]},
        },
    )
