"""Telegram transport for Magic SEO reports and alerts."""
import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path


EVENT_TITLES = {
    'daily': 'Ежедневный SEO-отчёт',
    'weekly': 'Еженедельный SEO-отчёт',
    'position_change': 'Изменение позиций',
    'top10_entry': 'Вход в TOP-10',
    'top10_exit': 'Выход из TOP-10',
    'strong_growth': 'Сильный рост',
    'strong_drop': 'Сильное падение',
    'metrika': 'Яндекс Метрика',
    'wordstat': 'Wordstat',
    'service_error': 'Ошибка SEO-сервиса',
    'manual_check': 'Ручная SEO-проверка',
    'other': 'SEO-уведомление',
    'test': 'Проверка SEO-уведомлений',
}


class TelegramError(RuntimeError):
    pass


class _Response:
    def __init__(self, status, body):
        self.ok = 200 <= status < 300
        self.body = body

    def json(self):
        return json.loads(self.body.decode('utf-8-sig'))


def _encode_multipart(multipart):
    """Hand-rolled multipart/form-data body -- no third-party HTTP dependency
    is used anywhere in this pipeline, so this stays on the stdlib too."""
    boundary = 'MagicSEOBoundary' + uuid.uuid4().hex
    parts = []
    for name, value in (multipart.get('fields') or {}).items():
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(str(value).encode('utf-8'))
        parts.append(b'\r\n')
    for name, (filename, content, content_type) in (multipart.get('files') or {}).items():
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f'Content-Type: {content_type}\r\n\r\n'.encode())
        parts.append(content)
        parts.append(b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts), f'multipart/form-data; boundary={boundary}'


def _post(url, *, data=None, json_data=None, multipart=None, headers=None, timeout):
    provided = [value for value in (data, json_data, multipart) if value is not None]
    if len(provided) != 1:
        raise ValueError('Exactly one request body must be provided.')
    if multipart is not None:
        body, content_type = _encode_multipart(multipart)
    elif data is not None:
        body = urllib.parse.urlencode(data).encode('utf-8')
        content_type = 'application/x-www-form-urlencoded'
    else:
        body = json.dumps(json_data, ensure_ascii=False).encode('utf-8')
        content_type = 'application/json; charset=utf-8'
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': content_type,
            'User-Agent': 'Magic-SEO/1.0',
            **(headers or {}),
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=max(timeout)) as response:
            return _Response(response.status, response.read())
    except urllib.error.HTTPError as error:
        return _Response(error.code, error.read())
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise TelegramError(f'Telegram request failed: {type(error).__name__}') from error


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise TelegramError(f'{name} is required.')
    return value


def _identifier(name, *, positive=False):
    value = _required(name)
    if not re.fullmatch(r'-?\d+', value) or (positive and int(value) < 1):
        qualifier = 'a positive integer' if positive else 'an integer'
        raise TelegramError(f'{name} must be {qualifier}.')
    return value


def _allowed_users(value):
    if not value.strip():
        return frozenset()
    users = set()
    for item in re.split(r'[\s,]+', value.strip()):
        if not item.isdigit() or int(item) < 1:
            raise TelegramError('TELEGRAM_ALLOWED_USERS must contain positive numeric IDs.')
        users.add(int(item))
    return frozenset(users)


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    group_chat_id: str
    seo_thread_id: str
    gateway_url: str
    gateway_secret: str
    allowed_users: frozenset[int]

    @classmethod
    def from_environment(cls):
        gateway_url = os.environ.get('TELEGRAM_GATEWAY_URL', '').strip().rstrip('/')
        gateway_secret = os.environ.get('TELEGRAM_GATEWAY_SECRET', '').strip()
        if gateway_url or gateway_secret:
            parsed = urllib.parse.urlsplit(gateway_url)
            if not gateway_url or not gateway_secret:
                raise TelegramError('TELEGRAM_GATEWAY_URL and TELEGRAM_GATEWAY_SECRET are both required.')
            if (parsed.scheme not in ('http', 'https') or not parsed.netloc
                    or parsed.username or parsed.password or parsed.path not in ('', '/')
                    or parsed.query or parsed.fragment):
                raise TelegramError('TELEGRAM_GATEWAY_URL must be an HTTP(S) origin without credentials.')
            return cls(
                token='',
                group_chat_id='',
                seo_thread_id='',
                gateway_url=gateway_url,
                gateway_secret=gateway_secret,
                allowed_users=_allowed_users(os.environ.get('TELEGRAM_ALLOWED_USERS', '')),
            )
        return cls(
            token=_required('TELEGRAM_BOT_TOKEN'),
            group_chat_id=_identifier('TELEGRAM_GROUP_CHAT_ID'),
            seo_thread_id=_identifier('TELEGRAM_SEO_THREAD_ID', positive=True),
            gateway_url='',
            gateway_secret='',
            allowed_users=_allowed_users(os.environ.get('TELEGRAM_ALLOWED_USERS', '')),
        )

    def user_is_allowed(self, user_id):
        return int(user_id) in self.allowed_users


class TelegramNotifier:
    def __init__(self, config, post=None):
        self.config = config
        self.post = post or _post

    def send_event(self, kind, message, *, photos=None):
        """``photos``: optional list of PNG file paths to attach -- the
        weekly/daily reports use this so the group topic gets the same
        dashboard image the private bot sends, not a text wall (spec
        sections 11-12). A missing or unreadable path is skipped, never
        fatal: the text notification still goes out.
        """
        if kind not in EVENT_TITLES:
            raise TelegramError(f'Unknown SEO notification kind: {kind}')
        body = str(message).strip()
        if not body:
            raise TelegramError('Telegram message must not be empty.')

        # Keep room below Telegram's 4096-character limit after entity parsing.
        if len(body) > 3200:
            body = body[:3199].rstrip() + '…'
        existing_photos = [
            path for path in (Path(p) for p in (photos or []) if p) if path.is_file()
        ]
        try:
            if self.config.gateway_url:
                payload_json = {'kind': kind, 'message': body}
                if existing_photos:
                    payload_json['photos'] = [
                        {
                            'base64': base64.b64encode(path.read_bytes()).decode('ascii'),
                            'filename': path.name,
                        }
                        for path in existing_photos[:10]
                    ]
                response = self.post(
                    self.config.gateway_url + '/api/seo-notifications',
                    json_data=payload_json,
                    headers={'X-Bot-Api-Secret': self.config.gateway_secret},
                    timeout=(10, 60) if existing_photos else (5, 20),
                )
            else:
                text = f'<b>{html.escape(EVENT_TITLES[kind])}</b>\n\n{html.escape(body)}'
                if not existing_photos:
                    response = self.post(
                        f'https://api.telegram.org/bot{self.config.token}/sendMessage',
                        data={
                            'chat_id': self.config.group_chat_id,
                            'message_thread_id': self.config.seo_thread_id,
                            'text': text,
                            'parse_mode': 'HTML',
                            'disable_web_page_preview': 'true',
                        },
                        timeout=(5, 20),
                    )
                elif len(existing_photos) == 1:
                    photo = existing_photos[0]
                    response = self.post(
                        f'https://api.telegram.org/bot{self.config.token}/sendPhoto',
                        multipart={
                            'fields': {
                                'chat_id': self.config.group_chat_id,
                                'message_thread_id': self.config.seo_thread_id,
                                'caption': text,
                                'parse_mode': 'HTML',
                            },
                            'files': {'photo': (photo.name, photo.read_bytes(), 'image/png')},
                        },
                        timeout=(10, 60),
                    )
                else:
                    # Telegram doesn't accept a caption or reply_markup on a
                    # media group as a whole -- the caption goes on the first
                    # image only, same convention as the Telegram bot side.
                    media, files = [], {}
                    for index, photo in enumerate(existing_photos[:10]):
                        attach_name = f'photo{index}'
                        files[attach_name] = (photo.name, photo.read_bytes(), 'image/png')
                        entry = {'type': 'photo', 'media': f'attach://{attach_name}'}
                        if index == 0:
                            entry['caption'] = text
                            entry['parse_mode'] = 'HTML'
                        media.append(entry)
                    response = self.post(
                        f'https://api.telegram.org/bot{self.config.token}/sendMediaGroup',
                        multipart={
                            'fields': {
                                'chat_id': self.config.group_chat_id,
                                'message_thread_id': self.config.seo_thread_id,
                                'media': json.dumps(media, ensure_ascii=False),
                            },
                            'files': files,
                        },
                        timeout=(10, 60),
                    )
            payload = response.json()
        except (json.JSONDecodeError, UnicodeError, ValueError) as error:
            raise TelegramError(f'Telegram request failed: {type(error).__name__}') from error
        if not isinstance(payload, dict):
            raise TelegramError('Telegram rejected the SEO notification: invalid API response')
        accepted = (payload.get('message') == 'SEO notification accepted.'
                    if self.config.gateway_url else payload.get('ok'))
        if not response.ok or not accepted:
            description = payload.get('description', 'unknown Telegram API error') if isinstance(payload, dict) else 'invalid Telegram API response'
            raise TelegramError(f'Telegram rejected the SEO notification: {description}')
        return payload.get('result', {})


def send_event(kind, message, *, requested_by=None, post=None, photos=None):
    config = TelegramConfig.from_environment()
    if requested_by is not None and not config.user_is_allowed(requested_by):
        raise TelegramError('The requesting Telegram user is not allowed.')
    return TelegramNotifier(config, post=post).send_event(kind, message, photos=photos)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=EVENT_TITLES)
    parser.add_argument('message', nargs='?', help='Notification text')
    parser.add_argument('--requested-by', type=int, help='Validate a manual request against TELEGRAM_ALLOWED_USERS')
    parser.add_argument('--dry-run', action='store_true', help='Validate routing without contacting Telegram')
    parser.add_argument('--photo', action='append', default=[], help='PNG path to attach; repeatable')
    args = parser.parse_args()
    message = args.message or ('Тестовая доставка в тему SEO.' if args.kind == 'test' else '')
    try:
        config = TelegramConfig.from_environment()
        if args.requested_by is not None and not config.user_is_allowed(args.requested_by):
            raise TelegramError('The requesting Telegram user is not allowed.')
        if args.dry_run:
            route = (f'gateway={config.gateway_url}' if config.gateway_url else
                     f'chat_id={config.group_chat_id}, message_thread_id={config.seo_thread_id}')
            print(f'Route valid: {route}')
            return 0
        TelegramNotifier(config).send_event(args.kind, message, photos=args.photo)
        print('SEO notification delivered.')
        return 0
    except TelegramError as error:
        print(f'SEO TELEGRAM FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
