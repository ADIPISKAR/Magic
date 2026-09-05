"""Small reusable visual building blocks shared by every dashboard.

Every function here draws into an existing ``Figure`` at a rectangle given
in figure-fraction coordinates ``(x0, y0, width, height)`` so composite
dashboards can lay tiles out on a grid without each chart re-inventing
card chrome, fonts or colors.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Sequence

import matplotlib.pyplot as plt

from . import theme
from .theme import PALETTE, SIZE, fmt_date_ru, fmt_number, fmt_signed, delta_color, delta_arrow


def kpi_tile(
    fig, rect, *, label: str, value, delta=None, delta_is_percent: bool = False,
    value_suffix: str = '', good_direction: int = 1, sparkline: Sequence[float] | None = None,
    invert_delta_color: bool = False, invert_sparkline: bool = False,
):
    """A single KPI card: label, big value, colored delta, optional sparkline.

    ``good_direction`` is 1 when a rising value is good (traffic, TOP-10
    count) and -1 when a falling value is good (average position, once the
    caller has already inverted the *display* sign so "+" always reads as
    "better"). ``invert_delta_color`` flips green/red without flipping the
    arrow direction -- used for average position where the raw change is
    reported as "1..better" but a positive change already means improvement.
    """
    x0, y0, w, h = rect
    theme.rounded_panel(fig, rect, radius=0.018)

    pad_x = w * 0.10
    label_y = y0 + h - h * 0.16
    fig.text(x0 + pad_x, label_y, label, ha='left', va='center',
              fontsize=theme.SIZE['kpi_label'], color=PALETTE.text_secondary, fontweight='medium')

    value_y = y0 + h * 0.42
    fig.text(x0 + pad_x, value_y, f'{fmt_number(value)}{value_suffix}', ha='left', va='center',
              fontsize=theme.SIZE['kpi_value'], color=PALETTE.text_primary, fontweight='bold')

    if delta is not None:
        color = PALETTE.negative if invert_delta_color and delta > 0 else (
            PALETTE.positive if invert_delta_color and delta < 0 else delta_color(delta)
        )
        arrow = delta_arrow(-delta if invert_delta_color else delta)
        suffix = ' п.п.' if delta_is_percent else ''
        delta_text = f'{arrow} {fmt_signed(delta, suffix=suffix)}'
        delta_y = y0 + h * 0.14
        fig.text(x0 + pad_x, delta_y, delta_text, ha='left', va='center',
                  fontsize=theme.SIZE['kpi_delta'], color=color, fontweight='bold')

    if sparkline and len(sparkline) >= 2:
        spark_ax = fig.add_axes([x0 + w * 0.56, y0 + h * 0.20, w * 0.36, h * 0.26])
        spark_ax.set_zorder(5)
        clean = [v for v in sparkline if v is not None]
        xs = list(range(len(sparkline)))
        ys = [v if v is not None else math.nan for v in sparkline]
        # "Better" means the line trends the way the KPI's own delta already
        # says it does -- for invert_sparkline metrics (e.g. average
        # position) a numeric drop is the improvement, so compare with the
        # sign flipped to pick the same green/red as the delta above.
        trend = None if len(clean) < 2 else (clean[-1] - clean[0])
        if not trend:  # None or exactly 0 -- no direction to color as good/bad
            line_color = PALETTE.neutral
        else:
            improving = (trend < 0) if invert_sparkline else (trend > 0)
            line_color = PALETTE.positive if improving else PALETTE.negative
        spark_ax.plot(xs, ys, color=line_color, linewidth=2.2, solid_capstyle='round')
        spark_ax.fill_between(xs, ys, min(clean, default=0), color=line_color, alpha=0.12, linewidth=0)
        if invert_sparkline:
            spark_ax.invert_yaxis()
        spark_ax.axis('off')
        spark_ax.set_facecolor('none')


def section_title(fig, x, y, text, *, color=None):
    fig.text(x, y, text, ha='left', va='bottom', fontsize=theme.SIZE['section_title'],
              color=color or PALETTE.text_primary, fontweight='bold')


def page_header(fig, title: str, subtitle: str | None = None, *, y=0.965):
    fig.text(0.055, y, title, ha='left', va='top', fontsize=21,
              color=PALETTE.text_primary, fontweight='bold')
    if subtitle:
        fig.text(0.055, y - 0.032, subtitle, ha='left', va='top', fontsize=theme.SIZE['chart_subtitle'],
                  color=PALETTE.text_secondary)


def footer_note(fig, text: str, *, y=0.014):
    fig.text(0.055, y, text, ha='left', va='bottom', fontsize=theme.SIZE['footer'], color=PALETTE.text_muted)


def callout_box(fig, rect, *, title: str, keyword: str, before, after, change, accent: str):
    """The "leader of growth" / "biggest drop" boxes used on dashboards."""
    x0, y0, w, h = rect
    theme.rounded_panel(fig, rect, radius=0.018, edgecolor=PALETTE.card_border)
    pad = w * 0.06
    marker_y = y0 + h - h * 0.22
    fig.add_artist(plt.Circle((x0 + pad * 0.35, marker_y), 0.007, transform=fig.transFigure,
                               color=accent, zorder=5))
    fig.text(x0 + pad * 0.35 + 0.016, marker_y, title, ha='left', va='center',
              fontsize=theme.SIZE['kpi_label'], color=PALETTE.text_secondary, fontweight='medium')
    max_chars = 19
    short_keyword = keyword if len(keyword) <= max_chars else keyword[:max_chars - 1] + '…'
    fig.text(x0 + pad, y0 + h * 0.56, short_keyword, ha='left', va='center',
              fontsize=13, color=PALETTE.text_primary, fontweight='bold')
    before_text = '—' if before is None else fmt_number(before)
    after_text = '—' if after is None else fmt_number(after)
    fig.text(x0 + pad, y0 + h * 0.20, f'{before_text} → {after_text}   {fmt_signed(change)}',
              ha='left', va='center', fontsize=12.5, color=accent, fontweight='bold')


def empty_state(ax, message: str):
    ax.axis('off')
    ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=theme.SIZE['chart_subtitle'],
            color=PALETTE.text_muted, transform=ax.transAxes)
