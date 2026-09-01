"""Search Console helpers. The historical filename remains for compatibility.

Only read-only APIs are used. Authentication and property never switch implicitly.
"""
import json
from urllib.parse import quote

from gsc_auth import get_credentials
from seo_common import SeoError, fetch, own_url, settings

_credentials = None


def get_access_token():
    global _credentials
    if _credentials is None or not _credentials.valid:
        _credentials = get_credentials()
    return _credentials.token


def api_post(url, payload):
    _, text, _, _ = fetch(url, payload=payload, headers={'Authorization': 'Bearer ' + get_access_token()})
    try:
        result = json.loads(text)
    except json.JSONDecodeError as error:
        raise SeoError('Google returned invalid JSON.') from error
    if 'error' in result:
        raise SeoError('Google API returned an error; no valid report was produced.')
    return result


def site_url_for_endpoint(endpoint=None):
    property_url = settings()['gsc_property']
    return property_url, quote(property_url, safe='')


def inspect_url(url):
    config = settings()
    if not own_url(url, config['site_url']):
        raise SeoError('Inspection URL is outside the configured site.')
    data = api_post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect', {
        'inspectionUrl': url, 'siteUrl': config['gsc_property'], 'languageCode': 'en-US',
    })
    index = data.get('inspectionResult', {}).get('indexStatusResult')
    if not isinstance(index, dict) or not index.get('verdict'):
        raise SeoError('Google returned no index status for the URL.')
    return {'verdict': index['verdict'], 'coverage': index.get('coverageState', 'unknown'),
            'last_crawl': index.get('lastCrawlTime'), 'google_canonical': index.get('googleCanonical'),
            'user_canonical': index.get('userCanonical')}


def search_analytics_query(start_date, end_date, dimensions=None, row_limit=50, start_row=0):
    _, encoded = site_url_for_endpoint()
    payload = {'startDate': start_date, 'endDate': end_date, 'rowLimit': row_limit,
               'startRow': start_row, 'type': 'web', 'dataState': 'final'}
    if dimensions:
        payload['dimensions'] = list(dimensions)
    return api_post(f'https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded}/searchAnalytics/query', payload)
