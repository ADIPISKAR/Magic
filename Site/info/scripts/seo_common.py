"""Shared configuration, HTTP and sitemap parsing for Magic."""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
REPORTS_DIR = PROJECT_ROOT / 'storage' / 'app' / 'private' / 'seo-reports'


class SeoError(RuntimeError):
    pass


def settings():
    data = json.loads((SCRIPT_DIR / 'seo-settings.json').read_text(encoding='utf-8'))
    local = SCRIPT_DIR / 'seo-settings.local.json'
    if local.exists():
        data.update(json.loads(local.read_text(encoding='utf-8')))
    data['site_url'] = os.environ.get('SEO_SITE_URL', data['site_url']).rstrip('/')
    data['gsc_property'] = os.environ.get('GSC_PROPERTY', data['gsc_property'])
    parsed = urllib.parse.urlsplit(data['site_url'])
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise SeoError('site_url must be an HTTP(S) origin, without a path or credentials.')
    data['sitemap_url'] = data['site_url'] + '/sitemap.xml'
    return data


def own_url(url, origin):
    parsed, base = urllib.parse.urlsplit(url), urllib.parse.urlsplit(origin)
    return (parsed.scheme == base.scheme and parsed.netloc == base.netloc
            and not parsed.fragment and not parsed.username)


def fetch(url, *, payload=None, headers=None):
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    request_headers = {'User-Agent': 'Magic-SEO/1.0', **(headers or {})}
    if body is not None:
        request_headers['Content-Type'] = 'application/json'
    if shutil.which('curl.exe') or shutil.which('curl'):
        return curl_fetch(url, body, request_headers)
    request = urllib.request.Request(url, data=body, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status, response.read().decode('utf-8-sig'), dict(response.headers), response.url
    except urllib.error.HTTPError as error:
        raise SeoError(f'HTTP {error.code} from {urllib.parse.urlsplit(url).hostname}') from error
    except (urllib.error.URLError, TimeoutError, UnicodeError) as error:
        raise SeoError(f'Unable to read {url}: {type(error).__name__}') from error


def curl_fetch(url, body, headers):
    # Native curl avoids the intermittent Python TLS timeouts on this Windows host.
    # Headers are kept in a temporary file, not exposed in process arguments.
    with tempfile.TemporaryDirectory(prefix='magic-seo-') as directory:
        request_headers = Path(directory) / 'request-headers'
        response_headers = Path(directory) / 'response-headers'
        request_headers.write_text('\n'.join(f'{k}: {v}' for k, v in headers.items()), encoding='utf-8')
        command = [shutil.which('curl.exe') or shutil.which('curl'), '-sS',
                   '--connect-timeout', '10', '--max-time', '25',
                   '--header', '@' + str(request_headers), '--dump-header', str(response_headers),
                   '--write-out', '\n__MAGIC_META__%{http_code}|%{url_effective}', url]
        command += ['--location', '--max-redirs', '5'] if body is None else ['--data-binary', '@-']
        try:
            result = subprocess.run(command, input=body, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            raise SeoError(f'Request timed out: {url}') from error
        if result.returncode:
            raise SeoError(f'HTTP transport failed for {url} (curl exit {result.returncode})')
        content, marker, metadata = result.stdout.rpartition(b'\n__MAGIC_META__')
        if not marker:
            raise SeoError('Missing HTTP response status.')
        code, final_url = metadata.decode('utf-8').split('|', 1)
        code = int(code)
        if code >= 400:
            raise SeoError(f'HTTP {code} from {urllib.parse.urlsplit(url).hostname}')
        text = response_headers.read_text(encoding='utf-8', errors='replace')
        parsed_headers = {}
        for line in text.splitlines():
            if line.startswith('HTTP/'):
                parsed_headers = {}
            elif ':' in line:
                key, value = line.split(':', 1)
                parsed_headers[key.strip()] = value.strip()
        return code, content.decode('utf-8-sig'), parsed_headers, final_url


def fetch_url(url, origin, fetch_base=None):
    if not own_url(url, origin):
        raise SeoError(f'URL is outside the configured site: {url}')
    if not fetch_base:
        return url
    parsed = urllib.parse.urlsplit(url)
    return fetch_base.rstrip('/') + parsed.path + ('?' + parsed.query if parsed.query else '')


def sitemap_urls(sitemap_url=None, fetch_base=None):
    config = settings()
    origin = config['site_url']
    pending = [sitemap_url or config['sitemap_url']]
    visited, urls = set(), []
    while pending:
        current = pending.pop(0)
        if current in visited:
            continue
        if len(visited) >= 100:
            raise SeoError('Sitemap index exceeds the 100-file audit limit.')
        visited.add(current)
        text = fetch(fetch_url(current, origin, fetch_base))[1]
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            raise SeoError('Sitemap is not valid XML.') from error
        kind = root.tag.rsplit('}', 1)[-1]
        if kind not in ('sitemapindex', 'urlset'):
            raise SeoError('Expected a sitemapindex or urlset, not an HTML page.')
        for entry in root:
            location = next((n.text.strip() for n in entry if n.tag.rsplit('}', 1)[-1] == 'loc' and n.text), None)
            if not location or not own_url(location, origin):
                raise SeoError(f'Missing or foreign sitemap location: {location}')
            (pending if kind == 'sitemapindex' else urls).append(location)
    urls = list(dict.fromkeys(urls))
    if not urls:
        raise SeoError('Sitemap contains zero URLs. Audit aborted.')
    return urls


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
