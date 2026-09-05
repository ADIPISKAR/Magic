"""Position charts: average position, TOP-10 dynamics, distribution, movers.

All functions take the exact data shapes already produced by
``seo_dashboard.position_series`` / ``position_distribution_series`` /
``build_summary`` -- no re-shaping is needed at the call site.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from . import theme
from .cards import empty_state, footer_note
from .theme import PALETTE, Size, fmt_date_ru, fmt_number, fmt_signed


def _dates_values(series: Sequence[dict], field: str):
    dates = [dt.date.fromisoformat(row['date']) for row in series]
    values = [math.nan if row.get(field) is None else row[field] for row in series]
    return dates, values


def _has_data(values) -> bool:
    return any(v == v for v in values)  # NaN != NaN


def _style_time_axis(axis, dates: Sequence[dt.date]):
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    span_days = max((dates[-1] - dates[0]).days, 1) if len(dates) > 1 else 1
    max_ticks = 6 if span_days <= 10 else 8
    axis.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=2, maxticks=max_ticks))
    axis.tick_params(axis='x', labelsize=theme.SIZE['axis_tick'], length=0)
    axis.tick_params(axis='y', labelsize=theme.SIZE['axis_tick'], length=0)


def _line_with_fill(axis, dates, values, *, color, fill_color, invert=False):
    line, = axis.plot(dates, values, color=color, linewidth=2.6, marker='o', markersize=5.5,
                       markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.6, zorder=3)
    baseline = min((v for v in values if v == v), default=0)
    axis.fill_between(dates, values, baseline, color=fill_color, alpha=0.35, linewidth=0, zorder=2)
    return line


def _endpoint_labels(axis, dates, values, *, color, value_fmt=None, invert=False):
    value_fmt = value_fmt or (lambda v: fmt_number(round(v, 1) if v % 1 else int(v)))
    points = [(d, v) for d, v in zip(dates, values) if v == v]
    if not points:
        return
    first_d, first_v = points[0]
    last_d, last_v = points[-1]
    # Offset labels diagonally away from the endpoints (up-left / up-right)
    # so they clear the line stroke regardless of local slope or axis
    # inversion, and pad the x-range so the last label never clips.
    span = (dates[-1] - dates[0]).days or 1
    axis.set_xlim(dates[0] - dt.timedelta(days=span * 0.05), dates[-1] + dt.timedelta(days=span * 0.14))
    axis.annotate(value_fmt(first_v), (first_d, first_v), textcoords='offset points',
                  xytext=(-2, 12), ha='left', va='bottom', fontsize=theme.SIZE['annotation'],
                  color=PALETTE.text_secondary, fontweight='bold', clip_on=False)
    if last_d != first_d:
        axis.annotate(value_fmt(last_v), (last_d, last_v), textcoords='offset points',
                      xytext=(8, 0), ha='left', va='center', fontsize=theme.SIZE['annotation'] + 1,
                      color=color, fontweight='bold', clip_on=False)


def average_position_chart(series: Sequence[dict], days: int, path: Path, *, size=Size.WIDE) -> Path:
    """Line chart of the average Topvisor position. Up on the chart = better.

    Position 1 is the best possible rank, so the axis is inverted and the
    raw values are unchanged -- moving from 20 to 10 draws as a rising line.
    """
    dates, values = _dates_values(series, 'average_position')
    fig = theme.figure(size)
    fig.text(0.055, 0.93, f'Средняя позиция Topvisor · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')

    axis = theme.panel_axes(fig, (0.045, 0.06, 0.91, 0.78), inset=(0.06, 0.05, 0.14, 0.12))
    if not _has_data(values):
        empty_state(axis, 'Недостаточно данных за период')
        theme.save(fig, path)
        return Path(path)

    theme.style_grid(axis)
    theme.hide_axes_chrome(axis)
    axis.invert_yaxis()
    _line_with_fill(axis, dates, values, color=PALETTE.brand, fill_color=PALETTE.brand_soft, invert=True)
    _endpoint_labels(axis, dates, values, color=PALETTE.brand_dark, invert=True)
    _style_time_axis(axis, dates)
    axis.set_ylabel('Позиция (1 — лучшая)', fontsize=theme.SIZE['axis_label'])

    known = [v for v in values if v == v]
    if len(known) >= 2:
        change = known[0] - known[-1]  # positive change == improvement (lower position number)
        color = PALETTE.positive if change > 0 else (PALETTE.negative if change < 0 else PALETTE.neutral)
        arrow = '↑' if change > 0 else ('↓' if change < 0 else '•')
        fig.text(0.945, 0.93, f'{arrow} {fmt_signed(abs(change))}', ha='right', va='center',
                  fontsize=theme.SIZE['chart_title'] - 2, color=color, fontweight='bold')
    footer_note(fig, 'Источник: Topvisor · чем выше линия, тем лучше позиции')
    theme.save(fig, path)
    return Path(path)


def top10_dynamics_chart(series: Sequence[dict], days: int, path: Path, *, size=Size.WIDE) -> Path:
    """Line/area chart: how many target keywords are ranked in the TOP-10."""
    dates, values = _dates_values(series, 'top10')
    fig = theme.figure(size)
    fig.text(0.055, 0.94, f'Запросы в TOP-10 · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')

    axis = theme.panel_axes(fig, (0.045, 0.045, 0.91, 0.77), inset=(0.06, 0.05, 0.14, 0.12))
    if not _has_data(values):
        fig.text(0.055, 0.895, ' ', fontsize=1)
        empty_state(axis, 'Недостаточно данных за период')
        theme.save(fig, path)
        return Path(path)

    theme.style_grid(axis)
    theme.hide_axes_chrome(axis)
    _line_with_fill(axis, dates, values, color=PALETTE.positive, fill_color=PALETTE.positive_soft)
    axis.set_ylim(bottom=0)
    axis.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    _endpoint_labels(axis, dates, values, color=PALETTE.positive)
    _style_time_axis(axis, dates)
    axis.set_ylabel('Количество запросов', fontsize=theme.SIZE['axis_label'])

    known = [v for v in values if v == v]
    if known:
        current, maximum = known[-1], max(known)
        change = current - known[0] if len(known) >= 2 else None
        pieces = [f'Сейчас: {fmt_number(current)}', f'Максимум периода: {fmt_number(maximum)}']
        if change is not None:
            pieces.insert(1, f'Изменение: {fmt_signed(change)}')
        fig.text(0.055, 0.895, '   ·   '.join(pieces), ha='left', va='center',
                  fontsize=theme.SIZE['chart_subtitle'], color=PALETTE.text_secondary)
    footer_note(fig, 'Источник: Topvisor')
    theme.save(fig, path)
    return Path(path)


_DISTRIBUTION_BUCKETS = (
    ('top3', 'TOP-3', PALETTE.top3),
    ('top10', 'TOP-10', PALETTE.top10),
    ('top20', 'TOP-20', PALETTE.top20),
    ('top50', 'TOP-50', PALETTE.top50),
    ('not_found', 'Вне TOP-100', PALETTE.not_found),
)


def _latest_distribution_row(distribution_series: Sequence[dict]) -> dict | None:
    for row in reversed(distribution_series):
        if any(row.get(key) is not None for key, _, _ in _DISTRIBUTION_BUCKETS):
            return row
    return None


def distribution_chart(distribution_series: Sequence[dict], days: int, path: Path, *, size=Size.WIDE) -> Path:
    """Horizontal bar chart of how the semantic core splits across TOP bands."""
    row = _latest_distribution_row(distribution_series)
    fig = theme.figure(size)
    fig.text(0.055, 0.93, f'Распределение по TOP · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')
    axis = theme.panel_axes(fig, (0.045, 0.06, 0.91, 0.78), inset=(0.19, 0.08, 0.10, 0.10))
    if row is None:
        empty_state(axis, 'Недостаточно данных за период')
        theme.save(fig, path)
        return Path(path)

    theme.hide_axes_chrome(axis)
    labels = [label for _, label, _ in _DISTRIBUTION_BUCKETS]
    values = [row.get(key) or 0 for key, _, _ in _DISTRIBUTION_BUCKETS]
    colors = [color for _, _, color in _DISTRIBUTION_BUCKETS]
    y_positions = list(range(len(labels)))[::-1]
    max_value = max(values) if max(values) else 1
    axis.barh(y_positions, values, color=colors, height=0.58, zorder=3)
    axis.set_yticks(y_positions)
    axis.set_yticklabels(labels, fontsize=theme.SIZE['axis_tick'])
    axis.set_xlim(0, max_value * 1.18)
    axis.set_xticks([])
    for y, value in zip(y_positions, values):
        axis.text(value + max_value * 0.02, y, fmt_number(value), va='center', ha='left',
                   fontsize=12.5, color=PALETTE.text_primary, fontweight='bold')
    footer_note(fig, 'Источник: Topvisor · срез на последний день периода')
    theme.save(fig, path)
    return Path(path)


def growth_drop_chart(best_growth: Sequence[dict], worst_drop: Sequence[dict], days: int, path: Path,
                       *, size=Size.WIDE_TALL, limit: int = 5) -> Path:
    """Two horizontal-bar panels: biggest gains (green) and drops (red)."""
    growth = list(best_growth)[:limit]
    drop = list(worst_drop)[:limit]
    fig = theme.figure(size)
    fig.text(0.055, 0.955, f'Рост и падение запросов · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')

    def panel(rect, rows, *, title, color, is_growth):
        axis = theme.panel_axes(fig, rect, inset=(0.34, 0.08, 0.09, 0.16))
        marker_x = rect[0] + rect[2] * 0.055
        marker_y = rect[1] + rect[3] * 0.905
        fig.add_artist(plt.Circle((marker_x, marker_y), 0.008, transform=fig.transFigure,
                                   color=color, zorder=5))
        fig.text(marker_x + 0.018, rect[1] + rect[3] * 0.90, title,
                  ha='left', va='center', fontsize=theme.SIZE['section_title'],
                  color=PALETTE.text_primary, fontweight='bold')
        theme.hide_axes_chrome(axis)
        if not rows:
            empty_state(axis, 'Нет сопоставимых изменений')
            return
        labels = [row['keyword'][:22] + ('…' if len(row['keyword']) > 22 else '') for row in rows][::-1]
        changes = [abs(row['change']) for row in rows][::-1]
        raw = [row['change'] for row in rows][::-1]
        y_positions = list(range(len(labels)))
        max_value = max(changes) if changes else 1
        axis.barh(y_positions, changes, color=color, height=0.5, zorder=3)
        axis.set_yticks(y_positions)
        axis.set_yticklabels(labels, fontsize=10.5)
        axis.set_xlim(0, max_value * 1.35)
        axis.set_xticks([])
        for y, value in zip(y_positions, raw):
            axis.text(abs(value) + max_value * 0.03, y, fmt_signed(value), va='center', ha='left',
                       fontsize=10.5, color=color, fontweight='bold')

    panel((0.045, 0.51, 0.91, 0.40), growth, title='Рост', color=PALETTE.positive, is_growth=True)
    panel((0.045, 0.06, 0.91, 0.40), drop, title='Падение', color=PALETTE.negative, is_growth=False)
    footer_note(fig, 'Источник: Topvisor · изменение позиции за период')
    theme.save(fig, path)
    return Path(path)


def keyword_card(history: dict, series: Sequence[dict], path: Path, *, size=Size.CARD) -> Path:
    """One keyword's full picture: current rank, URL, 30-day history, extremes."""
    fig = theme.figure(size)
    current = history.get('current') or {}
    periods = history.get('periods') or {}
    keyword = history.get('keyword', '')

    fig.text(0.06, 0.955, keyword, ha='left', va='top', fontsize=19, color=PALETTE.text_primary,
              fontweight='bold', wrap=True)

    position = current.get('position') if current.get('status') == 'found' else None
    change7 = (periods.get(7) or periods.get('7') or {}).get('change') if isinstance(periods, dict) else None
    change30 = (periods.get(30) or periods.get('30') or {}).get('change') if isinstance(periods, dict) else None

    top_row_y = 0.83
    fig.text(0.06, top_row_y, 'Текущая позиция', fontsize=theme.SIZE['kpi_label'], color=PALETTE.text_secondary)
    fig.text(0.06, top_row_y - 0.085, fmt_number(position) if position else 'не найдено', fontsize=36,
              color=PALETTE.text_primary, fontweight='bold')
    if change7 is not None:
        color = PALETTE.positive if change7 > 0 else (PALETTE.negative if change7 < 0 else PALETTE.neutral)
        arrow = '↑' if change7 > 0 else ('↓' if change7 < 0 else '•')
        fig.text(0.06, top_row_y - 0.155, f'{arrow} {fmt_signed(change7)} за 7 дней', fontsize=13,
                  color=color, fontweight='bold')

    found_url = current.get('found_url')
    if found_url:
        fig.text(0.06, top_row_y - 0.205, f'URL: {found_url}', fontsize=11, color=PALETTE.text_secondary)

    dates, values = _dates_values(series, 'position')
    axis = theme.panel_axes(fig, (0.045, 0.275, 0.91, 0.335), inset=(0.07, 0.06, 0.14, 0.12))
    if _has_data(values):
        theme.style_grid(axis)
        theme.hide_axes_chrome(axis)
        axis.invert_yaxis()
        _line_with_fill(axis, dates, values, color=PALETTE.brand, fill_color=PALETTE.brand_soft, invert=True)
        _endpoint_labels(axis, dates, values, color=PALETTE.brand_dark, invert=True)
        _style_time_axis(axis, dates)
    else:
        empty_state(axis, 'История за 30 дней пока не накоплена')

    known = [v for v in values if v == v]
    stats_y = 0.155
    stats = [
        ('Частотность', fmt_number(history.get('frequency')) if history.get('frequency') is not None else '—'),
        ('Лучшая', fmt_number(min(known)) if known else '—'),
        ('Худшая', fmt_number(max(known)) if known else '—'),
        ('Δ 30 дней', fmt_signed(change30) if change30 is not None else '—'),
    ]
    slot_w = 0.91 / len(stats)
    for index, (label, value) in enumerate(stats):
        x = 0.045 + slot_w * index + slot_w / 2
        fig.text(x, stats_y, label, ha='center', fontsize=10.5, color=PALETTE.text_secondary)
        fig.text(x, stats_y - 0.05, value, ha='center', fontsize=15, color=PALETTE.text_primary, fontweight='bold')

    footer_note(fig, 'Источник: Topvisor')
    theme.save(fig, path)
    return Path(path)
