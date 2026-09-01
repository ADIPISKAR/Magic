import datetime as dt
import sys
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

ORIGIN = 'https://magiarnd.ru'
CONFIG = {'site_url': ORIGIN, 'sitemap_url': ORIGIN + '/sitemap.xml', 'gsc_property': 'sc-domain:magiarnd.ru', 'reporting_lag_days': 3}


class SeoTests(unittest.TestCase):
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
