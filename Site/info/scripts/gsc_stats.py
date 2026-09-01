"""Save Search Console metrics and the previous equal-length period; fail on API errors."""
import argparse
import datetime as dt
import sys

from gsc_curl import search_analytics_query
from seo_common import REPORTS_DIR, SeoError, settings, write_json


def date_range(days, lag=3, today=None):
    if days < 1 or lag < 1:
        raise SeoError('days and reporting lag must be positive.')
    end = (today or dt.date.today()) - dt.timedelta(days=lag)
    start = end - dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def get_totals(start, end):
    result = search_analytics_query(start, end, row_limit=1)
    if result.get('error'):
        raise SeoError('Search Console totals are unavailable; an API error is not zero traffic.')
    rows = result.get('rows', [])
    # A successful empty response means no returned data, not a measured zero.
    return rows[0] if rows else None


def collect(days, today=None):
    config = settings()
    start, end = date_range(days, config['reporting_lag_days'], today)
    previous_end = dt.date.fromisoformat(start) - dt.timedelta(days=1)
    previous_start = previous_end - dt.timedelta(days=days - 1)
    report = {'site': config['site_url'], 'property': config['gsc_property'], 'search_type': 'web',
              'data_state': 'final', 'period': [start, end],
              'previous_period': [previous_start.isoformat(), previous_end.isoformat()],
              'totals': get_totals(start, end), 'previous_totals': get_totals(previous_start.isoformat(), previous_end.isoformat())}
    for key, dimensions, limit in [('queries', ['query'], 1000), ('pages', ['page'], 1000), ('daily', ['date'], 500)]:
        result = search_analytics_query(start, end, dimensions, limit)
        if result.get('error'):
            raise SeoError(f'Search Console {key} are unavailable.')
        report[key] = result.get('rows', [])
    report['opportunities'] = [r for r in report['queries'] if 4 <= r.get('position', 0) <= 15]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('days', type=int, nargs='?', default=28, choices=range(1, 367), metavar='DAYS')
    args = parser.parse_args()
    try:
        report = collect(args.days)
        path = REPORTS_DIR / f'gsc-{dt.date.today()}-{args.days}d.json'
        write_json(path, report)
        totals = report['totals']
        print('Period: ' + ' to '.join(report['period']))
        print(f"Clicks: {totals['clicks']}; impressions: {totals['impressions']}" if totals else 'No data returned for this period.')
        print(f'Report: {path}')
        return 0
    except (SeoError, ValueError, OSError) as error:
        print(f'GSC REPORT FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
