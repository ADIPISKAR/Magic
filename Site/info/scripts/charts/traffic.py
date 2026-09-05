"""Yandex Metrika traffic + goal (conversion) charts.

Metrika in this project only collects organic sessions (see
``seo-settings.json`` -> ``analytics.metrika.filter``), so charts here show
organic visits/users rather than a fabricated "all traffic" series -- the
brief's "весь трафик + органика" pair isn't something the pipeline
actually gathers, and this layer never draws numbers nobody measured.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from . import theme
from .cards import empty_state, footer_note
from .positions import _dates_values, _endpoint_labels, _has_data, _line_with_fill, _style_time_axis
from .theme import PALETTE, Size, fmt_number, fmt_signed


def traffic_chart(trend: Sequence[dict], days: int, path: Path, *, size=Size.WIDE) -> Path:
    """Organic visits vs. users over time."""
    fig = theme.figure(size)
    fig.text(0.055, 0.94, f'Органический трафик · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')

    axis = theme.panel_axes(fig, (0.045, 0.045, 0.91, 0.77), inset=(0.07, 0.05, 0.14, 0.12))
    dates, visits = _dates_values(trend, 'visits')
    _, users = _dates_values(trend, 'users')
    if not _has_data(visits):
        empty_state(axis, 'Данных Яндекс Метрики за период нет')
        theme.save(fig, path)
        return Path(path)

    theme.style_grid(axis)
    theme.hide_axes_chrome(axis)
    visits_line = _line_with_fill(axis, dates, visits, color=PALETTE.brand, fill_color=PALETTE.brand_soft)
    handles, labels = [visits_line], ['Визиты (органика)']
    if _has_data(users):
        users_line, = axis.plot(dates, users, color=PALETTE.series[2], linewidth=2.2, marker='o', markersize=4.5,
                                 markerfacecolor='white', markeredgecolor=PALETTE.series[2], zorder=3)
        handles.append(users_line)
        labels.append('Пользователи')
    axis.set_ylim(bottom=0)
    _endpoint_labels(axis, dates, visits, color=PALETTE.brand_dark)
    _style_time_axis(axis, dates)
    axis.set_ylabel('Визиты', fontsize=theme.SIZE['axis_label'])
    axis.legend(handles, labels, loc='upper left', frameon=False,
                fontsize=theme.SIZE['legend'], bbox_to_anchor=(0.0, 1.16))
    footer_note(fig, 'Источник: Яндекс Метрика · только органический трафик')
    theme.save(fig, path)
    return Path(path)


def aggregate_goals(metrika_period: dict) -> list[dict]:
    totals: dict[tuple, dict] = {}
    for landing in metrika_period.get('landings') or []:
        for goal in landing.get('goals') or []:
            key = goal.get('goal_name') or goal.get('goal_id')
            entry = totals.setdefault(key, {'name': key, 'reaches': 0})
            entry['reaches'] += goal.get('reaches') or 0
    return sorted(totals.values(), key=lambda row: -row['reaches'])


def conversions_chart(metrika_period: dict, days: int, path: Path, *, size=Size.WIDE_TALL) -> Path:
    """Horizontal bars for each goal + a daily conversion-rate line below."""
    goals = aggregate_goals(metrika_period)
    trend = metrika_period.get('trend') or []
    fig = theme.figure(size)
    fig.text(0.055, 0.965, f'Конверсии · {days} дней', ha='left', va='center',
              fontsize=theme.SIZE['chart_title'], color=PALETTE.text_primary, fontweight='bold')

    top_axis = theme.panel_axes(fig, (0.045, 0.535, 0.91, 0.375), inset=(0.30, 0.10, 0.14, 0.18))
    fig.text(0.045 + 0.91 * 0.055, 0.535 + 0.375 * 0.87, 'Достижения целей', ha='left', va='center',
              fontsize=theme.SIZE['section_title'], color=PALETTE.text_primary, fontweight='bold')
    theme.hide_axes_chrome(top_axis)
    if not goals:
        empty_state(top_axis, 'Целей за период не зафиксировано')
    else:
        top_goals = goals[:5][::-1]
        labels = [g['name'][:24] + ('…' if len(g['name']) > 24 else '') for g in top_goals]
        values = [g['reaches'] for g in top_goals]
        y_positions = list(range(len(labels)))
        max_value = max(values) if values else 1
        top_axis.barh(y_positions, values, color=PALETTE.brand, height=0.5, zorder=3)
        top_axis.set_yticks(y_positions)
        top_axis.set_yticklabels(labels, fontsize=10.5)
        top_axis.set_xlim(0, max_value * 1.3)
        top_axis.set_xticks([])
        for y, value in zip(y_positions, values):
            top_axis.text(value + max_value * 0.03, y, fmt_number(value), va='center', ha='left',
                           fontsize=11, color=PALETTE.brand_dark, fontweight='bold')

    bottom_axis = theme.panel_axes(fig, (0.045, 0.06, 0.91, 0.42), inset=(0.07, 0.05, 0.14, 0.16))
    fig.text(0.045 + 0.91 * 0.055, 0.06 + 0.42 * 0.90, 'Конверсия по дням, %', ha='left', va='center',
              fontsize=theme.SIZE['section_title'], color=PALETTE.text_primary, fontweight='bold')
    dates = [dt.date.fromisoformat(row['date']) for row in trend]
    rates = []
    for row in trend:
        visits = row.get('visits')
        reaches = row.get('goal_reaches')
        rates.append(None if not visits else round((reaches or 0) / visits * 100, 2))
    values = [math.nan if v is None else v for v in rates]
    theme.hide_axes_chrome(bottom_axis)
    if not _has_data(values):
        empty_state(bottom_axis, 'Недостаточно данных за период')
    else:
        theme.style_grid(bottom_axis)
        _line_with_fill(bottom_axis, dates, values, color=PALETTE.positive, fill_color=PALETTE.positive_soft)
        _endpoint_labels(bottom_axis, dates, values, color=PALETTE.positive,
                          value_fmt=lambda v: f'{v:.1f}%')
        _style_time_axis(bottom_axis, dates)
    footer_note(fig, 'Источник: Яндекс Метрика · конверсии считаются по landing page, не по запросу')
    theme.save(fig, path)
    return Path(path)
