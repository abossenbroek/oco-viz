"""Text annotations overlay using PIL/Pillow on rendered frames."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import AnnotationConfig


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font with graceful fallback.

    Tries DejaVu Sans, then Helvetica, then PIL default bitmap font.
    """
    candidates = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "Helvetica.ttf",
        "Arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    opacity: float,
) -> None:
    """Draw a semi-transparent dark rectangle as text background panel.

    Parameters
    ----------
    draw
        PIL ImageDraw on an RGBA overlay image.
    bbox
        (x0, y0, x1, y1) rectangle bounds.
    opacity
        Panel opacity in [0, 1].
    """
    alpha = int(opacity * 255)
    draw.rectangle(bbox, fill=(0, 0, 0, alpha))


def _draw_text_with_panel(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_rgba: tuple[int, ...],
    panel_pad: int,
    panel_opacity: float,
) -> None:
    """Draw text with a dark panel behind it."""
    bbox = draw.textbbox(position, text, font=font)
    _draw_panel(
        draw,
        (
            int(bbox[0]) - panel_pad,
            int(bbox[1]) - panel_pad,
            int(bbox[2]) + panel_pad,
            int(bbox[3]) + panel_pad,
        ),
        panel_opacity,
    )
    draw.text(position, text, font=font, fill=text_rgba)


def _draw_scale_bar(
    draw: ImageDraw.ImageDraw,
    w: int,
    h: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_rgba: tuple[int, ...],
    annotation_cfg: AnnotationConfig,
    grid_dx_m: float,
    panel_pad: int,
    margin: int,
    *,
    pixels_per_km: float | None = None,
) -> None:
    """Draw a scale bar in the bottom-left area of the frame."""
    bar_km = 10.0
    if pixels_per_km is not None:
        bar_length_px = int(bar_km * pixels_per_km)
    else:
        bar_length_px = int(bar_km * 1000.0 / grid_dx_m * (w / 100.0))
    bar_length_px = max(min(bar_length_px, w // 3), 40)

    bar_y = h - margin - 50
    bar_x0 = margin
    bar_x1 = bar_x0 + bar_length_px

    # Panel behind scale bar
    _draw_panel(
        draw,
        (
            bar_x0 - panel_pad,
            bar_y - annotation_cfg.font_size - panel_pad * 2,
            bar_x1 + panel_pad,
            bar_y + 6 + panel_pad,
        ),
        annotation_cfg.panel_opacity,
    )

    # Draw bar line and end ticks
    bar_thickness = 3
    tick_h = 8
    draw.rectangle((bar_x0, bar_y, bar_x1, bar_y + bar_thickness), fill=text_rgba)
    draw.rectangle(
        (bar_x0, bar_y - tick_h, bar_x0 + 2, bar_y + bar_thickness), fill=text_rgba
    )
    draw.rectangle(
        (bar_x1 - 2, bar_y - tick_h, bar_x1, bar_y + bar_thickness), fill=text_rgba
    )

    # Label
    label = f"{bar_km:.0f} km"
    draw.text(
        (bar_x0 + bar_length_px // 2, bar_y - annotation_cfg.font_size - panel_pad),
        label,
        font=font,
        fill=text_rgba,
        anchor="mt",
    )


def apply_annotations(
    rgb: NDArray[np.float32],
    annotation_cfg: AnnotationConfig,
    frame_meta: dict[str, Any],
) -> NDArray[np.float32]:
    """Apply text annotations onto a rendered frame.

    Draws timestamp, facility name, credits, and scale bar as configured.
    Text is rendered with semi-transparent dark panels behind it for legibility.

    Parameters
    ----------
    rgb
        Float32 RGB image array with shape (H, W, 3) and values in [0, 1].
    annotation_cfg
        Annotation configuration (which elements to show, font size, etc.).
    frame_meta
        Metadata dict with keys: ``timestamp``, ``frame_index``,
        ``total_frames``, ``grid_dx_m``.

    Returns
    -------
    NDArray[np.float32]
        Annotated image with same shape and dtype as input.

    Note
    ----
    The float32 → uint8 → float32 round-trip through PIL introduces 8-bit
    quantization, which may cause visible banding in smooth gradients. This is
    inherent to PIL text rendering; use higher bit-depth libraries if banding
    is unacceptable.
    """
    h, w = rgb.shape[:2]

    # Early return if nothing is enabled
    if not any(
        (
            annotation_cfg.show_timestamp,
            annotation_cfg.show_facility,
            annotation_cfg.show_credits,
            annotation_cfg.show_scale_bar,
        )
    ):
        return rgb.copy()

    # Convert float32 [0,1] to uint8 PIL Image
    img_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    base = Image.fromarray(img_uint8, mode="RGB").convert("RGBA")

    # Create transparent overlay for compositing
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = _load_font(annotation_cfg.font_size)
    text_color_uint8 = tuple(int(c * 255) for c in annotation_cfg.text_color)
    text_rgba = (*text_color_uint8, 255)

    margin = 12
    panel_pad = 6

    # Scale bar (bottom-left, above timestamp area)
    if annotation_cfg.show_scale_bar:
        grid_dx_m = float(frame_meta.get("grid_dx_m", 1000.0))
        _draw_scale_bar(
            draw, w, h, font, text_rgba, annotation_cfg, grid_dx_m, panel_pad, margin,
            pixels_per_km=frame_meta.get("pixels_per_km"),
        )

    # Timestamp (bottom-left)
    if annotation_cfg.show_timestamp:
        ts = str(frame_meta.get("timestamp", ""))
        frame_idx = frame_meta.get("frame_index", 0)
        total = frame_meta.get("total_frames", 1)
        ts_text = f"{ts}  [{frame_idx}/{total}]"
        ts_y = h - margin - annotation_cfg.font_size - 4
        _draw_text_with_panel(
            draw, (margin, ts_y), ts_text, font, text_rgba, panel_pad,
            annotation_cfg.panel_opacity,
        )

    # Facility name (top-left)
    if annotation_cfg.show_facility:
        _draw_text_with_panel(
            draw, (margin, margin), annotation_cfg.facility_name, font, text_rgba,
            panel_pad, annotation_cfg.panel_opacity,
        )

    # Credits (bottom-right)
    if annotation_cfg.show_credits:
        credit_text = "oco-viz | OCO-3 / CAMS"
        cred_y = h - margin - annotation_cfg.font_size - 4
        cred_bbox = draw.textbbox((0, 0), credit_text, font=font)
        cred_w = cred_bbox[2] - cred_bbox[0]
        cred_x = w - margin - cred_w
        _draw_text_with_panel(
            draw, (cred_x, cred_y), credit_text, font, text_rgba, panel_pad,
            annotation_cfg.panel_opacity,
        )

    # Composite overlay onto base
    composite = Image.alpha_composite(base, overlay)

    # Convert back to float32 [0,1] RGB
    return np.array(composite.convert("RGB"), dtype=np.float32) / 255.0
