"""Legacy entry point. Magic generates sitemap.xml through Laravel."""
import sys

if __name__ == '__main__':
    print('No sitemap file was changed. Update home_lastmod in config/seo.php or updated_at in '
          'config/seo_pages.php only after a significant content change. Laravel renders those dates.')
    sys.exit(0)
