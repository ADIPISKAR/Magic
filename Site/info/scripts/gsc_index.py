"""Legacy entry point: Google Indexing API does not support repair-service pages."""
import sys

if __name__ == '__main__':
    print('Disabled for Magic: Google Indexing API supports JobPosting and eligible livestream pages only. '
          'Use sitemap.xml and Search Console URL inspection. No URLs were submitted.', file=sys.stderr)
    sys.exit(2)
