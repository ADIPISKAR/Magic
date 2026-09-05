"""Keyword frequency (Wordstat) chart.

Note on data availability: the current pipeline stores only the latest
Topvisor frequency snapshot per keyword (``seo_keywords.frequency`` +
``frequency_checked_at``) -- there is no monthly frequency history table
yet. This module renders whatever points it is given: a real multi-point
trend once that history starts accumulating, or an honest "single
snapshot" card today, rather than inventing months of data that were
never measured.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from . import theme
from .cards import empty_state, footer_note
from .positions import _has_data, _line_with_fill, _style_time_axis
from .theme import PALETTE, Size, fmt_number, fmt_signed


def wordstat_chart(keyword: str, points: Sequence[dict], path: Path, *, size=Size.WIDE) -> Path:
    """``points``: [{'label': '2026-08', 'value': 1540}, ...] oldest -> newest."""
    fig = theme.figure(size)
    fig.text(0.055, 0.94, keyword, ha='left', va='center', fontsize=theme.SIZE['chart_title'],
              color=PALETTE.text_primary, fontweight='bold')

    values = [p['value'] for p in points if p.get('value') is not None]
    axis = theme.panel_axes(fig, (0.045, 0.045, 0.91, 0.77), inset=(0.09, 0.06, 0.16, 0.18))
    theme.hide_axes_chrome(axis)

    if len(values) >= 2:
        labels = [p['label'] for p in points]
        xs = list(range(len(points)))
        theme.style_grid(axis)
        line, = axis.plot(xs, [p.get('value') for p in points], color=PALETTE.brand, linewidth=2.6,
                           marker='o', markersize=6, markerfacecolor=PALETTE.marker_face,
                           markeredgecolor=PALETTE.brand, markeredgewidth=1.6, zorder=3)
        axis.fill_between(xs, [p.get('value') or 0 for p in points], min(values),
                           color=PALETTE.brand_soft, alpha=0.35, linewidth=0, zorder=2)
        axis.set_xticks(xs)
        axis.set_xticklabels(labels, fontsize=theme.SIZE['axis_tick'])
        axis.set_ylim(bottom=min(values) * 0.85)
        axis.tick_params(axis='y', labelsize=theme.SIZE['axis_tick'], length=0)
        current, previous = values[-1], values[-2]
        change_pct = None if previous == 0 else round((current - previous) / previous * 100, 1)
        headline = f'{fmt_number(current)} запросов'
        sub = '' if change_pct is None else f'  ·  {fmt_signed(change_pct, suffix="%")} к прошлому периоду'
        fig.text(0.055, 0.895, headline + sub, ha='left', va='center',
                  fontsize=theme.SIZE['chart_subtitle'], color=PALETTE.text_secondary)
    elif len(values) == 1:
        empty_state(axis, '')
        axis.text(0.5, 0.62, fmt_number(values[0]), ha='center', va='center', fontsize=44,
                   color=PALETTE.text_primary, fontweight='bold', transform=axis.transAxes)
        axis.text(0.5, 0.38, 'запросов в месяц · текущий снимок Wordstat', ha='center', va='center',
                   fontsize=theme.SIZE['chart_subtitle'], color=PALETTE.text_secondary, transform=axis.transAxes)
        axis.text(0.5, 0.20, 'История по месяцам ещё не накоплена', ha='center', va='center',
                   fontsize=10.5, color=PALETTE.text_muted, transform=axis.transAxes)
    else:
        empty_state(axis, 'Частотность пока не получена')

    footer_note(fig, 'Источник: Topvisor (снимок частотности)')
    theme.save(fig, path)
    return Path(path)
