import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bing_indexnow
import gsc_coverage
import gsc_curl
import gsc_stats
import seo_audit
import seo_common
import seo_telegram

ORIGIN = 'https://magiarnd.ru'
CONFIG = {'site_url': ORIGIN, 'sitemap_url': ORIGIN + '/sitemap.xml', 'gsc_property': 'sc-domain:magiarnd.ru', 'reporting_lag_days': 3}


class SeoTests(unittest.TestCase):
    def test_telegram_routes_seo_event_to_the_configured_topic(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {'ok': True, 'result': {'message_id': 1}}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_GROUP_CHAT_ID': '-1001234567890',
            'TELEGRAM_SEO_THREAD_ID': '84',
            'TELEGRAM_ALLOWED_USERS': '123, 456',
        }
        with patch.dict('os.environ', environment, clear=True):
            seo_telegram.send_event('daily', 'Проверка', post=post)

        self.assertEqual(sent['data']['chat_id'], '-1001234567890')
        self.assertEqual(sent['data']['message_thread_id'], '84')
        self.assertIn('Ежедневный SEO-отчёт', sent['data']['text'])

    def test_telegram_does_not_fall_back_to_legacy_chat_id(self):
        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_CHAT_ID': '-1009999999999',
            'TELEGRAM_SEO_THREAD_ID': '84',
        }
        with patch.dict('os.environ', environment, clear=True):
            with self.assertRaisesRegex(seo_telegram.TelegramError, 'TELEGRAM_GROUP_CHAT_ID'):
                seo_telegram.TelegramConfig.from_environment()

    def test_telegram_gateway_does_not_require_a_second_bot_token(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {'message': 'SEO notification accepted.'}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_GATEWAY_URL': 'https://worker.test',
            'TELEGRAM_GATEWAY_SECRET': 'seo-secret',
        }
        with patch.dict('os.environ', environment, clear=True):
            seo_telegram.send_event('wordstat', 'Проверка', post=post)

        self.assertEqual(sent['url'], 'https://worker.test/api/seo-notifications')
        self.assertEqual(sent['json_data'], {'kind': 'wordstat', 'message': 'Проверка'})
        self.assertEqual(sent['headers']['X-Bot-Api-Secret'], 'seo-secret')

    def test_telegram_gateway_uses_an_explicit_user_agent(self):
        class Response:
            status = 202

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            @staticmethod
            def read():
                return b'{"message":"SEO notification accepted."}'

        environment = {
            'TELEGRAM_GATEWAY_URL': 'https://worker.test',
            'TELEGRAM_GATEWAY_SECRET': 'seo-secret',
        }
        with patch.dict('os.environ', environment, clear=True), patch(
                'seo_telegram.urllib.request.urlopen', return_value=Response()) as urlopen:
            seo_telegram.send_event('daily', 'Проверка')

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header('User-agent'), 'Magic-SEO/1.0')

    def test_manual_telegram_request_requires_an_allowed_user(self):
        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_GROUP_CHAT_ID': '-1001234567890',
            'TELEGRAM_SEO_THREAD_ID': '84',
            'TELEGRAM_ALLOWED_USERS': '123',
        }
        with patch.dict('os.environ', environment, clear=True):
            with self.assertRaisesRegex(seo_telegram.TelegramError, 'not allowed'):
                seo_telegram.send_event('manual_check', 'Проверка', requested_by=999)

    def test_telegram_attaches_a_single_photo_via_sendphoto(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {'ok': True, 'result': {'message_id': 1}}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_GROUP_CHAT_ID': '-1001234567890',
            'TELEGRAM_SEO_THREAD_ID': '84',
        }
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / 'dashboard-7.png'
            photo.write_bytes(b'\x89PNG-fake-bytes')
            with patch.dict('os.environ', environment, clear=True):
                seo_telegram.send_event('weekly', 'Итоги недели', post=post, photos=[str(photo)])

        self.assertTrue(sent['url'].endswith('/sendPhoto'))
        multipart = sent['multipart']
        self.assertEqual(multipart['fields']['chat_id'], '-1001234567890')
        self.assertEqual(multipart['fields']['message_thread_id'], '84')
        self.assertIn('Еженедельный SEO-отчёт', multipart['fields']['caption'])
        filename, content, content_type = multipart['files']['photo']
        self.assertEqual(filename, 'dashboard-7.png')
        self.assertEqual(content, b'\x89PNG-fake-bytes')
        self.assertEqual(content_type, 'image/png')

    def test_telegram_attaches_multiple_photos_via_sendmediagroup(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {'ok': True, 'result': [{'message_id': 1}, {'message_id': 2}]}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_GROUP_CHAT_ID': '-1001234567890',
            'TELEGRAM_SEO_THREAD_ID': '84',
        }
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / 'dashboard-30-1.png'
            second = Path(tmp) / 'dashboard-30-2.png'
            first.write_bytes(b'one')
            second.write_bytes(b'two')
            with patch.dict('os.environ', environment, clear=True):
                seo_telegram.send_event(
                    'weekly', 'Итоги месяца', post=post, photos=[str(first), str(second)],
                )

        self.assertTrue(sent['url'].endswith('/sendMediaGroup'))
        media = json.loads(sent['multipart']['fields']['media'])
        self.assertEqual(len(media), 2)
        self.assertIn('caption', media[0])
        self.assertNotIn('caption', media[1])
        self.assertEqual(set(sent['multipart']['files']), {'photo0', 'photo1'})

    def test_telegram_gateway_base64_encodes_photos(self):
        import base64

        class Response:
            ok = True

            @staticmethod
            def json():
                return {'message': 'SEO notification accepted.'}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_GATEWAY_URL': 'https://worker.test',
            'TELEGRAM_GATEWAY_SECRET': 'seo-secret',
        }
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / 'daily.png'
            photo.write_bytes(b'daily-bytes')
            with patch.dict('os.environ', environment, clear=True):
                seo_telegram.send_event('daily', 'Сегодня', post=post, photos=[str(photo)])

        self.assertEqual(sent['url'], 'https://worker.test/api/seo-notifications')
        sent_photos = sent['json_data']['photos']
        self.assertEqual(len(sent_photos), 1)
        self.assertEqual(sent_photos[0]['filename'], 'daily.png')
        self.assertEqual(base64.b64decode(sent_photos[0]['base64']), b'daily-bytes')

    def test_telegram_missing_photo_path_falls_back_to_text(self):
        class Response:
            ok = True

            @staticmethod
            def json():
                return {'ok': True, 'result': {'message_id': 1}}

        sent = {}

        def post(url, **kwargs):
            sent.update(url=url, **kwargs)
            return Response()

        environment = {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_GROUP_CHAT_ID': '-1001234567890',
            'TELEGRAM_SEO_THREAD_ID': '84',
        }
        with patch.dict('os.environ', environment, clear=True):
            seo_telegram.send_event(
                'daily', 'Проверка', post=post, photos=['/no/such/file-anywhere.png'],
            )

        self.assertTrue(sent['url'].endswith('/sendMessage'))
        self.assertIn('data', sent)

    def test_empty_sitemap_is_an_error(self):
        with patch('seo_common.settings', return_value=CONFIG), patch('seo_common.fetch', return_value=(200, '<urlset/>', {}, '')):
            with self.assertRaisesRegex(seo_common.SeoError, 'zero URLs'):
                seo_common.sitemap_urls()

    def test_sitemap_index_and_xml_entities(self):
        documents = [
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://magiarnd.ru/pages.xml</loc></sitemap></sitemapindex>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://magiarnd.ru/?a=1&amp;b=2</loc></url></urlset>',
        ]
        with patch('seo_common.settings', return_value=CONFIG), patch('seo_common.fetch', side_effect=[(200, d, {}, '') for d in documents]):
            self.assertEqual(seo_common.sitemap_urls(), [ORIGIN + '/?a=1&b=2'])

    def test_foreign_sitemap_url_is_rejected(self):
        document = '<urlset><url><loc>https://other.example/</loc></url></urlset>'
        with patch('seo_common.settings', return_value=CONFIG), patch('seo_common.fetch', return_value=(200, document, {}, '')):
            with self.assertRaises(seo_common.SeoError):
                seo_common.sitemap_urls()

    def test_html_parser_handles_attribute_order_and_noindex(self):
        html = '<title>Magic</title><meta content="Repair" name="description"><link href="https://magiarnd.ru/" rel="canonical"><meta content="https://magiarnd.ru/" property="og:url"><h1>Repair</h1><script type="application/ld+json">{"@type":"Service"}</script>'
        self.assertEqual(seo_audit.inspect_page(ORIGIN + '/', html, {})['errors'], [])
        self.assertIn('Page in sitemap is marked noindex', seo_audit.inspect_page(ORIGIN + '/', html, {'X-Robots-Tag': 'noindex'})['errors'])
        page = seo_audit.inspect_page(ORIGIN + '/', html, {})
        self.assertEqual(page['h1_count'], 1)
        self.assertEqual(page['canonical'], ORIGIN + '/')
        self.assertEqual(page['schema_count'], 1)

    def test_http_error_is_not_zero_traffic(self):
        with patch('gsc_stats.search_analytics_query', return_value={'error': 'HTTP 403', 'rows': []}):
            with self.assertRaises(seo_common.SeoError):
                gsc_stats.get_totals('2026-08-01', '2026-08-28')

    def test_empty_success_is_marked_no_data(self):
        with patch('gsc_stats.search_analytics_query', return_value={'rows': []}):
            self.assertIsNone(gsc_stats.get_totals('2026-08-01', '2026-08-28'))

    def test_property_comes_from_configuration(self):
        with patch('gsc_curl.settings', return_value={**CONFIG, 'gsc_property': ORIGIN + '/'}):
            self.assertEqual(gsc_curl.site_url_for_endpoint(), (ORIGIN + '/', 'https%3A%2F%2Fmagiarnd.ru%2F'))

    def test_coverage_errors_are_not_queued_for_indexing(self):
        with patch('gsc_coverage.inspect_url', side_effect=[seo_common.SeoError('HTTP 403'), {'verdict': 'NEUTRAL', 'coverage': 'Discovered'}]), patch('gsc_coverage.time.sleep'):
            report = gsc_coverage.collect([ORIGIN + '/', ORIGIN + '/remont-vannoy'])
        self.assertFalse(report['complete'])
        self.assertEqual(report['errors'], 1)
        self.assertEqual(report['needs_review'], [ORIGIN + '/remont-vannoy'])

    def test_reporting_period_has_28_days_and_lag(self):
        start, end = gsc_stats.date_range(28, 3, dt.date(2026, 9, 1))
        self.assertEqual((start, end), ('2026-08-02', '2026-08-29'))
        self.assertEqual((dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days + 1, 28)

    def test_indexnow_preview_does_not_contact_api(self):
        with patch('bing_indexnow.fetch') as fetch:
            result = bing_indexnow.submit_urls([ORIGIN + '/'], submit=False)
            fetch.assert_not_called()
        self.assertFalse(result['submitted'])

    def test_indexnow_rejects_foreign_urls(self):
        with self.assertRaises(seo_common.SeoError):
            bing_indexnow.submit_urls(['https://digital-models.org/'])

    def test_indexnow_batches_do_not_drop_urls(self):
        urls = [f'{ORIGIN}/{i}' for i in range(10001)]
        self.assertEqual([len(batch) for batch in bing_indexnow.batches(urls)], [10000, 1])


if __name__ == '__main__':
    unittest.main()
