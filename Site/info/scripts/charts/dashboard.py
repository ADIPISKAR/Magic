"""Composite dashboards: the main "one image, not a text wall" screens.

Each function takes a plain ``context`` dict assembled by
``seo_dashboard.py`` from the existing data-access helpers (no DB access
happens in this module) and renders one Telegram-ready PNG.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Sequence

from . import theme
from .cards import callout_box, empty_state, footer_note, kpi_tile
from .positions import (
    _DISTRIBUTION_BUCKETS, _dates_values, _endpoint_labels, _has_data,
    _latest_distribution_row, _line_with_fill, _style_time_axis,
)
from .theme import PALETTE, Size, fmt_date_ru, fmt_number, fmt_signed


def _period_change(series: Sequence[dict], field: str) -> float | None:
    known = [row[field] for row in series if row.get(field) is not None]
    if len(known) < 2:
        return None
    return known[-1] - known[0]


def _rate(reaches, visits):
    if not visits:
        return None
    return round((reaches or 0) / visits * 100, 2)


def _mini_line(fig, rect, dates, values, *, color, fill_color, invert=False, title=None):
    axis = theme.panel_axes(fig, rect, inset=(0.07, 0.05, 0.13, 0.17 if title else 0.08))
    if title:
        fig.text(rect[0] + rect[2] * 0.06, rect[1] + rect[3] * 0.90, title, ha='left', va='center',
                  fontsize=theme.SIZE['section_title'], color=PALETTE.text_primary, fontweight='bold')
    theme.hide_axes_chrome(axis)
    if not _has_data(values):
        empty_state(axis, 'Недостаточно данных')
        return axis
    theme.style_grid(axis)
    if invert:
        axis.invert_yaxis()
    _line_with_fill(axis, dates, values, color=color, fill_color=fill_color, invert=invert)
    _endpoint_labels(axis, dates, values, color=color, invert=invert)
    _style_time_axis(axis, dates)
    return axis


def _distribution_mini(fig, rect, distribution_series, *, title='Распределение по TOP'):
    axis = theme.panel_axes(fig, rect, inset=(0.28, 0.08, 0.10, 0.20))
    fig.text(rect[0] + rect[2] * 0.055, rect[1] + rect[3] * 0.90, title, ha='left', va='center',
              fontsize=theme.SIZE['section_title'], color=PALETTE.text_primary, fontweight='bold')
    theme.hide_axes_chrome(axis)
    row = _latest_distribution_row(distribution_series)
    if row is None:
        empty_state(axis, 'Недостаточно данных')
        return
    buckets = _DISTRIBUTION_BUCKETS
    labels = [label for _, label, _ in buckets]
    values = [row.get(key) or 0 for key, _, _ in buckets]
    colors = [color for _, _, color in buckets]
    y_positions = list(range(len(labels)))[::-1]
    max_value = max(values) if max(values) else 1
    axis.barh(y_positions, values, color=colors, height=0.55, zorder=3)
    axis.set_yticks(y_positions)
    axis.set_yticklabels(labels, fontsize=10)
    axis.set_xlim(0, max_value * 1.22)
    axis.set_xticks([])
    for y, value in zip(y_positions, values):
        axis.text(value + max_value * 0.03, y, fmt_number(value), va='center', ha='left',
                   fontsize=10.5, color=PALETTE.text_primary, fontweight='bold')


def _movers_row(fig, rect, best_growth, worst_drop):
    half = rect[2] / 2 - 0.012
    growth = (best_growth or [None])[0]
    drop = (worst_drop or [None])[0]
    if growth:
        callout_box(fig, (rect[0], rect[1], half, rect[3]), title='Лидер роста', keyword=growth['keyword'],
                    before=growth['before'], after=growth['current'], change=growth['change'],
                    accent=PALETTE.positive)
    else:
        theme.rounded_panel(fig, (rect[0], rect[1], half, rect[3]), radius=0.018)
        fig.text(rect[0] + half * 0.5, rect[1] + rect[3] * 0.5, 'Нет роста за период', ha='center', va='center',
                  fontsize=11, color=PALETTE.text_muted)
    x1 = rect[0] + rect[2] / 2 + 0.012
    if drop:
        callout_box(fig, (x1, rect[1], half, rect[3]), title='Сильное падение', keyword=drop['keyword'],
                    before=drop['before'], after=drop['current'], change=drop['change'], accent=PALETTE.negative)
    else:
        theme.rounded_panel(fig, (x1, rect[1], half, rect[3]), radius=0.018)
        fig.text(x1 + half * 0.5, rect[1] + rect[3] * 0.5, 'Нет падений за период', ha='center', va='center',
                  fontsize=11, color=PALETTE.text_muted)


def _kpi_grid(fig, rect, tiles: Sequence[dict], *, columns: int = 2):
    rows = math.ceil(len(tiles) / columns)
    gap = 0.018
    tile_w = (rect[2] - gap * (columns - 1)) / columns
    tile_h = (rect[3] - gap * (rows - 1)) / rows
    for index, tile in enumerate(tiles):
        row, col = divmod(index, columns)
        x = rect[0] + col * (tile_w + gap)
        y = rect[1] + rect[3] - tile_h - row * (tile_h + gap)
        kpi_tile(fig, (x, y, tile_w, tile_h), **tile)


def _header(fig, title: str, subtitle: str):
    # Space the subtitle from the title in *inches* (via the figure height),
    # not a fixed figure-fraction gap -- a 22pt title eats a much bigger
    # fraction of a short (COMPACT) figure than a tall (DASHBOARD) one.
    height_in = fig.get_size_inches()[1]
    gap = 0.30 / height_in
    fig.text(0.055, 0.975, title, ha='left', va='top', fontsize=22, color=PALETTE.text_primary,
              fontweight='bold')
    fig.text(0.055, 0.975 - gap, subtitle, ha='left', va='top', fontsize=theme.SIZE['chart_subtitle'],
              color=PALETTE.text_secondary)


def _range_label(days: int, anchor: dt.date) -> str:
    start = anchor - dt.timedelta(days=max(days - 1, 0))
    return f'{fmt_date_ru(start.isoformat())} – {fmt_date_ru(anchor.isoformat())} · {days} дней'


def _position_tiles(context: dict) -> list[dict]:
    positions = context['positions']
    metrika = context.get('metrika') or {}
    metrika_prev = context.get('metrika_prev') or {}
    series = context['position_series']
    top10_delta = _period_change(series, 'top10')
    visits, visits_prev = metrika.get('visits'), metrika_prev.get('visits')
    visits_delta_pct = None
    if visits is not None and visits_prev:
        visits_delta_pct = round((visits - visits_prev) / visits_prev * 100, 1)
    reaches, reaches_prev = metrika.get('goal_reaches'), metrika_prev.get('goal_reaches')
    reaches_delta_pct = None
    if reaches is not None and reaches_prev:
        reaches_delta_pct = round((reaches - reaches_prev) / reaches_prev * 100, 1)
    return [
        dict(label='Средняя позиция', value=positions.get('average_position'),
             delta=positions.get('average_change'), sparkline=[r.get('average_position') for r in series],
             invert_sparkline=True),
        dict(label='TOP-10', value=positions.get('top10'), delta=top10_delta,
             sparkline=[r.get('top10') for r in series]),
        dict(label='Органический трафик', value=visits, delta=visits_delta_pct, delta_is_percent=False),
        dict(label='Заявки', value=reaches, delta=reaches_delta_pct, delta_is_percent=False),
    ]


def dashboard_7d(context: dict, path: Path, *, size=Size.DASHBOARD) -> Path:
    """Render the single-image dashboard. Despite the name (kept for the
    existing 7-day call sites), this is generic over ``context['days']`` --
    it is also reused for the 3-day period button.
    """
    positions = context['positions']
    anchor = dt.date.fromisoformat(context['anchor_date'])
    days = context.get('days', 7)
    fig = theme.figure(size)
    _header(fig, 'SEO DASHBOARD', _range_label(days, anchor))

    tiles = _position_tiles(context)
    for tile, value_suffix in zip(tiles, ('', '', '', '')):
        tile['value_suffix'] = value_suffix
    tiles[0]['sparkline'] = None  # avg position sparkline handled by the big chart below instead
    _kpi_grid(fig, (0.055, 0.715, 0.89, 0.175), tiles, columns=2)

    _mini_line(
        fig, (0.055, 0.46, 0.89, 0.235),
        *_dates_values(context['position_series'], 'average_position'),
        color=PALETTE.brand, fill_color=PALETTE.brand_soft, invert=True,
        title='Динамика средней позиции',
    )
    _distribution_mini(fig, (0.055, 0.265, 0.89, 0.165), context['distribution_series'])
    _movers_row(fig, (0.055, 0.075, 0.89, 0.165), positions.get('best_growth'), positions.get('worst_drop'))

    footer_note(fig, f"Обновлено: {context.get('generated_at', '—')} · Topvisor · Webmaster · Metrika")
    theme.save(fig, path)
    return Path(path)


def dashboard_30d_part1(context: dict, path: Path, *, size=Size.DASHBOARD) -> Path:
    positions = context['positions']
    anchor = dt.date.fromisoformat(context['anchor_date'])
    fig = theme.figure(size)
    _header(fig, 'SEO DASHBOARD · 30 дней', _range_label(30, anchor) + '  ·  1/2')

    metrika = context.get('metrika') or {}
    metrika_prev = context.get('metrika_prev') or {}
    conv_now = _rate(metrika.get('goal_reaches'), metrika.get('visits'))
    conv_prev = _rate(metrika_prev.get('goal_reaches'), metrika_prev.get('visits'))
    conv_delta = None if conv_now is None or conv_prev is None else round(conv_now - conv_prev, 2)
    dist_row = _latest_distribution_row(context['distribution_series']) or {}

    tiles = [
        dict(label='Средняя позиция', value=positions.get('average_position'),
             delta=positions.get('average_change')),
        dict(label='TOP-3', value=dist_row.get('top3')),
        dict(label='TOP-10', value=dist_row.get('top10'), delta=_period_change(context['position_series'], 'top10')),
        dict(label='TOP-20', value=dist_row.get('top20')),
        dict(label='Органический трафик', value=metrika.get('visits')),
        dict(label='Заявки', value=metrika.get('goal_reaches')),
        dict(label='Конверсия', value=conv_now, value_suffix='%', delta=conv_delta, delta_is_percent=True),
    ]
    _kpi_grid(fig, (0.055, 0.63, 0.89, 0.29), tiles, columns=3)

    _mini_line(
        fig, (0.055, 0.345, 0.89, 0.255),
        *_dates_values(context['position_series'], 'average_position'),
        color=PALETTE.brand, fill_color=PALETTE.brand_soft, invert=True,
        title='Динамика средней позиции',
    )
    trend = metrika.get('trend') or []
    traffic_dates = [dt.date.fromisoformat(row['date']) for row in trend]
    traffic_values = [math.nan if row.get('visits') is None else row['visits'] for row in trend]
    _mini_line(
        fig, (0.055, 0.075, 0.89, 0.245), traffic_dates, traffic_values,
        color=PALETTE.positive, fill_color=PALETTE.positive_soft,
        title='Органический трафик',
    )

    footer_note(fig, f"Обновлено: {context.get('generated_at', '—')} · Topvisor · Webmaster · Metrika")
    theme.save(fig, path)
    return Path(path)


def dashboard_30d_part2(context: dict, path: Path, *, size=Size.DASHBOARD) -> Path:
    positions = context['positions']
    anchor = dt.date.fromisoformat(context['anchor_date'])
    fig = theme.figure(size)
    _header(fig, 'SEO DASHBOARD · 30 дней', _range_label(30, anchor) + '  ·  2/2')

    _distribution_mini(fig, (0.055, 0.735, 0.89, 0.185), context['distribution_series'])
    _movers_row(fig, (0.055, 0.545, 0.89, 0.165), positions.get('best_growth'), positions.get('worst_drop'))

    wordstat_points = context.get('wordstat_points') or []
    panel_rect = (0.055, 0.075, 0.89, 0.435)
    axis = theme.panel_axes(fig, panel_rect, inset=(0.09, 0.06, 0.18, 0.14))
    fig.text(panel_rect[0] + panel_rect[2] * 0.055, panel_rect[1] + panel_rect[3] * 0.90,
              'Частотность (Wordstat)', ha='left', va='center',
              fontsize=theme.SIZE['section_title'], color=PALETTE.text_primary, fontweight='bold')
    theme.hide_axes_chrome(axis)
    values = [p['value'] for p in wordstat_points if p.get('value') is not None]
    if len(values) >= 2:
        xs = list(range(len(wordstat_points)))
        theme.style_grid(axis)
        axis.plot(xs, [p.get('value') for p in wordstat_points], color=PALETTE.brand, linewidth=2.4,
                   marker='o', markersize=5.5, markerfacecolor='white', markeredgecolor=PALETTE.brand, zorder=3)
        axis.fill_between(xs, [p.get('value') or 0 for p in wordstat_points], min(values),
                           color=PALETTE.brand_soft, alpha=0.3, linewidth=0, zorder=2)
        axis.set_xticks(xs)
        axis.set_xticklabels([p['label'] for p in wordstat_points], fontsize=theme.SIZE['axis_tick'])
        axis.set_ylim(bottom=min(values) * 0.85)
    elif values:
        axis.axis('off')
        axis.text(0.5, 0.55, fmt_number(values[0]), ha='center', va='center', fontsize=40,
                   color=PALETTE.text_primary, fontweight='bold', transform=axis.transAxes)
        axis.text(0.5, 0.25, 'суммарная частотность ядра · снимок Wordstat', ha='center', va='center',
                   fontsize=theme.SIZE['chart_subtitle'], color=PALETTE.text_secondary, transform=axis.transAxes)
    else:
        empty_state(axis, 'История Wordstat пока не накоплена')

    footer_note(fig, f"Обновлено: {context.get('generated_at', '—')} · Topvisor · Webmaster · Metrika")
    theme.save(fig, path)
    return Path(path)


def daily_card(context: dict, path: Path, *, size=Size.COMPACT) -> Path:
    positions = context['positions']
    metrika = context.get('metrika') or {}
    series = context['position_series']
    fig = theme.figure(size)
    _header(fig, 'SEO TODAY', dt.date.fromisoformat(context['anchor_date']).strftime('%d.%m.%Y'))

    tiles = [
        dict(label='Средняя позиция', value=positions.get('average_position'),
             delta=positions.get('average_change'), sparkline=[r.get('average_position') for r in series],
             invert_sparkline=True),
        dict(label='TOP-10', value=positions.get('top10'), delta=_period_change(series, 'top10'),
             sparkline=[r.get('top10') for r in series]),
        dict(label='Органика', value=metrika.get('visits')),
        dict(label='Заявки', value=metrika.get('goal_reaches')),
    ]
    _kpi_grid(fig, (0.06, 0.155, 0.88, 0.75), tiles, columns=2)
    footer_note(fig, f"Обновлено: {context.get('generated_at', '—')}")
    theme.save(fig, path)
    return Path(path)


def weekly_report_images(context: dict, out_dir: Path, *, version: str) -> list[Path]:
    """The image set attached to the weekly Telegram report: dashboard + 2 charts."""
    out_dir = Path(out_dir)
    dash = out_dir / f'weekly-dashboard-{version}.png'
    positions_chart = out_dir / f'weekly-positions-{version}.png'
    traffic_chart_path = out_dir / f'weekly-traffic-{version}.png'

    dashboard_7d(context, dash)

    fig = theme.figure(Size.WIDE)
    fig.text(0.055, 0.93, 'Динамика средней позиции · 7 дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')
    _mini_line(fig, (0.045, 0.045, 0.91, 0.80), *_dates_values(context['position_series'], 'average_position'),
               color=PALETTE.brand, fill_color=PALETTE.brand_soft, invert=True)
    theme.save(fig, positions_chart)

    trend = (context.get('metrika') or {}).get('trend') or []
    fig = theme.figure(Size.WIDE)
    fig.text(0.055, 0.93, 'Органический трафик · 7 дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')
    _mini_line(fig, (0.045, 0.045, 0.91, 0.80),
               [dt.date.fromisoformat(r['date']) for r in trend],
               [math.nan if r.get('visits') is None else r['visits'] for r in trend],
               color=PALETTE.positive, fill_color=PALETTE.positive_soft)
    theme.save(fig, traffic_chart_path)

    return [dash, positions_chart, traffic_chart_path]
