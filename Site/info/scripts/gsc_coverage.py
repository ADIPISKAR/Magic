"""Inspect sitemap URLs. Unknown/error states are never reported as deindexing."""
import argparse
import datetime as dt
import sys
import time

from gsc_curl import inspect_url
from seo_common import REPORTS_DIR, SeoError, settings, sitemap_urls, write_json


def collect(urls):
    rows, needs_review, errors = [], [], 0
    for url in urls:
        try:
            status = inspect_url(url)
            if status['verdict'] in ('FAIL', 'NEUTRAL', 'PARTIAL'):
                needs_review.append(url)
            rows.append({'url': url, **status})
        except SeoError as error:
            rows.append({'url': url, 'verdict': 'ERROR', 'error': str(error)})
            errors += 1
        time.sleep(0.15)
    return {'site': settings()['site_url'], 'property': settings()['gsc_property'],
            'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'complete': errors == 0, 'errors': errors, 'pages': rows, 'needs_review': needs_review}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=200, help='Maximum inspections per run (not a quota bypass)')
    args = parser.parse_args()
    try:
        urls = sitemap_urls()
        if args.limit < 1 or len(urls) > args.limit:
            raise SeoError(f'{len(urls)} URLs exceed the configured inspection limit; nothing inspected.')
        report = collect(urls)
        # Partial/error reports must not replace the last successful snapshot.
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        path = REPORTS_DIR / (f'coverage-failed-{stamp}.json' if report['errors'] else 'coverage.json')
        write_json(path, report)
        print(f"Checked {len(urls)} URLs; errors: {report['errors']}; manual review: {len(report['needs_review'])}")
        print(f'Report: {path}')
        return int(report['errors'] > 0)
    except (SeoError, OSError, ValueError) as error:
        print(f'COVERAGE FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
