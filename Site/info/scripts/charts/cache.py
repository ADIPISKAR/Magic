"""On-disk PNG cache for generated charts.

Charts are named ``{report_type}-{period}-{data_version}.png``. As long as
the underlying data hasn't changed (same ``data_version``), a Telegram
button press reuses the existing file instead of re-rendering a heavy
composite dashboard. Once new data lands, ``data_version`` changes and the
old file for that (report_type, period) is removed.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Callable

from seo_sources import AnalyticsStore


_CHARTS_DIR = Path(__file__).resolve().parent


def _render_version() -> str:
    """Hash of the rendering code itself.

    Without this the cache key is data-only, so restyling a chart keeps
    serving the previously rendered PNGs until new data happens to land.
    """
    digest = hashlib.sha1()
    for source in sorted(_CHARTS_DIR.glob('*.py')):
        digest.update(source.read_bytes())
    return digest.hexdigest()[:8]


def compute_data_version(store: AnalyticsStore) -> str:
    """A short hash that changes whenever any analytics table gets new rows,
    or whenever the chart rendering code changes."""
    with store.session() as connection:
        parts = []
        for table, column in (
            ('seo_position_checks', 'id'),
            ('seo_events', 'id'),
            ('seo_webmaster_queries', 'id'),
            ('seo_metrika_landings', 'id'),
            ('seo_metrika_goals', 'id'),
            ('seo_keywords', 'updated_at'),
        ):
            try:
                value = connection.execute(f'SELECT MAX({column}) FROM {table}').fetchone()[0]
            except sqlite3.Error:
                value = None
            parts.append(f'{table}:{value}')
    parts.append(f'render:{_render_version()}')
    digest = hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()
    return digest[:12]


def cached_path(charts_dir: str | Path, report_type: str, period: str, version: str) -> Path:
    return Path(charts_dir) / f'{report_type}-{period}-{version}.png'


def render_cached(
    charts_dir: str | Path, report_type: str, period: str, version: str,
    render_fn: Callable[[Path], None],
) -> Path:
    """Return the cached PNG for (report_type, period, version), rendering it
    if missing, and removing stale versions of the same (report_type, period).
    """
    target = cached_path(charts_dir, report_type, period, version)
    if target.exists():
        return target
    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)
    prefix = f'{report_type}-{period}-'
    for stale in charts_dir.glob(f'{prefix}*.png'):
        if stale.name != target.name:
            try:
                stale.unlink()
            except OSError:
                pass
    render_fn(target)
    return target
