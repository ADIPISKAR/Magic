"""Shared visual language for every SEO chart sent to Telegram.

Design goals (see /info/*SEO Telegram visualization brief*):
  * one light, modern, minimal style used everywhere -- no default
    matplotlib look ever ships to a user;
  * legible on a phone screen -- big numbers, generous padding, no
    clutter, no thin hairline text;
  * a small set of composable primitives (card, kpi tile, line, bars)
    rather than bespoke drawing code per chart.

Only matplotlib + numpy are used. Plotly/Kaleido were evaluated for this
project (see charts/README.md) and are not installed in the current
headless environment, so matplotlib with heavy custom styling is the
supported renderer, exactly as the fallback the brief allows.
"""
from __future__ import annotations

import math
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

_CACHE_DIR_ENV = 'MPLCONFIGDIR'


def _ensure_matplotlib_cache() -> None:
    """matplotlib needs a writable font-cache dir; keep it beside the charts."""
    cache_dir = Path(os.environ.get('MAGIC_SEO_MPL_CACHE', Path.home() / '.cache' / 'magic-seo-mpl'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(_CACHE_DIR_ENV, str(cache_dir))


_ensure_matplotlib_cache()

import matplotlib  # noqa: E402  (must follow MPLCONFIGDIR setup)
matplotlib.use('Agg')
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


# --------------------------------------------------------------------------
# Palette -- one light theme used by every chart. Keep it here, nowhere else.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Palette:
    page_bg: str = '#F4F6FB'        # outer figure background
    card_bg: str = '#FFFFFF'        # KPI tile / panel background
    card_border: str = '#E7EAF3'
    grid: str = '#E9ECF5'
    axis: str = '#C7CCDC'

    text_primary: str = '#111827'
    text_secondary: str = '#6B7280'
    text_muted: str = '#9AA2B1'

    brand: str = '#2F6BFF'          # primary accent (lines, highlights)
    brand_soft: str = '#DCE6FF'     # fill under primary lines
    brand_dark: str = '#1E4FD6'

    positive: str = '#16A34A'
    positive_soft: str = '#DCFCE7'
    negative: str = '#E23744'
    negative_soft: str = '#FDE2E4'
    neutral: str = '#6B7280'

    series: tuple = ('#2F6BFF', '#16A34A', '#F59E0B', '#A855F7', '#0EA5E9')

    top3: str = '#1E4FD6'
    top10: str = '#2F6BFF'
    top20: str = '#7FA6FF'
    top50: str = '#C6D7FF'
    not_found: str = '#E5E8F2'


PALETTE = Palette()


# --------------------------------------------------------------------------
# Typography / sizing
# --------------------------------------------------------------------------

FONT_FAMILY = 'DejaVu Sans'  # always present headless; no custom font install risk on the VPS

SIZE = {
    'kpi_value': 30,
    'kpi_label': 12.5,
    'kpi_delta': 12.5,
    'chart_title': 17,
    'chart_subtitle': 12,
    'axis_label': 11,
    'axis_tick': 10.5,
    'annotation': 11,
    'legend': 10.5,
    'section_title': 14.5,
    'footer': 10,
}

RADIUS = 0.05  # corner rounding used by rounded_box(), in axes fraction terms fallback


def apply_base_style() -> None:
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'text.color': PALETTE.text_primary,
        'axes.edgecolor': PALETTE.axis,
        'axes.labelcolor': PALETTE.text_secondary,
        'xtick.color': PALETTE.text_secondary,
        'ytick.color': PALETTE.text_secondary,
        'axes.titleweight': 'bold',
        'figure.facecolor': PALETTE.page_bg,
        'savefig.facecolor': PALETTE.page_bg,
        'svg.fonttype': 'none',
    })


apply_base_style()


# --------------------------------------------------------------------------
# Figure sizes tuned for Telegram on a phone.
# --------------------------------------------------------------------------

class Size:
    """(width_px, height_px, dpi) presets. All final PNGs stay <= ~1.2MP."""
    DASHBOARD = (1080, 1350, 150)     # vertical dashboard, Telegram-friendly
    DASHBOARD_TALL = (1080, 1620, 150)  # 30-day dashboard part 2
    WIDE = (1200, 675, 150)           # standalone line charts
    WIDE_TALL = (1200, 800, 150)      # line chart with extra footer stats
    CARD = (1080, 1080, 150)          # square keyword / KPI card
    COMPACT = (1080, 900, 150)        # daily compact card


def figure(size: tuple[int, int, int]):
    width_px, height_px, dpi = size
    fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor(PALETTE.page_bg)
    return fig


# --------------------------------------------------------------------------
# Drawing helpers shared by every module
# --------------------------------------------------------------------------

def rounded_panel(fig, rect, *, facecolor=None, edgecolor=None, pad=0.0, radius=0.03, zorder=0):
    """Draw a rounded rectangle "card" behind other axes at figure coords."""
    facecolor = facecolor or PALETTE.card_bg
    edgecolor = edgecolor or PALETTE.card_border
    x0, y0, w, h = rect
    box = FancyBboxPatch(
        (x0 + pad, y0 + pad), w - 2 * pad, h - 2 * pad,
        boxstyle=f'round,pad=0,rounding_size={radius}',
        linewidth=1.1, edgecolor=edgecolor, facecolor=facecolor,
        transform=fig.transFigure, zorder=zorder, mutation_aspect=1,
    )
    fig.patches.append(box)
    return box


def panel_axes(fig, rect, *, inset=(0.05, 0.07, 0.06, 0.08), radius=0.02):
    """Draw a rounded card at ``rect`` and return an Axes inset inside it.

    ``inset`` is (left, right, bottom, top) as a fraction of the panel's
    own width/height, so charts never touch the rounded corners.
    """
    rounded_panel(fig, rect, radius=radius)
    x0, y0, w, h = rect
    left, right, bottom, top = inset
    axis_rect = (
        x0 + w * left, y0 + h * bottom,
        w * (1 - left - right), h * (1 - bottom - top),
    )
    axis = fig.add_axes(axis_rect)
    axis.set_facecolor('none')
    axis.set_zorder(5)
    return axis


def hide_axes_chrome(axis, *, left=False, bottom=False):
    for spine_name in ('top', 'right'):
        axis.spines[spine_name].set_visible(False)
    axis.spines['left'].set_visible(left)
    axis.spines['bottom'].set_visible(bottom)
    if left:
        axis.spines['left'].set_color(PALETTE.axis)
    if bottom:
        axis.spines['bottom'].set_color(PALETTE.axis)


def style_grid(axis, *, axis_kind='y'):
    axis.grid(True, axis=axis_kind, color=PALETTE.grid, linewidth=1.0, zorder=0)
    axis.set_axisbelow(True)


def delta_color(value: float | None) -> str:
    if value is None or value == 0:
        return PALETTE.neutral
    return PALETTE.positive if value > 0 else PALETTE.negative


def delta_arrow(value: float | None) -> str:
    if value is None or value == 0:
        return '•'
    return '↑' if value > 0 else '↓'


def fmt_number(value, *, decimals=0, suffix='') -> str:
    if value is None:
        return '—'
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, float):
        text = f'{value:.{decimals}f}'
    else:
        text = f'{value:,}'.replace(',', ' ')
    return f'{text}{suffix}'


def fmt_signed(value, *, decimals=1, suffix='') -> str:
    if value is None:
        return '—'
    sign = '+' if value > 0 else ('-' if value < 0 else '±')
    magnitude = abs(value)
    if isinstance(magnitude, float) and magnitude.is_integer():
        body = f'{int(magnitude)}'
    else:
        body = f'{magnitude:.{decimals}f}'
    return f'{sign}{body}{suffix}'


def fmt_date_ru(iso_date: str) -> str:
    import datetime as dt
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    day = dt.date.fromisoformat(iso_date)
    return f'{day.day} {months[day.month - 1]}'


def save(fig, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format='png', facecolor=PALETTE.page_bg)
    plt.close(fig)
    try:
        path.chmod(0o600)
    except OSError:
        pass


@contextmanager
def saving(path: Path):
    """Context manager: yields a Figure, saves + closes it on exit."""
    fig = plt.figure()
    try:
        yield fig
    finally:
        save(fig, path)
