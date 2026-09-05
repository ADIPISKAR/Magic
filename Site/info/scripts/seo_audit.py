"""Audit rendered URLs in Magic's dynamic sitemap; no Google account needed."""
import argparse
import datetime
import json
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from seo_common import REPORTS_DIR, SeoError, fetch, fetch_url, settings, sitemap_urls, write_json


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.description, self.canonicals = '', [], []
        self.h1, self.robots, self.schemas = 0, [], []
        self.in_title, self.in_json, self.json_buffer = False, False, ''
        self.og = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            name = attrs.get('name', '').lower()
            if name == 'description':
                self.description.append(attrs.get('content', '').strip())
            if name in ('robots', 'googlebot', 'yandex'):
                self.robots.append(attrs.get('content', '').lower())
            if attrs.get('property', '').startswith('og:'):
                self.og[attrs['property']] = attrs.get('content', '')
        if tag == 'link' and 'canonical' in attrs.get('rel', '').lower().split():
            self.canonicals.append(attrs.get('href', ''))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json, self.json_buffer = True, ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_json:
            self.schemas.append(self.json_buffer)
            self.in_json = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_json:
            self.json_buffer += data


def inspect_page(url, body, headers):
    page = Page()
    page.feed(body)
    page.title = page.title.strip()
    errors, warnings = [], []
    if not page.title:
        errors.append('Missing title')
    if len(page.description) != 1 or not page.description[0]:
        errors.append('Expected one nonempty meta description')
    if page.h1 != 1:
        errors.append(f'Expected one H1, found {page.h1}')
    if page.canonicals != [url]:
        errors.append('Canonical must match the sitemap URL exactly')
    robots = ','.join(page.robots + [v.lower() for k, v in headers.items() if k.lower() == 'x-robots-tag'])
    if 'noindex' in robots or 'none' in robots:
        errors.append('Page in sitemap is marked noindex')
    if page.og.get('og:url') != url:
        errors.append('og:url differs from the canonical URL')
    if not page.schemas:
        warnings.append('No JSON-LD found')
    for schema in page.schemas:
        try:
            json.loads(schema)
        except json.JSONDecodeError:
            errors.append('Invalid JSON-LD')
    if len(page.title) > 70:
        warnings.append('Long title; review the snippet (not an indexing error)')
    return {
        'url': url,
        'title': page.title,
        'description': page.description[0] if page.description else '',
        'h1_count': page.h1,
        'canonical': page.canonicals[0] if len(page.canonicals) == 1 else None,
        'robots': robots or None,
        'schema_count': len(page.schemas),
        'errors': errors,
        'warnings': warnings,
    }


def audit(fetch_base=None):
    origin = settings()['site_url']
    urls = sitemap_urls(fetch_base=fetch_base)
    rows = []
    for url in urls:
        try:
            target = fetch_url(url, origin, fetch_base)
            status, body, headers, final_url = fetch(target)
            row = inspect_page(url, body, headers)
            row.update({
                'http_status': status,
                'final_url': final_url,
                'sitemap_included': True,
            })
            if status != 200 or final_url != target:
                row['errors'].append(f'Expected direct HTTP 200; received {status}, final URL {final_url}')
            row['indexable'] = status == 200 and final_url == target and not any(
                marker in (row.get('robots') or '') for marker in ('noindex', 'none')
            )
        except SeoError as error:
            row = {
                'url': url, 'title': '', 'description': '', 'h1_count': None,
                'canonical': None, 'robots': None, 'schema_count': None,
                'http_status': None, 'final_url': None, 'sitemap_included': True,
                'indexable': None, 'errors': [str(error)], 'warnings': [],
            }
        rows.append(row)
    for field in ('title', 'description'):
        groups = defaultdict(list)
        for row in rows:
            if row[field]:
                groups[row[field]].append(row)
        for group in groups.values():
            if len(group) > 1:
                for row in group:
                    row['errors'].append(f'Duplicate {field}')
    return {'site': origin, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'fetch_base': fetch_base, 'pages_checked': len(rows), 'pages': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-base', help='Fetch a local preview while validating production canonicals')
    parser.add_argument('--output', type=Path, default=REPORTS_DIR / 'audit.json')
    args = parser.parse_args()
    try:
        report = audit(args.fetch_base)
        write_json(args.output, report)
    except (SeoError, OSError, ValueError) as error:
        print(f'AUDIT FAILED: {error}', file=sys.stderr)
        return 1
    for row in report['pages']:
        print(('FAIL' if row['errors'] else 'OK') + ' ' + row['url'])
        for error in row['errors']:
            print('  ERROR: ' + error)
        for warning in row['warnings']:
            print('  NOTE: ' + warning)
    print(f"Checked {report['pages_checked']} pages. Report: {args.output}")
    return int(any(row['errors'] for row in report['pages']))


if __name__ == '__main__':
    sys.exit(main())
