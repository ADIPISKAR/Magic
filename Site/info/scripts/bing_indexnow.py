"""Preview IndexNow URLs; use --submit explicitly after the pages are deployed."""
import argparse
import os
import re
import sys

from seo_common import SeoError, fetch, own_url, settings, sitemap_urls


def batches(urls, size=10000):
    for offset in range(0, len(urls), size):
        yield urls[offset:offset + size]


def submit_urls(urls, *, submit=False):
    config = settings()
    origin = config['site_url']
    urls = list(dict.fromkeys(urls))
    if not urls or any(not own_url(url, origin) for url in urls):
        raise SeoError('Supply one or more URLs on the configured site only.')
    if not submit:
        return {'submitted': False, 'urls': urls}
    key = os.environ.get('INDEXNOW_KEY', '')
    if not re.fullmatch(r'[a-zA-Z0-9-]{8,128}', key):
        raise SeoError('Set INDEXNOW_KEY to your own valid IndexNow key.')
    key_url = f'{origin}/{key}.txt'
    if fetch(key_url)[1].strip() != key:
        raise SeoError('The public IndexNow verification file does not match your key.')
    from urllib.parse import urlsplit
    results = []
    for batch in batches(urls):
        code, _, _, _ = fetch('https://api.indexnow.org/indexnow', payload={
            'host': urlsplit(origin).netloc, 'key': key, 'keyLocation': key_url, 'urlList': batch,
        })
        if code not in (200, 202):
            raise SeoError(f'Unexpected IndexNow status: {code}')
        results.append({'count': len(batch), 'status': code})
    return {'submitted': True, 'batches': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['sitemap', 'urls'])
    parser.add_argument('urls', nargs='*')
    parser.add_argument('--submit', action='store_true')
    args = parser.parse_args()
    try:
        urls = sitemap_urls() if args.mode == 'sitemap' else args.urls
        result = submit_urls(urls, submit=args.submit)
        if not result['submitted']:
            print('Preview only. No indexing requests sent. URLs:')
            print('\n'.join(result['urls']))
        else:
            print(result)
            print('200 = received; 202 = key validation pending. Neither guarantees indexing.')
        return 0
    except (SeoError, OSError, ValueError) as error:
        print(f'INDEXNOW FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
