"""Collect Topvisor, Yandex Webmaster and Yandex Metrika SEO data.

The collectors keep source semantics separate.  Missing fields are stored as
NULL, and an API failure never creates a zero-valued analytics row.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from seo_common import PROJECT_ROOT, SeoError, settings
from seo_positions import (
    PositionCheck,
    PositionStore,
    generate_events,
    iso_time,
    load_keywords,
    load_position_config,
)


TOPVISOR_ENDPOINT = 'https://api.topvisor.com/v2/json/get/positions_2/history'
WEBMASTER_ENDPOINT = 'https://api.webmaster.yandex.net/v4'
METRIKA_REPORT_ENDPOINT = 'https://api-metrika.yandex.net/stat/v1/data'
METRIKA_MANAGEMENT_ENDPOINT = 'https://api-metrika.yandex.net/management/v1'
SOURCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS seo_source_runs (
    run_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    period_start TEXT,
    period_end TEXT,
    status TEXT NOT NULL CHECK (status IN ('ok', 'not_configured', 'error')),
    row_count INTEGER,
    error_code TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_runs_source_time
ON seo_source_runs(source, finished_at DESC);

CREATE TABLE IF NOT EXISTS seo_webmaster_queries (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES seo_source_runs(run_id),
    fetched_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    query_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    device TEXT NOT NULL,
    shows REAL,
    clicks REAL,
    ctr REAL,
    avg_show_position REAL,
    avg_click_position REAL,
    is_target INTEGER NOT NULL CHECK (is_target IN (0, 1)),
    target_keyword_id INTEGER REFERENCES seo_keywords(id),
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_webmaster_period_query
ON seo_webmaster_queries(period_start, period_end, query_text, fetched_at DESC);

CREATE TABLE IF NOT EXISTS seo_metrika_landings (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES seo_source_runs(run_id),
    fetched_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    landing_page TEXT NOT NULL,
    search_engine TEXT,
    visits REAL,
    users REAL,
    bounce_rate REAL,
    page_depth REAL,
    avg_visit_duration_seconds REAL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrika_landing_period
ON seo_metrika_landings(period_start, period_end, landing_page, fetched_at DESC);

CREATE TABLE IF NOT EXISTS seo_metrika_goals (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES seo_source_runs(run_id),
    fetched_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    landing_page TEXT NOT NULL,
    search_engine TEXT,
    goal_id INTEGER NOT NULL,
    goal_name TEXT,
    goal_type TEXT,
    reaches REAL,
    conversion_rate REAL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrika_goal_period
ON seo_metrika_goals(period_start, period_end, landing_page, goal_id, fetched_at DESC);

CREATE TRIGGER IF NOT EXISTS seo_webmaster_queries_no_update
BEFORE UPDATE ON seo_webmaster_queries BEGIN
    SELECT RAISE(ABORT, 'seo_webmaster_queries is append-only');
END;
CREATE TRIGGER IF NOT EXISTS seo_webmaster_queries_no_delete
BEFORE DELETE ON seo_webmaster_queries BEGIN
    SELECT RAISE(ABORT, 'seo_webmaster_queries is append-only');
END;
CREATE TRIGGER IF NOT EXISTS seo_metrika_landings_no_update
BEFORE UPDATE ON seo_metrika_landings BEGIN
    SELECT RAISE(ABORT, 'seo_metrika_landings is append-only');
END;
CREATE TRIGGER IF NOT EXISTS seo_metrika_landings_no_delete
BEFORE DELETE ON seo_metrika_landings BEGIN
    SELECT RAISE(ABORT, 'seo_metrika_landings is append-only');
END;
CREATE TRIGGER IF NOT EXISTS seo_metrika_goals_no_update
BEFORE UPDATE ON seo_metrika_goals BEGIN
    SELECT RAISE(ABORT, 'seo_metrika_goals is append-only');
END;
CREATE TRIGGER IF NOT EXISTS seo_metrika_goals_no_delete
BEFORE DELETE ON seo_metrika_goals BEGIN
    SELECT RAISE(ABORT, 'seo_metrika_goals is append-only');
END;
"""


class SourceFailure(SeoError):
    def __init__(self, source: str, message: str, code: str | None = None):
        super().__init__(message)
        self.source = source
        self.code = code


class MissingCredentials(SourceFailure):
    pass


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def configured_timezone(name: str) -> dt.tzinfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == 'Europe/Moscow':
            return dt.timezone(dt.timedelta(hours=3), name='Europe/Moscow')
        raise SeoError(f'Timezone data is unavailable for {name}.')


def load_source_config() -> dict:
    data = settings()
    positions = load_position_config()
    analytics = dict(data.get('analytics') or {})
    required = {'timezone', 'dashboard_path', 'charts_path', 'webmaster', 'metrika'}
    missing = sorted(required - analytics.keys())
    if missing:
        raise SeoError('Missing analytics settings: ' + ', '.join(missing))
    analytics['database_path'] = positions['database_path']
    analytics['dashboard_path'] = str(resolve_path(analytics['dashboard_path']))
    analytics['charts_path'] = str(resolve_path(analytics['charts_path']))
    analytics['positions'] = positions
    analytics['site_url'] = data['site_url']
    return analytics


def normalize_query(value: str) -> str:
    return re.sub(r'\s+', ' ', value.strip().casefold().replace('ё', 'е'))


def nullable_number(value) -> float | None:
    if value is None or value == '' or value == '--' or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer_or_none(value) -> int | None:
    number = nullable_number(value)
    if number is None or number < 1 or not number.is_integer():
        return None
    return int(number)


class JsonHttpClient:
    def __init__(self, opener: Callable = urllib.request.urlopen, timeout: int = 30):
        self.opener = opener
        self.timeout = timeout

    def request(
        self,
        url: str,
        *,
        method: str = 'GET',
        headers: dict | None = None,
        body: dict | None = None,
        source: str,
    ) -> dict:
        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            url,
            data=encoded,
            method=method,
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Magic-SEO/2.0',
                **({'Content-Type': 'application/json; charset=utf-8'} if body is not None else {}),
                **(headers or {}),
            },
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', errors='replace')[:500]
            raise SourceFailure(source, f'{source} HTTP {error.code}: {detail}', str(error.code)) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise SourceFailure(source, f'{source} request failed: {type(error).__name__}') from error
        try:
            decoded = json.loads(payload.decode('utf-8-sig'))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise SourceFailure(source, f'{source} returned invalid JSON.') from error
        if not isinstance(decoded, dict):
            raise SourceFailure(source, f'{source} returned a non-object response.')
        return decoded


@dataclass(frozen=True)
class TopvisorRecord:
    keyword: str
    measured_on: str
    position: int | None
    found_url: str | None
    title: str | None
    frequency: float | None
    frequency_present: bool
    topvisor_keyword_id: int | None = None


def _topvisor_frequency(row: dict, field: str) -> tuple[bool, float | None]:
    candidates = [row]
    if isinstance(row.get('fields'), dict):
        candidates.append(row['fields'])
    for candidate in candidates:
        if field in candidate:
            return True, nullable_number(candidate[field])
    return False, None


def parse_topvisor_history(payload: dict, volume_field: str) -> list[TopvisorRecord]:
    errors = payload.get('errors') or []
    if errors:
        raise SourceFailure('topvisor', 'Topvisor API error: ' + json.dumps(errors, ensure_ascii=False)[:800])
    result = payload.get('result') or {}
    rows = result.get('keywords') if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise SourceFailure('topvisor', 'Topvisor response has no result.keywords array.')
    records = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        keyword = str(row.get('name') or row.get('keyword') or row.get('text') or '').strip()
        if not keyword:
            continue
        frequency_present, frequency = _topvisor_frequency(row, volume_field)
        keyword_id = integer_or_none(row.get('id'))
        positions = row.get('positionsData') or {}
        if not isinstance(positions, dict):
            continue
        for external_key, value in positions.items():
            measured_on = str(external_key).split(':', 1)[0]
            try:
                dt.date.fromisoformat(measured_on)
            except ValueError:
                continue
            item = value if isinstance(value, dict) else {'position': value}
            position = integer_or_none(item.get('position'))
            url = str(item.get('relevant_url') or '').strip() or None
            snippet = item.get('snippet')
            title = None
            if isinstance(snippet, dict):
                title = str(snippet.get('title') or '').strip() or None
            elif isinstance(snippet, str):
                title = snippet.strip() or None
            records.append(TopvisorRecord(
                keyword, measured_on, position, url, title,
                frequency, frequency_present, keyword_id,
            ))
    return sorted(records, key=lambda item: (item.measured_on, normalize_query(item.keyword)))


def load_topvisor_bootstrap(path: str | Path) -> list[TopvisorRecord]:
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise SourceFailure('topvisor', f'Unable to read Topvisor bootstrap: {error}') from error
    records = []
    for row in payload.get('measurements') or []:
        records.append(TopvisorRecord(
            keyword=str(row['keyword']),
            measured_on=str(row['date']),
            position=integer_or_none(row.get('position')),
            found_url=str(row.get('found_url') or '').strip() or None,
            title=str(row.get('title') or '').strip() or None,
            frequency=nullable_number(row.get('frequency')),
            frequency_present='frequency' in row,
            topvisor_keyword_id=integer_or_none(row.get('topvisor_keyword_id')),
        ))
    return sorted(records, key=lambda item: (item.measured_on, normalize_query(item.keyword)))


class TopvisorApi:
    def __init__(
        self,
        user_id: str,
        api_key: str,
        project_id: int,
        region_index: int,
        volume_field: str,
        client: JsonHttpClient | None = None,
    ):
        if not user_id or not api_key:
            raise MissingCredentials('topvisor', 'TOPVISOR_USER_ID and TOPVISOR_API_KEY are required.')
        self.user_id = user_id
        self.api_key = api_key
        self.project_id = int(project_id)
        self.region_index = int(region_index)
        self.volume_field = volume_field
        self.client = client or JsonHttpClient()

    def history(self, date1: dt.date, date2: dt.date) -> list[TopvisorRecord]:
        payload = self.client.request(
            TOPVISOR_ENDPOINT,
            method='POST',
            headers={
                'User-Id': self.user_id,
                'Authorization': 'bearer ' + self.api_key,
            },
            body={
                'project_id': self.project_id,
                'regions_indexes': [self.region_index],
                'date1': date1.isoformat(),
                'date2': date2.isoformat(),
                'type_range': 0,
                'limit': 10000,
                'fields': ['id', 'name', self.volume_field],
                'positions_fields': ['position', 'relevant_url', 'snippet'],
                'show_exists_dates': 1,
            },
            source='topvisor',
        )
        return parse_topvisor_history(payload, self.volume_field)


class AnalyticsStore(PositionStore):
    def initialize(self) -> None:
        super().initialize()
        with self.session() as connection:
            connection.executescript(SOURCE_SCHEMA)
            columns = {
                row['name'] for row in connection.execute(
                    'PRAGMA table_info(seo_metrika_landings)'
                )
            }
            migrations = {
                'page_depth': (
                    'ALTER TABLE seo_metrika_landings ADD COLUMN page_depth REAL'
                ),
                'avg_visit_duration_seconds': (
                    'ALTER TABLE seo_metrika_landings '
                    'ADD COLUMN avg_visit_duration_seconds REAL'
                ),
            }
            for column, statement in migrations.items():
                if column not in columns:
                    connection.execute(statement)

    def add_source_run(
        self,
        *,
        run_id: str,
        source: str,
        started_at: str,
        finished_at: str,
        period_start: str | None,
        period_end: str | None,
        status: str,
        row_count: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.initialize()
        with self.session() as connection:
            connection.execute(
                """INSERT INTO seo_source_runs
                   (run_id, source, started_at, finished_at, period_start, period_end,
                    status, row_count, error_code, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, source, started_at, finished_at, period_start, period_end,
                 status, row_count, error_code, error_message),
            )

    def add_webmaster_rows(self, run_id: str, fetched_at: str, rows: Sequence[dict]) -> None:
        if not rows:
            return
        with self.session() as connection:
            connection.executemany(
                """INSERT INTO seo_webmaster_queries
                   (run_id, fetched_at, period_start, period_end, query_id, query_text,
                    device, shows, clicks, ctr, avg_show_position, avg_click_position,
                    is_target, target_keyword_id, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'yandex_webmaster')""",
                [(
                    run_id, fetched_at, row['period_start'], row['period_end'],
                    row['query_id'], row['query_text'], row['device'], row['shows'],
                    row['clicks'], row['ctr'], row['avg_show_position'],
                    row['avg_click_position'], int(row['is_target']),
                    row['target_keyword_id'],
                ) for row in rows],
            )

    def add_metrika_landings(self, run_id: str, fetched_at: str, rows: Sequence[dict]) -> None:
        if not rows:
            return
        with self.session() as connection:
            connection.executemany(
                """INSERT INTO seo_metrika_landings
                   (run_id, fetched_at, period_start, period_end, landing_page,
                    search_engine, visits, users, bounce_rate, page_depth,
                    avg_visit_duration_seconds, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'yandex_metrika')""",
                [(
                    run_id, fetched_at, row['period_start'], row['period_end'],
                    row['landing_page'], row['search_engine'], row['visits'],
                    row['users'], row['bounce_rate'], row.get('page_depth'),
                    row.get('avg_visit_duration_seconds'),
                ) for row in rows],
            )

    def add_metrika_goals(self, run_id: str, fetched_at: str, rows: Sequence[dict]) -> None:
        if not rows:
            return
        with self.session() as connection:
            connection.executemany(
                """INSERT INTO seo_metrika_goals
                   (run_id, fetched_at, period_start, period_end, landing_page,
                    search_engine, goal_id, goal_name, goal_type, reaches,
                    conversion_rate, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'yandex_metrika')""",
                [(
                    run_id, fetched_at, row['period_start'], row['period_end'],
                    row['landing_page'], row['search_engine'], row['goal_id'],
                    row['goal_name'], row['goal_type'], row['reaches'],
                    row['conversion_rate'],
                ) for row in rows],
            )


def topvisor_checked_at(measured_on: str) -> str:
    # Topvisor exposes a date, not a timestamp. Noon in Moscow keeps the date stable.
    local = dt.datetime.combine(
        dt.date.fromisoformat(measured_on), dt.time(12), configured_timezone('Europe/Moscow'),
    )
    return iso_time(local)


def sync_topvisor_records(
    store: AnalyticsStore,
    records: Sequence[TopvisorRecord],
    config: dict,
    *,
    source: str = 'topvisor',
) -> dict:
    keywords = load_keywords(config['keywords_path'], config)
    store.sync_keywords(keywords)
    active = {normalize_query(row['keyword']): row for row in store.active_keywords()}
    inserted = skipped = unknown = events_count = 0
    seen_frequency = set()
    for record in records:
        row = active.get(normalize_query(record.keyword))
        if row is None:
            unknown += 1
            continue
        checked_at = topvisor_checked_at(record.measured_on)
        frequency_present = record.frequency_present and row['id'] not in seen_frequency
        store.update_keyword_source_data(
            row['id'],
            topvisor_keyword_id=record.topvisor_keyword_id,
            frequency=record.frequency,
            frequency_checked_at=checked_at,
            frequency_present=frequency_present,
        )
        if frequency_present:
            seen_frequency.add(row['id'])
        if store.measurement_exists(row['id'], checked_at, source):
            skipped += 1
            continue
        status = 'found' if record.position is not None else 'not_found'
        if status == 'found' and not record.found_url:
            raise SourceFailure(
                'topvisor',
                f'Topvisor returned position without relevant_url for {record.keyword!r}.',
            )
        previous = store.previous_usable(row['id'], checked_at)
        check = PositionCheck(
            record.keyword, row['category'], row['region'], row['device'],
            checked_at, record.position, record.found_url, record.title, status,
            int(config['search_depth']), source,
        )
        run_id = f'topvisor:{record.measured_on}:{uuid.uuid4()}'
        check_id = store.add_check(row['id'], check, run_id)
        event_types = generate_events(
            previous['status'] if previous else None,
            previous['position'] if previous else None,
            status,
            record.position,
            big_move_threshold=int(config['big_move_threshold']),
        )
        store.add_events(
            check_id=check_id,
            keyword_id=row['id'],
            event_types=event_types,
            created_at=checked_at,
            previous_position=previous['position'] if previous else None,
            current_position=record.position,
            run_id=run_id,
            payload={'keyword': record.keyword, 'url': record.found_url, 'source': source},
        )
        events_count += len(event_types)
        inserted += 1
    return {
        'records': len(records), 'inserted': inserted, 'skipped': skipped,
        'unknown': unknown, 'events': events_count,
    }


class YandexWebmasterApi:
    def __init__(self, token: str, client: JsonHttpClient | None = None):
        if not token:
            raise MissingCredentials('yandex_webmaster', 'YANDEX_WEBMASTER_TOKEN is required.')
        self.token = token
        self.client = client or JsonHttpClient()

    @property
    def headers(self) -> dict:
        return {'Authorization': 'OAuth ' + self.token}

    def _get(self, path: str, params: Sequence[tuple[str, object]] = ()) -> dict:
        query = urllib.parse.urlencode(params, doseq=True)
        url = WEBMASTER_ENDPOINT + path + (('?' + query) if query else '')
        return self.client.request(url, headers=self.headers, source='yandex_webmaster')

    def discover_site(self, site_url: str, configured_host_id: str = '') -> tuple[int, str]:
        user = self._get('/user')
        user_id = int(user.get('user_id') or user.get('id') or 0)
        if user_id < 1:
            raise SourceFailure('yandex_webmaster', 'Webmaster API returned no user_id.')
        if configured_host_id:
            return user_id, configured_host_id
        hosts_payload = self._get(f'/user/{user_id}/hosts')
        target = (urllib.parse.urlsplit(site_url).hostname or '').casefold()
        for host in hosts_payload.get('hosts') or []:
            candidates = [
                host.get('unicode_host_url'), host.get('ascii_host_url'), host.get('host_id'),
            ]
            if any(target and target in str(value).casefold() for value in candidates if value):
                return user_id, str(host['host_id'])
        raise SourceFailure('yandex_webmaster', f'No verified Webmaster host matched {target}.')

    def popular(
        self,
        user_id: int,
        host_id: str,
        date_from: dt.date,
        date_to: dt.date,
        *,
        order_by: str,
        device: str,
        limit: int,
    ) -> list[dict]:
        params = [
            ('order_by', order_by),
            ('query_indicator', 'TOTAL_SHOWS'),
            ('query_indicator', 'TOTAL_CLICKS'),
            ('query_indicator', 'AVG_SHOW_POSITION'),
            ('query_indicator', 'AVG_CLICK_POSITION'),
            ('device_type_indicator', device),
            ('date_from', date_from.isoformat()),
            ('date_to', date_to.isoformat()),
            ('offset', 0),
            ('limit', limit),
        ]
        encoded_host = urllib.parse.quote(host_id, safe='')
        payload = self._get(
            f'/user/{user_id}/hosts/{encoded_host}/search-queries/popular', params,
        )
        return [row for row in (payload.get('queries') or []) if isinstance(row, dict)]


def webmaster_rows(
    api: YandexWebmasterApi,
    *,
    site_url: str,
    host_id: str,
    date_from: dt.date,
    date_to: dt.date,
    device: str,
    limit: int,
    targets: dict[str, int],
) -> list[dict]:
    user_id, selected_host = api.discover_site(site_url, host_id)
    merged = {}
    for order in ('TOTAL_SHOWS', 'TOTAL_CLICKS'):
        for row in api.popular(
            user_id, selected_host, date_from, date_to,
            order_by=order, device=device, limit=limit,
        ):
            key = str(row.get('query_id') or normalize_query(str(row.get('query_text') or '')))
            merged[key] = row
    result = []
    for row in merged.values():
        query_text = str(row.get('query_text') or '').strip()
        if not query_text:
            continue
        indicators = row.get('indicators') or {}
        shows = nullable_number(indicators.get('TOTAL_SHOWS'))
        clicks = nullable_number(indicators.get('TOTAL_CLICKS'))
        ctr = None if shows in (None, 0) or clicks is None else round(clicks / shows * 100, 6)
        target_keyword_id = targets.get(normalize_query(query_text))
        result.append({
            'period_start': date_from.isoformat(),
            'period_end': date_to.isoformat(),
            'query_id': str(row.get('query_id') or normalize_query(query_text)),
            'query_text': query_text,
            'device': device,
            'shows': shows,
            'clicks': clicks,
            'ctr': ctr,
            'avg_show_position': nullable_number(indicators.get('AVG_SHOW_POSITION')),
            'avg_click_position': nullable_number(indicators.get('AVG_CLICK_POSITION')),
            'is_target': target_keyword_id is not None,
            'target_keyword_id': target_keyword_id,
        })
    return result


class YandexMetrikaApi:
    def __init__(self, token: str, counter_id: int, client: JsonHttpClient | None = None):
        if not token:
            raise MissingCredentials('yandex_metrika', 'YANDEX_METRIKA_TOKEN is required.')
        self.token = token
        self.counter_id = int(counter_id)
        self.client = client or JsonHttpClient()

    @property
    def headers(self) -> dict:
        return {'Authorization': 'OAuth ' + self.token}

    def goals(self) -> list[dict]:
        payload = self.client.request(
            f'{METRIKA_MANAGEMENT_ENDPOINT}/counter/{self.counter_id}/goals',
            headers=self.headers,
            source='yandex_metrika',
        )
        return [row for row in (payload.get('goals') or []) if isinstance(row, dict)]

    def report(
        self,
        date_from: dt.date,
        date_to: dt.date,
        *,
        metrics: Sequence[str],
        dimensions: Sequence[str],
        filter_expression: str,
        accuracy: str,
    ) -> dict:
        params = {
            'ids': self.counter_id,
            'date1': date_from.isoformat(),
            'date2': date_to.isoformat(),
            'metrics': ','.join(metrics),
            'dimensions': ','.join(dimensions),
            'filters': filter_expression,
            'accuracy': accuracy,
            'limit': 10000,
            'lang': 'ru',
        }
        return self.client.request(
            METRIKA_REPORT_ENDPOINT + '?' + urllib.parse.urlencode(params),
            headers=self.headers,
            source='yandex_metrika',
        )


def _dimension_value(value) -> str | None:
    if isinstance(value, dict):
        selected = value.get('id') if value.get('id') is not None else value.get('name')
    else:
        selected = value
    return None if selected is None else str(selected).strip() or None


def parse_metrika_report(payload: dict, metric_names: Sequence[str]) -> list[dict]:
    rows = []
    for row in payload.get('data') or []:
        dimensions = row.get('dimensions') or []
        metrics = row.get('metrics') or []
        rows.append({
            'landing_page': _dimension_value(dimensions[0]) if dimensions else None,
            'search_engine': _dimension_value(dimensions[1]) if len(dimensions) > 1 else None,
            **{
                name: nullable_number(metrics[index]) if index < len(metrics) else None
                for index, name in enumerate(metric_names)
            },
        })
    return [row for row in rows if row['landing_page'] is not None]


def collect_metrika_rows(
    api: YandexMetrikaApi,
    *,
    date_from: dt.date,
    date_to: dt.date,
    filter_expression: str,
    accuracy: str,
    configured_goal_ids: set[int] | None = None,
) -> tuple[list[dict], list[dict]]:
    dimensions = ['ym:s:startURLPath', 'ym:s:searchEngine']
    traffic_payload = api.report(
        date_from, date_to,
        metrics=[
            'ym:s:visits', 'ym:s:users', 'ym:s:bounceRate',
            'ym:s:pageDepth', 'ym:s:avgVisitDurationSeconds',
        ],
        dimensions=dimensions,
        filter_expression=filter_expression,
        accuracy=accuracy,
    )
    landings = []
    for row in parse_metrika_report(traffic_payload, [
        'visits', 'users', 'bounce_rate', 'page_depth',
        'avg_visit_duration_seconds',
    ]):
        landings.append({
            'period_start': date_from.isoformat(), 'period_end': date_to.isoformat(), **row,
        })
    goals = []
    for goal in api.goals():
        goal_id = integer_or_none(goal.get('id'))
        if goal_id is None or (configured_goal_ids is not None and goal_id not in configured_goal_ids):
            continue
        payload = api.report(
            date_from, date_to,
            metrics=[f'ym:s:goal{goal_id}reaches', f'ym:s:goal{goal_id}conversionRate'],
            dimensions=dimensions,
            filter_expression=filter_expression,
            accuracy=accuracy,
        )
        for row in parse_metrika_report(payload, ['reaches', 'conversion_rate']):
            goals.append({
                'period_start': date_from.isoformat(),
                'period_end': date_to.isoformat(),
                'goal_id': goal_id,
                'goal_name': str(goal.get('name') or '').strip() or None,
                'goal_type': str(goal.get('type') or '').strip() or None,
                **row,
            })
    return landings, goals


def _goal_ids_from_environment() -> set[int] | None:
    raw = os.environ.get('YANDEX_METRIKA_GOAL_IDS', '').strip()
    if not raw:
        return None
    values = {int(value) for value in re.split(r'[\s,]+', raw) if value}
    if any(value < 1 for value in values):
        raise SeoError('YANDEX_METRIKA_GOAL_IDS must contain positive integers.')
    return values


def _local_today(config: dict) -> dt.date:
    return dt.datetime.now(configured_timezone(config['timezone'])).date()


def _record_run(
    store: AnalyticsStore,
    source: str,
    started: str,
    period_start: dt.date | None,
    period_end: dt.date | None,
    status: str,
    *,
    row_count: int | None = None,
    error: SourceFailure | None = None,
) -> str:
    run_id = str(uuid.uuid4())
    store.add_source_run(
        run_id=run_id,
        source=source,
        started_at=started,
        finished_at=iso_time(),
        period_start=period_start.isoformat() if period_start else None,
        period_end=period_end.isoformat() if period_end else None,
        status=status,
        row_count=row_count,
        error_code=error.code if error else None,
        error_message=str(error) if error else None,
    )
    return run_id


def sync_topvisor(config: dict, store: AnalyticsStore, date1: dt.date, date2: dt.date) -> dict:
    positions = config['positions']
    started = iso_time()
    try:
        api = TopvisorApi(
            os.environ.get('TOPVISOR_USER_ID', '').strip(),
            os.environ.get('TOPVISOR_API_KEY', '').strip(),
            positions['topvisor_project_id'],
            positions['topvisor_region_index'],
            positions['topvisor_volume_field'],
        )
        records = api.history(date1, date2)
        result = sync_topvisor_records(store, records, positions)
        _record_run(store, 'topvisor', started, date1, date2, 'ok', row_count=result['inserted'])
        return {'source': 'topvisor', 'status': 'ok', **result}
    except MissingCredentials as error:
        _record_run(store, 'topvisor', started, date1, date2, 'not_configured', error=error)
        return {'source': 'topvisor', 'status': 'not_configured', 'message': str(error)}
    except SourceFailure as error:
        _record_run(store, 'topvisor', started, date1, date2, 'error', error=error)
        return {'source': 'topvisor', 'status': 'error', 'message': str(error)}


def sync_webmaster(config: dict, store: AnalyticsStore, date1: dt.date, date2: dt.date) -> dict:
    started = iso_time()
    source_config = config['webmaster']
    try:
        api = YandexWebmasterApi(
            os.environ.get('YANDEX_WEBMASTER_TOKEN', '').strip()
            or os.environ.get('YANDEX_OAUTH_TOKEN', '').strip(),
        )
        targets = {normalize_query(row['keyword']): row['id'] for row in store.active_keywords()}
        rows = webmaster_rows(
            api,
            site_url=config['site_url'],
            host_id=os.environ.get('YANDEX_WEBMASTER_HOST_ID', '').strip(),
            date_from=date1,
            date_to=date2,
            device=str(source_config.get('device', 'ALL')),
            limit=int(source_config.get('limit', 500)),
            targets=targets,
        )
        run_id = _record_run(store, 'yandex_webmaster', started, date1, date2, 'ok', row_count=len(rows))
        store.add_webmaster_rows(run_id, iso_time(), rows)
        return {
            'source': 'yandex_webmaster', 'status': 'ok', 'rows': len(rows),
            'new_queries': sum(not row['is_target'] for row in rows),
        }
    except MissingCredentials as error:
        _record_run(store, 'yandex_webmaster', started, date1, date2, 'not_configured', error=error)
        return {'source': 'yandex_webmaster', 'status': 'not_configured', 'message': str(error)}
    except SourceFailure as error:
        _record_run(store, 'yandex_webmaster', started, date1, date2, 'error', error=error)
        return {'source': 'yandex_webmaster', 'status': 'error', 'message': str(error)}


def sync_metrika(config: dict, store: AnalyticsStore, date1: dt.date, date2: dt.date) -> dict:
    started = iso_time()
    source_config = config['metrika']
    try:
        api = YandexMetrikaApi(
            os.environ.get('YANDEX_METRIKA_TOKEN', '').strip()
            or os.environ.get('YANDEX_OAUTH_TOKEN', '').strip(),
            int(source_config['counter_id']),
        )
        landings, goals = collect_metrika_rows(
            api,
            date_from=date1,
            date_to=date2,
            filter_expression=str(source_config['filter']),
            accuracy=str(source_config.get('accuracy', 'full')),
            configured_goal_ids=_goal_ids_from_environment(),
        )
        run_id = _record_run(
            store, 'yandex_metrika', started, date1, date2, 'ok',
            row_count=len(landings) + len(goals),
        )
        fetched = iso_time()
        store.add_metrika_landings(run_id, fetched, landings)
        store.add_metrika_goals(run_id, fetched, goals)
        return {
            'source': 'yandex_metrika', 'status': 'ok',
            'landings': len(landings), 'goal_rows': len(goals),
        }
    except MissingCredentials as error:
        _record_run(store, 'yandex_metrika', started, date1, date2, 'not_configured', error=error)
        return {'source': 'yandex_metrika', 'status': 'not_configured', 'message': str(error)}
    except SourceFailure as error:
        _record_run(store, 'yandex_metrika', started, date1, date2, 'error', error=error)
        return {'source': 'yandex_metrika', 'status': 'error', 'message': str(error)}


def bootstrap_topvisor(config: dict, store: AnalyticsStore) -> dict:
    positions = config['positions']
    started = iso_time()
    records = load_topvisor_bootstrap(resolve_path(positions['bootstrap_path']))
    result = sync_topvisor_records(store, records, positions)
    dates = [dt.date.fromisoformat(record.measured_on) for record in records]
    _record_run(
        store, 'topvisor', started, min(dates), max(dates), 'ok',
        row_count=result['inserted'],
    )
    return result


def sync_all(config: dict, store: AnalyticsStore) -> list[dict]:
    today = _local_today(config)
    topvisor_days = int(config.get('topvisor_history_days', 365))
    webmaster_day = today - dt.timedelta(days=int(config.get('webmaster_lag_days', 3)))
    metrika_day = today - dt.timedelta(days=int(config.get('metrika_lag_days', 1)))
    return [
        sync_topvisor(config, store, today - dt.timedelta(days=topvisor_days), today),
        sync_webmaster(config, store, webmaster_day, webmaster_day),
        sync_metrika(config, store, metrika_day, metrika_day),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('init')
    subparsers.add_parser('bootstrap-topvisor')
    for command in ('sync-topvisor', 'sync-webmaster', 'sync-metrika'):
        sub = subparsers.add_parser(command)
        sub.add_argument('--date-from', type=dt.date.fromisoformat)
        sub.add_argument('--date-to', type=dt.date.fromisoformat)
    subparsers.add_parser('sync-all')
    args = parser.parse_args(argv)
    try:
        config = load_source_config()
        store = AnalyticsStore(config['database_path'])
        store.initialize()
        store.sync_keywords(load_keywords(config['positions']['keywords_path'], config['positions']))
        if args.command == 'init':
            print(f'Initialized SEO analytics database: {store.path}')
            return 0
        if args.command == 'bootstrap-topvisor':
            result = bootstrap_topvisor(config, store)
        elif args.command == 'sync-all':
            result = sync_all(config, store)
        else:
            today = _local_today(config)
            date1 = args.date_from or today
            date2 = args.date_to or date1
            if date2 < date1:
                raise SeoError('--date-to must not be earlier than --date-from.')
            if args.command == 'sync-topvisor':
                result = sync_topvisor(config, store, date1, date2)
            elif args.command == 'sync-webmaster':
                result = sync_webmaster(config, store, date1, date2)
            else:
                result = sync_metrika(config, store, date1, date2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        results: Iterable[dict] = result if isinstance(result, list) else [result]
        return int(any(item.get('status') == 'error' for item in results))
    except (SeoError, OSError, sqlite3.Error, ValueError) as error:
        print(f'SEO SOURCES FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
