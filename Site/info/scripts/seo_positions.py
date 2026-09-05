"""Append-only position history for Magic's production keyword set.

Topvisor is the active source.  The Yandex Search API implementation remains in
this module as a disabled, explicitly selected reserve provider.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from seo_common import PROJECT_ROOT, SCRIPT_DIR, SeoError, settings


YANDEX_SEARCH_ENDPOINT = 'https://searchapi.api.cloud.yandex.net/v2/web/search'
VALID_STATUSES = {
    'found', 'not_found', 'request_error', 'rate_limited', 'captcha', 'api_error',
}
ERROR_STATUSES = VALID_STATUSES - {'found', 'not_found'}
EVENT_TYPES = {
    'NEW_TOP_3', 'NEW_TOP_10', 'NEW_TOP_20',
    'LEFT_TOP_3', 'LEFT_TOP_10', 'LEFT_TOP_20',
    'BIG_GROWTH', 'BIG_DROP', 'NEW_IN_SEARCH', 'DISAPPEARED_FROM_SEARCH',
}


@dataclass(frozen=True)
class Keyword:
    keyword: str
    category: str
    region: str
    region_id: int
    device: str


@dataclass(frozen=True)
class SearchDocument:
    url: str
    title: str = ''


@dataclass(frozen=True)
class PositionCheck:
    keyword: str
    category: str
    region: str
    device: str
    checked_at: str
    position: int | None
    found_url: str | None
    title: str | None
    status: str
    search_depth: int
    source: str
    error_code: str | None = None
    error_message: str | None = None

    def validate(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f'Unsupported position status: {self.status}')
        if self.search_depth < 1:
            raise ValueError('search_depth must be positive.')
        if self.status == 'found':
            if self.position is None or self.position < 1 or not self.found_url:
                raise ValueError('A found check requires a positive position and found_url.')
        elif self.position is not None or self.found_url is not None:
            raise ValueError('Only found checks may contain a position or found_url.')


class ProviderFailure(SeoError):
    def __init__(self, status: str, message: str, code: str | None = None):
        if status not in ERROR_STATUSES:
            raise ValueError(f'Provider failure must be an error status, got {status}.')
        super().__init__(message)
        self.status = status
        self.code = code


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_time(value: dt.datetime | None = None) -> str:
    value = value or utc_now()
    if value.tzinfo is None:
        raise ValueError('checked_at must be timezone-aware.')
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError(f'Timestamp has no timezone: {value}')
    return parsed.astimezone(dt.timezone.utc)


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_position_config() -> dict:
    data = settings()
    config = dict(data.get('positions') or {})
    required = {
        'database_path', 'keywords_path', 'region', 'region_id', 'device',
        'search_depth', 'source', 'big_move_threshold', 'comparison_tolerance_days',
    }
    missing = sorted(required - config.keys())
    if missing:
        raise SeoError('Missing position settings: ' + ', '.join(missing))
    config['site_url'] = data['site_url']
    config['database_path'] = str(resolve_path(os.environ.get(
        'SEO_POSITIONS_DB', config['database_path'],
    )))
    config['keywords_path'] = str(resolve_path(os.environ.get(
        'SEO_KEYWORDS_FILE', config['keywords_path'],
    )))
    config['region_id'] = int(os.environ.get('YANDEX_REGION_ID', config['region_id']))
    config['search_depth'] = int(os.environ.get(
        'SEO_POSITION_SEARCH_DEPTH', config['search_depth'],
    ))
    config['api_page_size'] = int(config.get('api_page_size', 100))
    config['device'] = os.environ.get('SEO_POSITION_DEVICE', config['device']).strip().lower()
    if not 1 <= config['search_depth'] <= 100:
        raise SeoError('SEO_POSITION_SEARCH_DEPTH must be between 1 and 100.')
    if not 1 <= config['api_page_size'] <= 100:
        raise SeoError('api_page_size must be between 1 and 100.')
    if config['device'] != 'desktop':
        raise SeoError('Stage B supports the configured desktop Yandex Search API profile only.')
    return config


def load_keywords(path: str | Path, config: dict | None = None) -> list[Keyword]:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise SeoError(f'Unable to read keyword file {path}: {error}') from error
    config = config or {}
    region = str(config.get('region', data.get('region', ''))).strip()
    region_id = int(config.get('region_id', data.get('region_id', 0)))
    device = str(config.get('device', data.get('device', ''))).strip().lower()
    if not region or region_id < 1 or not device:
        raise SeoError('Keyword metadata requires region, region_id and device.')
    result, seen = [], set()
    for number, row in enumerate(data.get('keywords') or [], 1):
        keyword = str(row.get('keyword', '')).strip()
        category = str(row.get('category', '')).strip()
        key = keyword.casefold()
        if not keyword or not category:
            raise SeoError(f'Keyword row {number} has no keyword or category.')
        if key in seen:
            raise SeoError(f'Duplicate keyword: {keyword}')
        seen.add(key)
        result.append(Keyword(keyword, category, region, region_id, device))
    if not result:
        raise SeoError('Keyword file contains zero queries.')
    return result


SCHEMA = """
CREATE TABLE IF NOT EXISTS seo_keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    device TEXT NOT NULL,
    topvisor_keyword_id INTEGER,
    frequency REAL,
    frequency_checked_at TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(keyword, region_id, device)
);

CREATE TABLE IF NOT EXISTS seo_position_checks (
    id INTEGER PRIMARY KEY,
    keyword_id INTEGER NOT NULL REFERENCES seo_keywords(id),
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    device TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    position INTEGER CHECK (position IS NULL OR position > 0),
    found_url TEXT,
    title TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('found', 'not_found', 'request_error', 'rate_limited', 'captcha', 'api_error')
    ),
    search_depth INTEGER NOT NULL CHECK (search_depth > 0),
    source TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    run_id TEXT NOT NULL,
    CHECK (
        (status = 'found' AND position IS NOT NULL AND found_url IS NOT NULL)
        OR
        (status <> 'found' AND position IS NULL AND found_url IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_position_checks_keyword_time
ON seo_position_checks(keyword_id, checked_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_position_checks_run
ON seo_position_checks(run_id);

CREATE TABLE IF NOT EXISTS seo_events (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL REFERENCES seo_position_checks(id),
    keyword_id INTEGER NOT NULL REFERENCES seo_keywords(id),
    event_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    previous_position INTEGER,
    current_position INTEGER,
    run_id TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(check_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_seo_events_time
ON seo_events(created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS seo_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS seo_position_checks_no_update
BEFORE UPDATE ON seo_position_checks
BEGIN
    SELECT RAISE(ABORT, 'seo_position_checks is append-only');
END;

CREATE TRIGGER IF NOT EXISTS seo_position_checks_no_delete
BEFORE DELETE ON seo_position_checks
BEGIN
    SELECT RAISE(ABORT, 'seo_position_checks is append-only');
END;
"""


class PositionStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        connection.execute('PRAGMA journal_mode = WAL')
        connection.execute('PRAGMA busy_timeout = 5000')
        return connection

    @contextmanager
    def session(self):
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.session() as connection:
            connection.executescript(SCHEMA)
            columns = {
                row['name'] for row in connection.execute('PRAGMA table_info(seo_keywords)')
            }
            migrations = {
                'topvisor_keyword_id': 'ALTER TABLE seo_keywords ADD COLUMN topvisor_keyword_id INTEGER',
                'frequency': 'ALTER TABLE seo_keywords ADD COLUMN frequency REAL',
                'frequency_checked_at': 'ALTER TABLE seo_keywords ADD COLUMN frequency_checked_at TEXT',
            }
            for column, statement in migrations.items():
                if column not in columns:
                    connection.execute(statement)

    def sync_keywords(self, keywords: Sequence[Keyword], now: dt.datetime | None = None) -> int:
        self.initialize()
        timestamp = iso_time(now)
        with self.session() as connection:
            connection.execute('UPDATE seo_keywords SET active = 0, updated_at = ?', (timestamp,))
            for item in keywords:
                connection.execute(
                    """INSERT INTO seo_keywords
                       (keyword, category, region, region_id, device, active, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                       ON CONFLICT(keyword, region_id, device) DO UPDATE SET
                           category = excluded.category,
                           region = excluded.region,
                           active = 1,
                           updated_at = excluded.updated_at""",
                    (item.keyword, item.category, item.region, item.region_id,
                     item.device, timestamp, timestamp),
                )
        return len(keywords)

    def active_keywords(self) -> list[sqlite3.Row]:
        self.initialize()
        with self.session() as connection:
            return connection.execute(
                'SELECT * FROM seo_keywords WHERE active = 1 ORDER BY id',
            ).fetchall()

    def previous_usable(self, keyword_id: int, before: str) -> sqlite3.Row | None:
        with self.session() as connection:
            return connection.execute(
                """SELECT * FROM seo_position_checks
                   WHERE keyword_id = ? AND checked_at < ?
                     AND status IN ('found', 'not_found')
                   ORDER BY checked_at DESC, id DESC LIMIT 1""",
                (keyword_id, before),
            ).fetchone()

    def add_check(self, keyword_id: int, check: PositionCheck, run_id: str) -> int:
        check.validate()
        with self.session() as connection:
            cursor = connection.execute(
                """INSERT INTO seo_position_checks
                   (keyword_id, category, region, device, checked_at, position,
                    found_url, title, status, search_depth, source, error_code,
                    error_message, run_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (keyword_id, check.category, check.region, check.device,
                 check.checked_at, check.position, check.found_url, check.title,
                 check.status, check.search_depth, check.source, check.error_code,
                 check.error_message, run_id),
            )
            return int(cursor.lastrowid)

    def measurement_exists(self, keyword_id: int, checked_at: str, source: str) -> bool:
        self.initialize()
        with self.session() as connection:
            return connection.execute(
                """SELECT 1 FROM seo_position_checks
                   WHERE keyword_id = ? AND checked_at = ? AND source = ? LIMIT 1""",
                (keyword_id, checked_at, source),
            ).fetchone() is not None

    def update_keyword_source_data(
        self,
        keyword_id: int,
        *,
        topvisor_keyword_id: int | None = None,
        frequency: float | int | None = None,
        frequency_checked_at: str | None = None,
        frequency_present: bool = False,
    ) -> None:
        self.initialize()
        assignments, values = [], []
        if topvisor_keyword_id is not None:
            assignments.append('topvisor_keyword_id = ?')
            values.append(topvisor_keyword_id)
        if frequency_present:
            assignments.extend(['frequency = ?', 'frequency_checked_at = ?'])
            values.extend([frequency, frequency_checked_at])
        if not assignments:
            return
        values.append(keyword_id)
        with self.session() as connection:
            connection.execute(
                f"UPDATE seo_keywords SET {', '.join(assignments)} WHERE id = ?",
                values,
            )

    def add_events(
        self,
        *,
        check_id: int,
        keyword_id: int,
        event_types: Sequence[str],
        created_at: str,
        previous_position: int | None,
        current_position: int | None,
        run_id: str,
        payload: dict | None = None,
    ) -> None:
        unknown = set(event_types) - EVENT_TYPES
        if unknown:
            raise ValueError('Unsupported SEO events: ' + ', '.join(sorted(unknown)))
        encoded = json.dumps(payload or {}, ensure_ascii=False, separators=(',', ':'))
        with self.session() as connection:
            for event_type in event_types:
                connection.execute(
                    """INSERT OR IGNORE INTO seo_events
                       (check_id, keyword_id, event_type, created_at,
                        previous_position, current_position, run_id, payload_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (check_id, keyword_id, event_type, created_at,
                     previous_position, current_position, run_id, encoded),
                )

    def latest_snapshot(self, at: str | None = None) -> list[dict]:
        self.initialize()
        cutoff = at or '9999-12-31T23:59:59+00:00'
        with self.session() as connection:
            rows = connection.execute(
                """SELECT k.id AS keyword_id, k.keyword, k.category, k.region,
                          k.region_id, k.device, k.topvisor_keyword_id, k.frequency,
                          k.frequency_checked_at, c.id AS check_id, c.checked_at,
                          c.position, c.found_url, c.title, c.status,
                          c.search_depth, c.source, c.error_code, c.error_message
                   FROM seo_keywords k
                   LEFT JOIN seo_position_checks c ON c.id = (
                       SELECT c2.id FROM seo_position_checks c2
                       WHERE c2.keyword_id = k.id AND c2.checked_at <= ?
                       ORDER BY c2.checked_at DESC, c2.id DESC LIMIT 1
                   )
                   WHERE k.active = 1 ORDER BY k.id""",
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]

    def period_baselines(
        self,
        keyword_ids: Sequence[int],
        target: dt.datetime,
        tolerance_days: int,
    ) -> dict[int, dict]:
        if not keyword_ids:
            return {}
        upper = iso_time(target)
        lower = iso_time(target - dt.timedelta(days=tolerance_days))
        result = {}
        with self.session() as connection:
            for keyword_id in keyword_ids:
                row = connection.execute(
                    """SELECT * FROM seo_position_checks
                       WHERE keyword_id = ? AND checked_at <= ? AND checked_at >= ?
                         AND status IN ('found', 'not_found')
                       ORDER BY checked_at DESC, id DESC LIMIT 1""",
                    (keyword_id, upper, lower),
                ).fetchone()
                if row:
                    result[keyword_id] = dict(row)
        return result

    def count_checks(self) -> int:
        self.initialize()
        with self.session() as connection:
            return int(connection.execute(
                'SELECT COUNT(*) FROM seo_position_checks',
            ).fetchone()[0])


def xml_text(element: ET.Element | None) -> str:
    return '' if element is None else ''.join(element.itertext()).strip()


def local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def child_by_name(element: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in element if local_name(child.tag) == name), None)


def parse_yandex_xml(payload: str) -> list[SearchDocument]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ProviderFailure('api_error', 'Yandex Search API returned invalid XML.') from error
    error_node = next((node for node in root.iter() if local_name(node.tag) == 'error'), None)
    if error_node is not None:
        message = xml_text(error_node) or 'Yandex Search API error.'
        status = 'captcha' if 'captcha' in message.casefold() else 'api_error'
        raise ProviderFailure(status, message, error_node.attrib.get('code'))
    documents = []
    for node in root.iter():
        if local_name(node.tag) != 'doc':
            continue
        url = xml_text(child_by_name(node, 'url'))
        if not url:
            continue
        documents.append(SearchDocument(
            url=url,
            title=xml_text(child_by_name(node, 'title')),
        ))
    return documents


class YandexSearchApi:
    def __init__(
        self,
        *,
        api_key: str,
        folder_id: str,
        region_id: int,
        page_size: int = 100,
        timeout: int = 30,
        max_retries: int = 3,
        opener: Callable = urllib.request.urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if not api_key or not folder_id:
            raise SeoError('YANDEX_SEARCH_API_KEY and YANDEX_FOLDER_ID are required.')
        self.api_key = api_key
        self.folder_id = folder_id
        self.region_id = int(region_id)
        self.page_size = int(page_size)
        self.timeout = timeout
        self.max_retries = max_retries
        self.opener = opener
        self.sleeper = sleeper

    def request_page(self, keyword: str, page: int, groups_on_page: int) -> list[SearchDocument]:
        body = {
            'query': {
                'searchType': 'SEARCH_TYPE_RU',
                'queryText': keyword,
                'familyMode': 'FAMILY_MODE_MODERATE',
                'fixTypoMode': 'FIX_TYPO_MODE_OFF',
            },
            'folderId': self.folder_id,
            'groupSpec': {
                'groupMode': 'GROUP_MODE_FLAT',
                'groupsOnPage': groups_on_page,
                'docsInGroup': 1,
            },
            'page': page,
            'l10n': 'LOCALIZATION_RU',
            # Region 39 is Rostov-on-Don. It stays configurable via YANDEX_REGION_ID.
            'region': str(self.region_id),
            'responseFormat': 'FORMAT_XML',
        }
        encoded = json.dumps(body, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            YANDEX_SEARCH_ENDPOINT,
            data=encoded,
            headers={
                'Authorization': 'Api-Key ' + self.api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'Magic-SEO/1.0',
            },
            method='POST',
        )
        response_body = self._read(request)
        try:
            envelope = json.loads(response_body.decode('utf-8'))
            raw = base64.b64decode(envelope['rawData'], validate=True).decode('utf-8')
        except (KeyError, ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise ProviderFailure('api_error', 'Invalid Yandex Search API response envelope.') from error
        return parse_yandex_xml(raw)

    def _read(self, request: urllib.request.Request) -> bytes:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    return response.read()
            except urllib.error.HTTPError as error:
                detail = error.read().decode('utf-8', errors='replace')[:500]
                if error.code == 429:
                    last_error = ProviderFailure('rate_limited', 'Yandex Search API rate limit.', '429')
                elif error.code in (401, 403):
                    raise ProviderFailure('api_error', 'Yandex Search API authorization failed.', str(error.code)) from error
                elif 'captcha' in detail.casefold():
                    raise ProviderFailure('captcha', 'Yandex returned a CAPTCHA response.', str(error.code)) from error
                else:
                    last_error = ProviderFailure('request_error', f'Yandex Search API HTTP {error.code}.', str(error.code))
                retryable = error.code == 429 or error.code == 408 or error.code >= 500
                if not retryable or attempt >= self.max_retries:
                    raise last_error from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_error = ProviderFailure('request_error', f'Yandex Search request failed: {type(error).__name__}.')
                if attempt >= self.max_retries:
                    raise last_error from error
            self.sleeper(min(2 ** attempt, 30))
        raise last_error or ProviderFailure('request_error', 'Yandex Search request failed.')

    def search(self, keyword: str, depth: int) -> list[SearchDocument]:
        documents, page = [], 0
        while len(documents) < depth:
            page_size = min(self.page_size, depth - len(documents))
            batch = self.request_page(keyword, page, page_size)
            documents.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
        return documents[:depth]


def host_matches(url: str, site_url: str) -> bool:
    host = (urllib.parse.urlsplit(url).hostname or '').casefold().rstrip('.')
    site_host = (urllib.parse.urlsplit(site_url).hostname or '').casefold().rstrip('.')
    return bool(host and site_host and (host == site_host or host.endswith('.' + site_host)))


def check_from_documents(
    keyword: Keyword,
    documents: Sequence[SearchDocument],
    *,
    site_url: str,
    checked_at: str,
    search_depth: int,
    source: str,
) -> PositionCheck:
    for position, document in enumerate(documents[:search_depth], 1):
        if host_matches(document.url, site_url):
            return PositionCheck(
                keyword.keyword, keyword.category, keyword.region, keyword.device,
                checked_at, position, document.url, document.title or None,
                'found', search_depth, source,
            )
    return PositionCheck(
        keyword.keyword, keyword.category, keyword.region, keyword.device,
        checked_at, None, None, None, 'not_found', search_depth, source,
    )


def position_change(previous: int | None, current: int | None) -> int | None:
    if previous is None or current is None:
        return None
    return previous - current


def generate_events(
    previous_status: str | None,
    previous_position: int | None,
    current_status: str,
    current_position: int | None,
    *,
    big_move_threshold: int = 5,
) -> list[str]:
    if previous_status is None or current_status in ERROR_STATUSES:
        return []
    if previous_status == 'not_found' and current_status == 'found':
        return ['NEW_IN_SEARCH']
    if previous_status == 'found' and current_status == 'not_found':
        return ['DISAPPEARED_FROM_SEARCH']
    if previous_status != 'found' or current_status != 'found':
        return []
    if previous_position is None or current_position is None:
        return []
    events = []
    for threshold in (3, 10, 20):
        if previous_position > threshold >= current_position:
            events.append(f'NEW_TOP_{threshold}')
        if previous_position <= threshold < current_position:
            events.append(f'LEFT_TOP_{threshold}')
    change = position_change(previous_position, current_position)
    if change is not None and change >= big_move_threshold:
        events.append('BIG_GROWTH')
    elif change is not None and change <= -big_move_threshold:
        events.append('BIG_DROP')
    return events


def run_check(
    store: PositionStore,
    keywords: Sequence[Keyword],
    provider,
    *,
    site_url: str,
    search_depth: int,
    source: str,
    big_move_threshold: int = 5,
    checked_at: dt.datetime | None = None,
    progress: Callable[[int, int, PositionCheck], None] | None = None,
) -> dict:
    checked = iso_time(checked_at)
    run_id = str(uuid.uuid4())
    store.sync_keywords(keywords, checked_at)
    rows = {row['keyword']: row for row in store.active_keywords()}
    counts = Counter()
    events_count = 0
    for index, keyword in enumerate(keywords, 1):
        row = rows[keyword.keyword]
        previous = store.previous_usable(row['id'], checked)
        try:
            documents = provider.search(keyword.keyword, search_depth)
            check = check_from_documents(
                keyword, documents, site_url=site_url, checked_at=checked,
                search_depth=search_depth, source=source,
            )
        except ProviderFailure as error:
            check = PositionCheck(
                keyword.keyword, keyword.category, keyword.region, keyword.device,
                checked, None, None, None, error.status, search_depth, source,
                error.code, str(error),
            )
        check_id = store.add_check(row['id'], check, run_id)
        event_types = generate_events(
            previous['status'] if previous else None,
            previous['position'] if previous else None,
            check.status,
            check.position,
            big_move_threshold=big_move_threshold,
        )
        store.add_events(
            check_id=check_id,
            keyword_id=row['id'],
            event_types=event_types,
            created_at=checked,
            previous_position=previous['position'] if previous else None,
            current_position=check.position,
            run_id=run_id,
            payload={'keyword': keyword.keyword, 'url': check.found_url},
        )
        counts[check.status] += 1
        events_count += len(event_types)
        if progress:
            progress(index, len(keywords), check)
    return {
        'run_id': run_id,
        'checked_at': checked,
        'checked': len(keywords),
        'found': counts['found'],
        'not_found': counts['not_found'],
        'errors': sum(counts[status] for status in ERROR_STATUSES),
        'events': events_count,
    }


def average(values: Iterable[int]) -> float | None:
    values = list(values)
    return None if not values else round(sum(values) / len(values), 2)


def summarize_snapshot(current_rows: Sequence[dict], baselines: dict[int, dict] | None = None) -> dict:
    baselines = baselines or {}
    found = [row for row in current_rows if row.get('status') == 'found']
    errors = [row for row in current_rows if row.get('status') in ERROR_STATUSES]
    unchecked = [row for row in current_rows if not row.get('status')]
    comparison = []
    appeared, disappeared = [], []
    for row in current_rows:
        before = baselines.get(row['keyword_id'])
        if not before:
            continue
        if row.get('status') == 'found' and before.get('status') == 'found':
            change = position_change(before.get('position'), row.get('position'))
            comparison.append({
                'keyword': row['keyword'],
                'category': row['category'],
                'before': before['position'],
                'current': row['position'],
                'change': change,
                'url': row.get('found_url'),
            })
        elif row.get('status') == 'found' and before.get('status') == 'not_found':
            appeared.append(row['keyword'])
        elif row.get('status') == 'not_found' and before.get('status') == 'found':
            disappeared.append(row['keyword'])
    changes = [row for row in comparison if row['change'] is not None]
    categories = {}
    for category in sorted({row['category'] for row in current_rows}):
        category_rows = [row for row in current_rows if row['category'] == category]
        category_found = [row for row in category_rows if row.get('status') == 'found']
        category_changes = [row['change'] for row in changes if row['category'] == category]
        categories[category] = {
            'total': len(category_rows),
            'found': len(category_found),
            'top10': sum(row['position'] <= 10 for row in category_found),
            'average_position': average(row['position'] for row in category_found),
            'average_change': average(category_changes),
        }
    comparable_before = average(row['before'] for row in comparison)
    comparable_current = average(row['current'] for row in comparison)
    return {
        'total': len(current_rows),
        'found': len(found),
        'top3': sum(row['position'] <= 3 for row in found),
        'top10': sum(row['position'] <= 10 for row in found),
        'top20': sum(row['position'] <= 20 for row in found),
        'top50': sum(row['position'] <= 50 for row in found),
        'not_found': sum(row.get('status') == 'not_found' for row in current_rows),
        'errors': len(errors),
        'unchecked': len(unchecked),
        'average_position': average(row['position'] for row in found),
        'average_before': comparable_before,
        'average_current_comparable': comparable_current,
        'average_change': (
            None if comparable_before is None or comparable_current is None
            else round(comparable_before - comparable_current, 2)
        ),
        'improved': sum(row['change'] > 0 for row in changes),
        'declined': sum(row['change'] < 0 for row in changes),
        'unchanged': sum(row['change'] == 0 for row in changes),
        'appeared': len(appeared),
        'disappeared': len(disappeared),
        'appeared_keywords': appeared,
        'disappeared_keywords': disappeared,
        'best_growth': sorted(
            (row for row in changes if row['change'] > 0),
            key=lambda row: (-row['change'], row['keyword']),
        ),
        'worst_drop': sorted(
            (row for row in changes if row['change'] < 0),
            key=lambda row: (row['change'], row['keyword']),
        ),
        'categories': categories,
    }


def build_summary(store: PositionStore, period_days: int, config: dict, at: str | None = None) -> dict:
    current = store.latest_snapshot(at)
    checked_times = [parse_time(row['checked_at']) for row in current if row.get('checked_at')]
    if not checked_times:
        summary = summarize_snapshot(current)
        summary.update({'period_days': period_days, 'checked_at': None, 'baseline_target': None})
        return summary
    anchor = max(checked_times)
    target = anchor - dt.timedelta(days=period_days)
    tolerance_map = config.get('comparison_tolerance_days') or {}
    tolerance = int(tolerance_map.get(str(period_days), max(1, min(period_days, 5))))
    baselines = store.period_baselines(
        [row['keyword_id'] for row in current], target, tolerance,
    )
    summary = summarize_snapshot(current, baselines)
    summary.update({
        'period_days': period_days,
        'checked_at': iso_time(anchor),
        'baseline_target': target.date().isoformat(),
        'baseline_count': len(baselines),
    })
    return summary


def keyword_history(store: PositionStore, keyword: str, config: dict) -> dict | None:
    current = next(
        (row for row in store.latest_snapshot() if row['keyword'].casefold() == keyword.casefold()),
        None,
    )
    if not current:
        return None
    result = {
        'keyword': current['keyword'],
        'category': current['category'],
        'current': {
            'checked_at': current.get('checked_at'),
            'status': current.get('status'),
            'position': current.get('position'),
            'found_url': current.get('found_url'),
        },
        'previous': None,
        'periods': {},
    }
    if not current.get('checked_at'):
        return result
    previous = store.previous_usable(current['keyword_id'], current['checked_at'])
    if previous:
        result['previous'] = {
            'checked_at': previous['checked_at'],
            'status': previous['status'],
            'position': previous['position'],
            'change': position_change(previous['position'], current.get('position')),
        }
    anchor = parse_time(current['checked_at'])
    tolerance_map = config.get('comparison_tolerance_days') or {}
    for days in (1, 3, 7, 30):
        target = anchor - dt.timedelta(days=days)
        tolerance = int(tolerance_map.get(str(days), max(1, min(days, 5))))
        baseline = store.period_baselines([current['keyword_id']], target, tolerance).get(
            current['keyword_id'],
        )
        result['periods'][days] = None if not baseline else {
            'checked_at': baseline['checked_at'],
            'status': baseline['status'],
            'position': baseline['position'],
            'change': position_change(baseline['position'], current.get('position')),
        }
    return result


def signed(value: float | int | None) -> str:
    if value is None:
        return '—'
    return f'{value:+g}'


def format_telegram_report(summary: dict) -> str:
    days = summary['period_days']
    lines = [
        '🔎 Позиции сайта',
        f'Период: {days} дн.',
        '',
        f"Всего запросов: {summary['total']}",
        '',
        f"TOP-3: {summary['top3']}",
        f"TOP-10: {summary['top10']}",
        f"TOP-20: {summary['top20']}",
        f"TOP-50: {summary['top50']}",
        f"Не найдено: {summary['not_found']}",
    ]
    if summary['errors']:
        lines.append(f"Ошибки проверки: {summary['errors']}")
    if summary['unchecked']:
        lines.append(f"Ещё не проверено: {summary['unchecked']}")
    lines.extend(['', 'Средняя позиция:'])
    if summary['average_before'] is None:
        lines.append(str(summary['average_position'] if summary['average_position'] is not None else '—'))
    else:
        lines.append(
            f"{summary['average_before']:g} → {summary['average_current_comparable']:g} "
            f"({signed(summary['average_change'])})"
        )
    lines.extend([
        '',
        f"🔥 Выросло: {summary['improved']}",
        f"📉 Упало: {summary['declined']}",
        f"➖ Без изменений: {summary['unchanged']}",
        f"🆕 Появилось: {summary['appeared']}",
        f"❌ Пропало: {summary['disappeared']}",
    ])
    if summary['best_growth']:
        lines.extend(['', '🔥 Лучший рост'])
        for row in summary['best_growth'][:5]:
            lines.append(
                f"{row['keyword']}\n{row['before']} → {row['current']}\n{signed(row['change'])}"
            )
    if summary['worst_drop']:
        lines.extend(['', '📉 Падение'])
        for row in summary['worst_drop'][:5]:
            lines.append(
                f"{row['keyword']}\n{row['before']} → {row['current']}\n{signed(row['change'])}"
            )
    return '\n'.join(lines)


def provider_from_environment(config: dict) -> YandexSearchApi:
    reserve = config.get('yandex_search_api') or {}
    if not reserve.get('enabled'):
        raise SeoError('Yandex Search API reserve provider is disabled in seo-settings.json.')
    return YandexSearchApi(
        api_key=os.environ.get('YANDEX_SEARCH_API_KEY', '').strip(),
        folder_id=os.environ.get('YANDEX_FOLDER_ID', '').strip(),
        region_id=config['region_id'],
        page_size=int(reserve.get('api_page_size', config.get('api_page_size', 100))),
    )


def command_init(config: dict) -> int:
    keywords = load_keywords(config['keywords_path'], config)
    store = PositionStore(config['database_path'])
    count = store.sync_keywords(keywords)
    categories = Counter(keyword.category for keyword in keywords)
    print(f'Initialized {count} keywords in {store.path}')
    print('Categories: ' + ', '.join(f'{name}={amount}' for name, amount in categories.items()))
    print(f"Region: {config['region']} [{config['region_id']}], device: {config['device']}")
    return 0


def command_check_yandex(config: dict) -> int:
    keywords = load_keywords(config['keywords_path'], config)
    try:
        provider = provider_from_environment(config)
    except SeoError as error:
        print(f'POSITIONS CHECK ABORTED: {error}', file=sys.stderr)
        print('No position rows were written.', file=sys.stderr)
        return 2
    store = PositionStore(config['database_path'])
    result = run_check(
        store,
        keywords,
        provider,
        site_url=config['site_url'],
        search_depth=config['search_depth'],
        source=(config.get('yandex_search_api') or {}).get('source', 'yandex_search_api_v2'),
        big_move_threshold=int(config['big_move_threshold']),
        progress=lambda done, total, check: print(
            f'[{done}/{total}] {check.status}: {check.keyword}',
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result['errors'] > 0)


def command_report(config: dict, period_days: int) -> int:
    store = PositionStore(config['database_path'])
    print(format_telegram_report(build_summary(store, period_days, config)))
    return 0


def command_keyword(config: dict, keyword: str) -> int:
    history = keyword_history(PositionStore(config['database_path']), keyword, config)
    if history is None:
        print(f'Unknown active keyword: {keyword}', file=sys.stderr)
        return 1
    print(json.dumps(history, ensure_ascii=False, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('init', help='Create the separate SQLite database and sync keywords')
    subparsers.add_parser(
        'check-yandex-reserve',
        help='Run the disabled reserve Yandex Search API provider explicitly',
    )
    report = subparsers.add_parser('report', help='Build a local Telegram-ready period report')
    report.add_argument('--days', type=int, choices=(1, 3, 7, 30), default=7)
    keyword_parser = subparsers.add_parser('keyword', help='Show current/previous/3/7/30 day history')
    keyword_parser.add_argument('keyword')
    args = parser.parse_args(argv)
    try:
        config = load_position_config()
        if args.command == 'init':
            return command_init(config)
        if args.command == 'check-yandex-reserve':
            return command_check_yandex(config)
        if args.command == 'keyword':
            return command_keyword(config, args.keyword)
        return command_report(config, args.days)
    except (SeoError, OSError, sqlite3.Error, ValueError) as error:
        print(f'POSITIONS FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
