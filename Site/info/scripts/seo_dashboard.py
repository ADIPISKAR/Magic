"""Build the combined Topvisor → Webmaster → Metrika SEO dashboard."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sqlite3
import sys
import tempfile
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from seo_common import SeoError
from seo_positions import (
    build_summary,
    format_telegram_report,
    keyword_history,
    parse_time,
)
from seo_sources import AnalyticsStore, iso_time, load_source_config, normalize_query

from charts import cache as chart_cache
from charts import dashboard as chart_dashboard
from charts import positions as chart_positions
from charts import traffic as chart_traffic
from charts import wordstat as chart_wordstat


def _sum_known(values: Iterable[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return None if not known else sum(known)


def _average_known(values: Iterable[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return None if not known else round(sum(known) / len(known), 4)


def _weighted_position(rows: Sequence[dict], field: str) -> float | None:
    weighted = [
        (row[field], row['shows']) for row in rows
        if row.get(field) is not None and row.get('shows') not in (None, 0)
    ]
    if weighted:
        denominator = sum(weight for _, weight in weighted)
        return round(sum(value * weight for value, weight in weighted) / denominator, 4)
    return _average_known(row.get(field) for row in rows)


def _weighted_metric(
    rows: Sequence[dict], field: str, weight_field: str = 'visits',
) -> float | None:
    weighted = [
        (row.get(field), row.get(weight_field)) for row in rows
        if row.get(field) is not None and row.get(weight_field) not in (None, 0)
    ]
    if weighted:
        weight = sum(value for _, value in weighted)
        return round(sum(value * item_weight for value, item_weight in weighted) / weight, 4)
    return _average_known(row.get(field) for row in rows)


def _period_bounds(anchor: dt.date, days: int) -> tuple[str, str]:
    return (anchor - dt.timedelta(days=max(days - 1, 0))).isoformat(), anchor.isoformat()


def _dedupe_latest(rows: Sequence[sqlite3.Row], key_fields: Sequence[str]) -> list[dict]:
    result = {}
    for raw in sorted(rows, key=lambda row: (row['fetched_at'], row['id'])):
        row = dict(raw)
        result[tuple(row[field] for field in key_fields)] = row
    return list(result.values())


def source_statuses(store: AnalyticsStore) -> dict:
    with store.session() as connection:
        rows = connection.execute(
            """SELECT r.* FROM seo_source_runs r
               JOIN (
                   SELECT source, MAX(finished_at) AS finished_at
                   FROM seo_source_runs GROUP BY source
               ) latest ON latest.source = r.source AND latest.finished_at = r.finished_at
               ORDER BY r.run_id""",
        ).fetchall()
    return {row['source']: dict(row) for row in rows}


def webmaster_period(store: AnalyticsStore, anchor: dt.date, days: int) -> dict:
    date1, date2 = _period_bounds(anchor, days)
    with store.session() as connection:
        rows = connection.execute(
            """SELECT * FROM seo_webmaster_queries
               WHERE period_start >= ? AND period_end <= ?
               ORDER BY fetched_at, id""",
            (date1, date2),
        ).fetchall()
    rows = _dedupe_latest(rows, ('period_start', 'period_end', 'query_id', 'device'))
    grouped = defaultdict(list)
    for row in rows:
        grouped[normalize_query(row['query_text'])].append(row)
    queries = []
    for group in grouped.values():
        sample = group[-1]
        shows = _sum_known(row.get('shows') for row in group)
        clicks = _sum_known(row.get('clicks') for row in group)
        ctr = None if shows in (None, 0) or clicks is None else round(clicks / shows * 100, 4)
        queries.append({
            'query_id': sample['query_id'],
            'query_text': sample['query_text'],
            'shows': shows,
            'clicks': clicks,
            'ctr': ctr,
            'avg_show_position': _weighted_position(group, 'avg_show_position'),
            'avg_click_position': _weighted_position(group, 'avg_click_position'),
            'is_target': bool(sample['is_target']),
            'target_keyword_id': sample['target_keyword_id'],
        })
    queries.sort(key=lambda row: (-(row['shows'] if row['shows'] is not None else -1), row['query_text']))
    trend_groups = defaultdict(list)
    for row in rows:
        trend_groups[row['period_start']].append(row)
    trend = []
    for day, day_rows in sorted(trend_groups.items()):
        shows = _sum_known(row.get('shows') for row in day_rows)
        clicks = _sum_known(row.get('clicks') for row in day_rows)
        trend.append({
            'date': day,
            'shows': shows,
            'clicks': clicks,
            'ctr': None if shows in (None, 0) or clicks is None else round(clicks / shows * 100, 4),
            'avg_show_position': _weighted_position(day_rows, 'avg_show_position'),
            'avg_click_position': _weighted_position(day_rows, 'avg_click_position'),
        })
    return {
        'period_start': date1,
        'period_end': date2,
        'query_count': len(queries) if rows else None,
        'shows': _sum_known(row['shows'] for row in queries),
        'clicks': _sum_known(row['clicks'] for row in queries),
        'ctr': (
            None if _sum_known(row['shows'] for row in queries) in (None, 0)
            or _sum_known(row['clicks'] for row in queries) is None
            else round(
                _sum_known(row['clicks'] for row in queries)
                / _sum_known(row['shows'] for row in queries) * 100,
                4,
            )
        ),
        'queries': queries,
        'new_queries': [row for row in queries if not row['is_target']],
        'trend': trend,
    }


def _landing_path(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urllib.parse.urlsplit(value)
    path = parsed.path if parsed.scheme or parsed.netloc else value.split('?', 1)[0]
    path = '/' + path.lstrip('/')
    return path.rstrip('/') or '/'


def metrika_period(store: AnalyticsStore, anchor: dt.date, days: int) -> dict:
    date1, date2 = _period_bounds(anchor, days)
    with store.session() as connection:
        traffic_rows = connection.execute(
            """SELECT * FROM seo_metrika_landings
               WHERE period_start >= ? AND period_end <= ?
               ORDER BY fetched_at, id""",
            (date1, date2),
        ).fetchall()
        goal_rows = connection.execute(
            """SELECT * FROM seo_metrika_goals
               WHERE period_start >= ? AND period_end <= ?
               ORDER BY fetched_at, id""",
            (date1, date2),
        ).fetchall()
    traffic_rows = _dedupe_latest(
        traffic_rows, ('period_start', 'period_end', 'landing_page', 'search_engine'),
    )
    goal_rows = _dedupe_latest(
        goal_rows, ('period_start', 'period_end', 'landing_page', 'search_engine', 'goal_id'),
    )
    landings = defaultdict(list)
    for row in traffic_rows:
        path = _landing_path(row['landing_page'])
        if path:
            landings[path].append(row)
    goals_by_landing = defaultdict(list)
    for row in goal_rows:
        path = _landing_path(row['landing_page'])
        if path:
            goals_by_landing[path].append(row)
    items = []
    for path in sorted(set(landings) | set(goals_by_landing)):
        traffic = landings.get(path, [])
        goals_grouped = defaultdict(list)
        for row in goals_by_landing.get(path, []):
            goals_grouped[row['goal_id']].append(row)
        goal_items = []
        for goal_id, rows in goals_grouped.items():
            sample = rows[-1]
            reaches = _sum_known(row.get('reaches') for row in rows)
            visits = _sum_known(row.get('visits') for row in traffic)
            goal_items.append({
                'goal_id': goal_id,
                'goal_name': sample.get('goal_name'),
                'goal_type': sample.get('goal_type'),
                'reaches': reaches,
                'conversion_rate': (
                    None if visits in (None, 0) or reaches is None
                    else round(reaches / visits * 100, 4)
                ),
                'attribution_level': 'landing_page',
            })
        items.append({
            'landing_page': path,
            'visits': _sum_known(row.get('visits') for row in traffic),
            'users': _sum_known(row.get('users') for row in traffic),
            'bounce_rate': _average_known(row.get('bounce_rate') for row in traffic),
            'page_depth': _weighted_metric(traffic, 'page_depth'),
            'avg_visit_duration_seconds': _weighted_metric(
                traffic, 'avg_visit_duration_seconds',
            ),
            'goals': sorted(goal_items, key=lambda item: item['goal_id']),
        })
    items.sort(key=lambda row: (-(row['visits'] if row['visits'] is not None else -1), row['landing_page']))
    goal_reaches = _sum_known(
        goal['reaches'] for landing in items for goal in landing['goals']
    )
    messenger_reaches = _sum_known(
        goal['reaches'] for landing in items for goal in landing['goals']
        if (goal.get('goal_type') or '').casefold() == 'messenger'
    )
    trend_groups = defaultdict(list)
    for row in traffic_rows:
        trend_groups[row['period_start']].append(row)
    trend = []
    for day, day_rows in sorted(trend_groups.items()):
        day_goal_rows = [
            row for row in goal_rows if row['period_start'] == day
        ]
        trend.append({
            'date': day,
            'visits': _sum_known(row.get('visits') for row in day_rows),
            'users': _sum_known(row.get('users') for row in day_rows),
            'bounce_rate': _weighted_metric(day_rows, 'bounce_rate'),
            'page_depth': _weighted_metric(day_rows, 'page_depth'),
            'avg_visit_duration_seconds': _weighted_metric(
                day_rows, 'avg_visit_duration_seconds',
            ),
            'goal_reaches': _sum_known(row.get('reaches') for row in day_goal_rows),
        })
    return {
        'period_start': date1,
        'period_end': date2,
        'visits': _sum_known(item['visits'] for item in items),
        'users': _sum_known(item['users'] for item in items),
        'bounce_rate': _weighted_metric(items, 'bounce_rate'),
        'page_depth': _weighted_metric(items, 'page_depth'),
        'avg_visit_duration_seconds': _weighted_metric(
            items, 'avg_visit_duration_seconds',
        ),
        'goal_reaches': goal_reaches,
        'messenger_reaches': messenger_reaches,
        'landings': items,
        'trend': trend,
    }


def _current_anchor(store: AnalyticsStore) -> dt.date:
    rows = store.latest_snapshot()
    checks = [parse_time(row['checked_at']).date() for row in rows if row.get('checked_at')]
    return max(checks) if checks else dt.datetime.now(dt.timezone.utc).date()


def merge_keyword_analytics(position_rows: Sequence[dict], webmaster: dict, metrika: dict) -> list[dict]:
    webmaster_by_query = {normalize_query(row['query_text']): row for row in webmaster['queries']}
    metrika_by_landing = {row['landing_page']: row for row in metrika['landings']}
    merged = []
    for row in position_rows:
        query = webmaster_by_query.get(normalize_query(row['keyword']))
        landing = _landing_path(row.get('found_url'))
        landing_analytics = metrika_by_landing.get(landing) if landing else None
        merged.append({
            'keyword_id': row['keyword_id'],
            'keyword': row['keyword'],
            'category': row['category'],
            'position': row.get('position'),
            'position_status': row.get('status'),
            'frequency': row.get('frequency'),
            'found_url': row.get('found_url'),
            'webmaster': query,
            'landing_page': landing,
            # Conversions remain attached to the landing page, never to the query.
            'landing_analytics': landing_analytics,
            'conversion_attribution': 'landing_page' if landing_analytics else None,
        })
    return merged


def _status_label(status: dict | None) -> str:
    if not status:
        return 'нет данных'
    return {
        'ok': 'готово', 'not_configured': 'не настроено', 'error': 'ошибка',
    }.get(status.get('status'), 'нет данных')


def _metric(value, suffix: str = '') -> str:
    if value is None:
        return 'нет данных'
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f'{value}{suffix}'


def format_combined_period(position_summary: dict, webmaster: dict, metrika: dict) -> str:
    text = format_telegram_report(position_summary)
    lines = [text, '', '🔍 Яндекс Вебмастер']
    if webmaster['query_count'] is None:
        lines.append('Данных за период нет.')
    else:
        lines.extend([
            f"Запросов: {webmaster['query_count']}",
            f"Показы: {_metric(webmaster['shows'])}",
            f"Клики: {_metric(webmaster['clicks'])}",
            f"CTR: {_metric(webmaster['ctr'], '%')}",
            f"Новых запросов вне семантики: {len(webmaster['new_queries'])}",
        ])
    lines.extend(['', '📊 Яндекс Метрика'])
    if metrika['visits'] is None:
        lines.append('Органический трафик за период: нет данных.')
    else:
        lines.extend([
            f"Органические визиты: {_metric(metrika['visits'])}",
            f"Пользователи: {_metric(metrika['users'])}",
            f"Достижения целей: {_metric(metrika['goal_reaches'])}",
            f"Переходы в мессенджеры: {_metric(metrika['messenger_reaches'])}",
        ])
    return '\n'.join(lines)


def position_series(store: AnalyticsStore, days: int, keyword_id: int | None = None) -> list[dict]:
    anchor = _current_anchor(store)
    date1, date2 = _period_bounds(anchor, days)
    with store.session() as connection:
        parameters: list[object] = [date1, date2]
        predicate = ''
        if keyword_id is not None:
            predicate = ' AND c.keyword_id = ?'
            parameters.append(keyword_id)
        rows = connection.execute(
            f"""SELECT c.keyword_id, k.keyword, substr(c.checked_at, 1, 10) AS day,
                       c.position, c.status
                FROM seo_position_checks c
                JOIN seo_keywords k ON k.id = c.keyword_id
                WHERE substr(c.checked_at, 1, 10) BETWEEN ? AND ?
                  AND c.source = 'topvisor' {predicate}
                ORDER BY day, c.keyword_id, c.id""",
            parameters,
        ).fetchall()
    latest = {}
    for row in rows:
        latest[(row['day'], row['keyword_id'])] = dict(row)
    by_day = defaultdict(list)
    for row in latest.values():
        by_day[row['day']].append(row)
    result = []
    start = dt.date.fromisoformat(date1)
    end = dt.date.fromisoformat(date2)
    day = start
    while day <= end:
        values = by_day.get(day.isoformat(), [])
        found = [row['position'] for row in values if row['status'] == 'found']
        result.append({
            'date': day.isoformat(),
            'average_position': None if not found else round(sum(found) / len(found), 2),
            'top10': None if not values else sum(
                row['status'] == 'found' and row['position'] <= 10 for row in values
            ),
            'position': (
                values[-1]['position'] if keyword_id is not None and values
                and values[-1]['status'] == 'found' else None
            ),
        })
        day += dt.timedelta(days=1)
    return result


def position_distribution_series(store: AnalyticsStore, days: int) -> list[dict]:
    anchor = _current_anchor(store)
    date1, date2 = _period_bounds(anchor, days)
    with store.session() as connection:
        rows = connection.execute(
            """SELECT c.keyword_id, substr(c.checked_at, 1, 10) AS day,
                      c.position, c.status, c.id
               FROM seo_position_checks c
               WHERE substr(c.checked_at, 1, 10) BETWEEN ? AND ?
                 AND c.source = 'topvisor'
               ORDER BY day, c.keyword_id, c.id""",
            (date1, date2),
        ).fetchall()
    latest = {}
    for row in rows:
        latest[(row['day'], row['keyword_id'])] = dict(row)
    by_day = defaultdict(list)
    for row in latest.values():
        by_day[row['day']].append(row)
    result = []
    day = dt.date.fromisoformat(date1)
    end = dt.date.fromisoformat(date2)
    while day <= end:
        values = by_day.get(day.isoformat(), [])
        found = [row['position'] for row in values if row['status'] == 'found']
        result.append({
            'date': day.isoformat(),
            'top3': None if not values else sum(value <= 3 for value in found),
            'top10': None if not values else sum(value <= 10 for value in found),
            'top20': None if not values else sum(value <= 20 for value in found),
            'top50': None if not values else sum(value <= 50 for value in found),
            'not_found': None if not values else sum(
                row['status'] == 'not_found' for row in values
            ),
        })
        day += dt.timedelta(days=1)
    return result


def visualization_payload(store: AnalyticsStore, periods: dict) -> dict:
    charts = {}
    for days in (1, 3, 7, 30):
        summary = periods[str(days)]['positions']
        charts[str(days)] = {
            'average_position': position_series(store, days),
            'distribution': position_distribution_series(store, days),
            'movement': {
                'improved': summary['improved'],
                'declined': summary['declined'],
                'unchanged': summary['unchanged'],
                'appeared': summary['appeared'],
                'disappeared': summary['disappeared'],
            },
        }
    return charts


def build_period_context(
    store: AnalyticsStore, config: dict, anchor: dt.date, days: int,
    *, positions: dict | None = None,
) -> dict:
    """Everything charts/dashboard.py needs to render one period's screens."""
    prev_anchor = anchor - dt.timedelta(days=days)
    return {
        'days': days,
        'anchor_date': anchor.isoformat(),
        'generated_at': iso_time(),
        'positions': positions if positions is not None else build_summary(store, days, config['positions']),
        'position_series': position_series(store, days),
        'distribution_series': position_distribution_series(store, days),
        'metrika': metrika_period(store, anchor, days),
        'metrika_prev': metrika_period(store, prev_anchor, days),
        'webmaster': webmaster_period(store, anchor, days),
    }


def _portfolio_wordstat_points(position_rows: Sequence[dict]) -> list[dict]:
    """Single current snapshot: the pipeline has no monthly frequency
    history yet (see charts/wordstat.py), so this is one honest data point,
    not a fabricated multi-month trend."""
    total = sum(row['frequency'] for row in position_rows if row.get('frequency') is not None)
    if not total:
        return []
    return [{'label': 'Текущий снимок', 'value': round(total)}]


def generate_visual_charts(
    store: AnalyticsStore, config: dict, position_rows: Sequence[dict],
    contexts: dict[int, dict], anchor: dt.date,
) -> dict:
    """Render (or reuse from cache) every PNG the Telegram bot can send.

    ``contexts`` maps period-days -> the dict built by build_period_context.
    Nothing here is generated twice for the same data: see charts/cache.py.
    """
    charts_dir = Path(config['charts_path'])
    version = chart_cache.compute_data_version(store)
    wordstat_points = _portfolio_wordstat_points(position_rows)

    def cached(report_type: str, period: str, render_fn) -> str:
        return str(chart_cache.render_cached(charts_dir, report_type, period, version, render_fn))

    result: dict = {'data_version': version, 'average_position': {}, 'top10_dynamics': {},
                     'distribution': {}, 'growth_drop': {}, 'traffic': {}, 'conversions': {}, 'keyword': {}}

    for days in (3, 7, 30, 90):
        context = contexts.get(days) or build_period_context(store, config, anchor, days)
        contexts[days] = context
        series = context['position_series']
        dist = context['distribution_series']
        positions = context['positions']

        result['average_position'][str(days)] = cached(
            'average-position', str(days),
            lambda p, s=series, d=days: chart_positions.average_position_chart(s, d, p),
        )
        result['top10_dynamics'][str(days)] = cached(
            'top10-dynamics', str(days),
            lambda p, s=series, d=days: chart_positions.top10_dynamics_chart(s, d, p),
        )
        result['distribution'][str(days)] = cached(
            'distribution', str(days),
            lambda p, s=dist, d=days: chart_positions.distribution_chart(s, d, p),
        )
        result['growth_drop'][str(days)] = cached(
            'growth-drop', str(days),
            lambda p, pos=positions, d=days: chart_positions.growth_drop_chart(
                pos.get('best_growth') or [], pos.get('worst_drop') or [], d, p,
            ),
        )
        if context['metrika'].get('visits') is not None:
            result['traffic'][str(days)] = cached(
                'traffic', str(days),
                lambda p, ctx=context, d=days: chart_traffic.traffic_chart(ctx['metrika']['trend'], d, p),
            )
        if (context['metrika'].get('goal_reaches') or 0) or context['metrika'].get('visits') is not None:
            result['conversions'][str(days)] = cached(
                'conversions', str(days),
                lambda p, ctx=context, d=days: chart_traffic.conversions_chart(ctx['metrika'], d, p),
            )

    context1 = contexts.get(1) or build_period_context(store, config, anchor, 1)
    contexts[1] = context1
    context3 = contexts.get(3) or build_period_context(store, config, anchor, 3)
    contexts[3] = context3
    context7 = contexts[7]
    context30 = contexts[30]
    # The daily card's KPI values are "today" (context1), but a 1-point
    # series can't draw a sparkline -- borrow the 7-day trend for that so
    # the card still shows a mini history line, per spec section 12.
    daily_context = {**context1, 'position_series': context7['position_series']}
    result['dashboard'] = {
        '1': cached('dashboard', '1', lambda p, ctx=daily_context: chart_dashboard.daily_card(ctx, p)),
        '3': cached('dashboard', '3', lambda p, ctx=context3: chart_dashboard.dashboard_7d(ctx, p)),
        '7': cached('dashboard', '7', lambda p, ctx=context7: chart_dashboard.dashboard_7d(ctx, p)),
        '30_1': cached('dashboard', '30-1', lambda p, ctx=context30: chart_dashboard.dashboard_30d_part1(
            {**ctx, 'wordstat_points': wordstat_points}, p)),
        '30_2': cached('dashboard', '30-2', lambda p, ctx=context30: chart_dashboard.dashboard_30d_part2(
            {**ctx, 'wordstat_points': wordstat_points}, p)),
    }
    result['daily'] = result['dashboard']['1']  # kept for backward compatibility

    if wordstat_points:
        result['wordstat'] = cached(
            'wordstat', 'portfolio',
            lambda p: chart_wordstat.wordstat_chart('Суммарная частотность ядра', wordstat_points, p),
        )

    weekly_dir = charts_dir / 'weekly'
    result['weekly'] = {}
    weekly_paths = chart_dashboard.weekly_report_images(context7, weekly_dir, version=version)
    for name, weekly_path in zip(('dashboard', 'positions', 'traffic'), weekly_paths):
        result['weekly'][name] = str(weekly_path)

    for row in position_rows:
        keyword_id = row['keyword_id']
        history = keyword_history(store, row['keyword'], config['positions'])
        if not history:
            continue
        history['frequency'] = row.get('frequency')
        kw_series = position_series(store, 30, keyword_id)
        result['keyword'][str(keyword_id)] = cached(
            'keyword', str(keyword_id),
            lambda p, h=history, s=kw_series: chart_positions.keyword_card(h, s, p),
        )

    return result


def build_dashboard(config: dict, store: AnalyticsStore, *, with_charts: bool = True) -> dict:
    store.initialize()
    anchor = _current_anchor(store)
    position_rows = store.latest_snapshot()
    statuses = source_statuses(store)
    periods = {}
    for days in (1, 3, 7, 30):
        positions = build_summary(store, days, config['positions'])
        webmaster = webmaster_period(store, anchor, days)
        metrika = metrika_period(store, anchor, days)
        periods[str(days)] = {
            'positions': positions,
            'webmaster': webmaster,
            'metrika': metrika,
            'merged_keywords': merge_keyword_analytics(position_rows, webmaster, metrika),
            'telegram_text': format_combined_period(positions, webmaster, metrika),
        }
    histories = {
        str(row['keyword_id']): keyword_history(store, row['keyword'], config['positions'])
        for row in position_rows
    }
    keyword_series = {
        str(row['keyword_id']): position_series(store, 30, row['keyword_id'])
        for row in position_rows
    }
    charts = {}
    chart_error = None
    if with_charts:
        try:
            contexts = {
                days: {
                    **build_period_context(store, config, anchor, days, positions=periods[str(days)]['positions']),
                }
                for days in (1, 3, 7, 30)
            }
            charts = generate_visual_charts(store, config, position_rows, contexts, anchor)
        except (SeoError, OSError, sqlite3.Error, ValueError, KeyError) as error:
            chart_error = f'{type(error).__name__}: {error}'
    dashboard = {
        'generated_at': iso_time(),
        'anchor_date': anchor.isoformat(),
        'position_source': 'topvisor',
        'search_api_reserve_enabled': bool(
            (config['positions'].get('yandex_search_api') or {}).get('enabled')
        ),
        'sources': statuses,
        'source_labels': {name: _status_label(status) for name, status in statuses.items()},
        'keywords': position_rows,
        'keyword_histories': histories,
        'keyword_series': keyword_series,
        'periods': periods,
        'visualizations': visualization_payload(store, periods),
        'charts': charts,
        'chart_error': chart_error,
    }
    return dashboard


def write_dashboard(config: dict, dashboard: dict) -> Path:
    path = Path(config['dashboard_path'])
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dashboard, ensure_ascii=False, indent=2).encode('utf-8')
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    build = subparsers.add_parser('build')
    build.add_argument('--no-charts', action='store_true')
    report = subparsers.add_parser('report')
    report.add_argument('--days', choices=(1, 3, 7, 30), type=int, default=7)
    args = parser.parse_args(argv)
    try:
        config = load_source_config()
        store = AnalyticsStore(config['database_path'])
        dashboard = build_dashboard(config, store, with_charts=not getattr(args, 'no_charts', False))
        if args.command == 'report':
            print(dashboard['periods'][str(args.days)]['telegram_text'])
        else:
            path = write_dashboard(config, dashboard)
            print(f'Wrote SEO dashboard: {path}')
            if dashboard['chart_error']:
                print('Charts unavailable: ' + dashboard['chart_error'], file=sys.stderr)
        return 0
    except (SeoError, OSError, sqlite3.Error, ValueError) as error:
        print(f'SEO DASHBOARD FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
