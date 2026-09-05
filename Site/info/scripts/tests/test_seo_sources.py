import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import seo_dashboard
import seo_sources


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = seo_sources.AnalyticsStore(
            Path(self.temporary.name) / 'positions.sqlite3',
        )
        self.config = {
            'database_path': str(self.store.path),
            'keywords_path': str(Path(seo_sources.PROJECT_ROOT) / 'info/scripts/seo-keywords.json'),
            'bootstrap_path': str(Path(seo_sources.PROJECT_ROOT) / 'info/scripts/topvisor-bootstrap-2026-09-02.json'),
            'region': 'Ростов-на-Дону',
            'region_id': 39,
            'device': 'desktop',
            'search_depth': 100,
            'source': 'topvisor',
            'big_move_threshold': 5,
            'comparison_tolerance_days': {'1': 1, '3': 2, '7': 3, '30': 5},
            'topvisor_project_id': 32438229,
            'topvisor_region_index': 76,
            'topvisor_volume_field': 'volume:39:0:1',
            'yandex_search_api': {'enabled': False},
        }
        self.store.initialize()
        self.store.sync_keywords(seo_sources.load_keywords(
            self.config['keywords_path'], self.config,
        ))

    def tearDown(self):
        self.temporary.cleanup()

    def test_topvisor_parser_preserves_zero_frequency_and_not_found(self):
        payload = {
            'result': {
                'keywords': [{
                    'id': 10,
                    'name': 'ремонт квартир ростов-на-дону',
                    'volume:39:0:1': 0,
                    'positionsData': {
                        '2026-09-02:32438229:76': {
                            'position': '--',
                            'relevant_url': '',
                        },
                        '2026-09-01:32438229:76': {
                            'position': 19,
                            'relevant_url': 'https://magiarnd.ru/remont-kvartir',
                        },
                    },
                }],
            },
        }
        rows = seo_sources.parse_topvisor_history(payload, 'volume:39:0:1')
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].frequency_present)
        self.assertEqual(rows[0].frequency, 0)
        self.assertEqual(rows[0].position, 19)
        self.assertIsNone(rows[1].position)

    def test_bootstrap_imports_two_real_dates_idempotently(self):
        first = seo_sources.bootstrap_topvisor({'positions': self.config}, self.store)
        second = seo_sources.bootstrap_topvisor({'positions': self.config}, self.store)
        self.assertEqual(first['inserted'], 33)
        self.assertEqual(second['inserted'], 0)
        self.assertEqual(second['skipped'], 33)
        with self.store.session() as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM seo_keywords WHERE frequency IS NOT NULL',
            ).fetchone()[0], 32)
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM seo_position_checks',
            ).fetchone()[0], 33)

    def test_metrika_parser_keeps_missing_metric_as_null(self):
        rows = seo_sources.parse_metrika_report({
            'data': [{
                'dimensions': [{'id': '/remont'}, {'id': 'yandex'}],
                'metrics': [None, 2, 0],
            }],
        }, ['visits', 'users', 'bounce_rate'])
        self.assertIsNone(rows[0]['visits'])
        self.assertEqual(rows[0]['users'], 2)
        self.assertEqual(rows[0]['bounce_rate'], 0)

    def test_metrika_extended_engagement_metrics_are_preserved(self):
        rows = seo_sources.parse_metrika_report({
            'data': [{
                'dimensions': [{'id': '/remont'}, {'id': 'yandex'}],
                'metrics': [4, 3, 25, 2.5, 91],
            }],
        }, ['visits', 'users', 'bounce_rate', 'page_depth', 'avg_visit_duration_seconds'])
        self.assertEqual(rows[0]['page_depth'], 2.5)
        self.assertEqual(rows[0]['avg_visit_duration_seconds'], 91)

    def test_webmaster_missing_indicators_do_not_become_zero(self):
        class Api:
            @staticmethod
            def discover_site(site_url, host_id):
                return 1, 'https:magiarnd.ru:443'

            @staticmethod
            def popular(*args, **kwargs):
                return [{
                    'query_id': 'q1',
                    'query_text': 'новый запрос',
                    'indicators': {},
                }]

        rows = seo_sources.webmaster_rows(
            Api(),
            site_url='https://magiarnd.ru',
            host_id='',
            date_from=dt.date(2026, 9, 1),
            date_to=dt.date(2026, 9, 1),
            device='ALL',
            limit=500,
            targets={},
        )
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['shows'])
        self.assertIsNone(rows[0]['clicks'])
        self.assertIsNone(rows[0]['ctr'])
        self.assertFalse(rows[0]['is_target'])

    def test_keyword_conversion_is_only_attached_via_landing_page(self):
        position = [{
            'keyword_id': 1,
            'keyword': 'ремонт квартир ростов-на-дону',
            'category': 'Главная',
            'position': 9,
            'status': 'found',
            'frequency': 53,
            'found_url': 'https://magiarnd.ru/remont-kvartir?utm=x',
        }]
        webmaster = {'queries': [{
            'query_text': 'ремонт квартир ростов-на-дону',
            'shows': 10,
            'clicks': 2,
            'ctr': 20,
        }]}
        metrika = {'landings': [{
            'landing_page': '/remont-kvartir',
            'visits': 2,
            'goals': [{'goal_id': 7, 'reaches': 1, 'attribution_level': 'landing_page'}],
        }]}
        merged = seo_dashboard.merge_keyword_analytics(position, webmaster, metrika)[0]
        self.assertEqual(merged['webmaster']['shows'], 10)
        self.assertEqual(merged['landing_analytics']['goals'][0]['reaches'], 1)
        self.assertEqual(merged['conversion_attribution'], 'landing_page')
        self.assertNotIn('conversion', merged['webmaster'])

    def test_missing_credentials_record_status_without_analytics_rows(self):
        config = {
            'positions': self.config,
            'site_url': 'https://magiarnd.ru',
            'webmaster': {'device': 'ALL', 'limit': 500},
        }
        with patch.dict('os.environ', {}, clear=True):
            result = seo_sources.sync_webmaster(
                config, self.store, dt.date(2026, 9, 1), dt.date(2026, 9, 1),
            )
        self.assertEqual(result['status'], 'not_configured')
        with self.store.session() as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM seo_webmaster_queries',
            ).fetchone()[0], 0)
            self.assertEqual(connection.execute(
                "SELECT status FROM seo_source_runs WHERE source='yandex_webmaster'",
            ).fetchone()[0], 'not_configured')


if __name__ == '__main__':
    unittest.main()
