import base64
import datetime as dt
import json
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import seo_positions


UTC = dt.timezone.utc


def keyword(text='ремонт квартир ростов-на-дону', category='Главная'):
    return seo_positions.Keyword(text, category, 'Ростов-на-Дону', 39, 'desktop')


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = seo_positions.PositionStore(Path(self.temporary.name) / 'positions.sqlite3')
        self.keyword = keyword()
        self.store.sync_keywords([self.keyword], dt.datetime(2026, 8, 1, tzinfo=UTC))
        self.keyword_id = self.store.active_keywords()[0]['id']

    def tearDown(self):
        self.temporary.cleanup()

    def add_check(self, when, status, position=None, category='Главная'):
        found_url = 'https://magiarnd.ru/remont-kvartir' if status == 'found' else None
        check = seo_positions.PositionCheck(
            self.keyword.keyword,
            category,
            self.keyword.region,
            self.keyword.device,
            seo_positions.iso_time(when),
            position,
            found_url,
            'Магия' if status == 'found' else None,
            status,
            100,
            'test',
            'TEST' if status in seo_positions.ERROR_STATUSES else None,
            'failure' if status in seo_positions.ERROR_STATUSES else None,
        )
        return self.store.add_check(self.keyword_id, check, 'run-' + when.date().isoformat())

    def test_position_change_uses_seo_sign(self):
        self.assertEqual(seo_positions.position_change(18, 9), 9)
        self.assertEqual(seo_positions.position_change(9, 18), -9)
        self.assertIsNone(seo_positions.position_change(None, 18))

    def test_top_buckets_average_not_found_and_errors(self):
        rows = [
            {'keyword_id': 1, 'keyword': 'a', 'category': 'A', 'status': 'found', 'position': 2},
            {'keyword_id': 2, 'keyword': 'b', 'category': 'A', 'status': 'found', 'position': 8},
            {'keyword_id': 3, 'keyword': 'c', 'category': 'A', 'status': 'found', 'position': 15},
            {'keyword_id': 4, 'keyword': 'd', 'category': 'B', 'status': 'found', 'position': 40},
            {'keyword_id': 5, 'keyword': 'e', 'category': 'B', 'status': 'not_found', 'position': None},
            {'keyword_id': 6, 'keyword': 'f', 'category': 'B', 'status': 'request_error', 'position': None},
        ]
        summary = seo_positions.summarize_snapshot(rows)
        self.assertEqual((summary['top3'], summary['top10'], summary['top20'], summary['top50']), (1, 2, 3, 4))
        self.assertEqual(summary['average_position'], 16.25)
        self.assertEqual(summary['not_found'], 1)
        self.assertEqual(summary['errors'], 1)

    def test_comparisons_for_3_7_and_30_days(self):
        now = dt.datetime(2026, 9, 1, 8, tzinfo=UTC)
        for days, position in ((30, 40), (7, 25), (3, 18)):
            self.add_check(now - dt.timedelta(days=days), 'found', position)
        self.add_check(now, 'found', 9)
        config = {'comparison_tolerance_days': {'3': 2, '7': 3, '30': 5}}
        expected = {3: 9, 7: 16, 30: 31}
        for days in (3, 7, 30):
            with self.subTest(days=days):
                summary = seo_positions.build_summary(self.store, days, config)
                self.assertEqual(summary['best_growth'][0]['change'], expected[days])
                self.assertEqual(summary['baseline_count'], 1)

    def test_period_uses_previous_measurement_within_tolerance(self):
        now = dt.datetime(2026, 9, 1, 8, tzinfo=UTC)
        self.add_check(now - dt.timedelta(days=8), 'found', 20)
        self.add_check(now, 'found', 10)
        config = {'comparison_tolerance_days': {'7': 3}}
        summary = seo_positions.build_summary(self.store, 7, config)
        self.assertEqual(summary['best_growth'][0]['change'], 10)

    def test_keyword_history_has_previous_and_3_7_30_day_changes(self):
        now = dt.datetime(2026, 9, 1, 8, tzinfo=UTC)
        for days, position in ((30, 40), (7, 25), (3, 18)):
            self.add_check(now - dt.timedelta(days=days), 'found', position)
        self.add_check(now - dt.timedelta(days=1), 'found', 11)
        self.add_check(now, 'found', 9)
        history = seo_positions.keyword_history(
            self.store,
            self.keyword.keyword,
            {'comparison_tolerance_days': {'3': 2, '7': 3, '30': 5}},
        )
        self.assertEqual(history['current']['position'], 9)
        self.assertEqual(history['previous']['position'], 11)
        self.assertEqual(history['previous']['change'], 2)
        self.assertEqual(history['periods'][3]['change'], 9)
        self.assertEqual(history['periods'][7]['change'], 16)
        self.assertEqual(history['periods'][30]['change'], 31)

    def test_error_check_is_not_used_as_period_baseline(self):
        now = dt.datetime(2026, 9, 1, 8, tzinfo=UTC)
        self.add_check(now - dt.timedelta(days=7), 'request_error')
        self.add_check(now, 'found', 10)
        summary = seo_positions.build_summary(
            self.store, 7, {'comparison_tolerance_days': {'7': 3}},
        )
        self.assertEqual(summary['baseline_count'], 0)
        self.assertIsNone(summary['average_change'])

    def test_telegram_report_contains_metrics_and_growth(self):
        summary = {
            'period_days': 3, 'total': 2, 'top3': 0, 'top10': 1, 'top20': 2,
            'top50': 2, 'not_found': 0, 'errors': 0, 'unchecked': 0,
            'average_position': 12.0, 'average_before': 18.0,
            'average_current_comparable': 12.0, 'average_change': 6.0,
            'improved': 1, 'declined': 0, 'unchanged': 1, 'appeared': 0,
            'disappeared': 0,
            'best_growth': [{'keyword': 'ремонт', 'before': 18, 'current': 9, 'change': 9}],
            'worst_drop': [],
        }
        report = seo_positions.format_telegram_report(summary)
        self.assertIn('Период: 3 дн.', report)
        self.assertIn('TOP-10: 1', report)
        self.assertIn('18 → 9', report)
        self.assertIn('+9', report)

    def test_event_generation(self):
        self.assertEqual(
            seo_positions.generate_events('found', 14, 'found', 8),
            ['NEW_TOP_10', 'BIG_GROWTH'],
        )
        self.assertEqual(
            seo_positions.generate_events('found', 7, 'found', 19),
            ['LEFT_TOP_10', 'BIG_DROP'],
        )
        self.assertEqual(
            seo_positions.generate_events('not_found', None, 'found', 20),
            ['NEW_IN_SEARCH'],
        )
        self.assertEqual(
            seo_positions.generate_events('found', 20, 'not_found', None),
            ['DISAPPEARED_FROM_SEARCH'],
        )
        self.assertEqual(
            seo_positions.generate_events('found', 20, 'request_error', None),
            [],
        )

    def test_not_found_has_null_position(self):
        check = seo_positions.check_from_documents(
            self.keyword,
            [seo_positions.SearchDocument('https://example.org/')],
            site_url='https://magiarnd.ru',
            checked_at='2026-09-01T08:00:00+00:00',
            search_depth=50,
            source='test',
        )
        self.assertEqual(check.status, 'not_found')
        self.assertIsNone(check.position)
        self.assertIsNone(check.found_url)

    def test_domain_position_and_title_are_extracted(self):
        xml = '''<yandexsearch><response><results><grouping>
          <group><doc><url>https://one.example/</url><title>One</title></doc></group>
          <group><doc><url>https://www.magiarnd.ru/remont</url><title>Магия <hlword>ремонта</hlword></title></doc></group>
        </grouping></results></response></yandexsearch>'''
        documents = seo_positions.parse_yandex_xml(xml)
        check = seo_positions.check_from_documents(
            self.keyword, documents, site_url='https://magiarnd.ru',
            checked_at='2026-09-01T08:00:00+00:00', search_depth=100, source='test',
        )
        self.assertEqual(check.position, 2)
        self.assertEqual(check.title, 'Магия ремонта')

    def test_yandex_request_uses_configured_region_and_official_v2_envelope(self):
        captured = {}
        xml = '<yandexsearch><response><results><grouping/></results></response></yandexsearch>'
        envelope = json.dumps({'rawData': base64.b64encode(xml.encode()).decode()}).encode()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            @staticmethod
            def read():
                return envelope

        def opener(request, timeout):
            captured['body'] = json.loads(request.data.decode('utf-8'))
            captured['authorization'] = request.get_header('Authorization')
            captured['timeout'] = timeout
            return Response()

        provider = seo_positions.YandexSearchApi(
            api_key='secret', folder_id='folder', region_id=39, opener=opener,
        )
        self.assertEqual(provider.search('ремонт', 50), [])
        self.assertEqual(captured['body']['region'], '39')
        self.assertEqual(captured['body']['query']['searchType'], 'SEARCH_TYPE_RU')
        self.assertEqual(captured['body']['responseFormat'], 'FORMAT_XML')
        self.assertEqual(captured['authorization'], 'Api-Key secret')

    def test_checks_are_append_only(self):
        check_id = self.add_check(dt.datetime(2026, 9, 1, tzinfo=UTC), 'found', 10)
        with self.store.session() as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    'UPDATE seo_position_checks SET position = 9 WHERE id = ?',
                    (check_id,),
                )

    def test_keyword_file_is_the_verified_32_query_set(self):
        path = Path(seo_positions.SCRIPT_DIR) / 'seo-keywords.json'
        items = seo_positions.load_keywords(path)
        self.assertEqual(len(items), 32)
        self.assertEqual(Counter(item.category for item in items), {
            'Главная': 8,
            'Новостройки': 6,
            'Вторичное жильё': 6,
            'Ванная': 6,
            'Дизайнерский ремонт': 6,
        })

    def test_missing_credentials_abort_before_writing_checks(self):
        config = {
            'keywords_path': str(Path(seo_positions.SCRIPT_DIR) / 'seo-keywords.json'),
            'database_path': str(Path(self.temporary.name) / 'missing-creds.sqlite3'),
            'region': 'Ростов-на-Дону', 'region_id': 39, 'device': 'desktop',
            'api_page_size': 100, 'site_url': 'https://magiarnd.ru',
            'search_depth': 100, 'source': 'yandex_search_api_v2',
            'big_move_threshold': 5,
            'yandex_search_api': {
                'enabled': True,
                'api_page_size': 100,
                'source': 'yandex_search_api_v2',
            },
        }
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(seo_positions.command_check_yandex(config), 2)
        self.assertFalse(Path(config['database_path']).exists())

    def test_reserve_provider_is_disabled_by_default(self):
        with self.assertRaisesRegex(seo_positions.SeoError, 'reserve provider is disabled'):
            seo_positions.provider_from_environment({
                'region_id': 39,
                'yandex_search_api': {'enabled': False},
            })


if __name__ == '__main__':
    unittest.main()
