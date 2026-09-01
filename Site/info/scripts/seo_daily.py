"""Read-only daily SEO checks. No publishing, sitemap rewrites or indexing submissions."""
import argparse
import subprocess
import sys

from seo_common import SCRIPT_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-gsc', action='store_true', help='Requires configured read-only Google access')
    args = parser.parse_args()
    scripts = ['seo_audit.py'] + (['gsc_coverage.py', 'gsc_stats.py'] if args.with_gsc else [])
    for script in scripts:
        result = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT_DIR / script)], cwd=SCRIPT_DIR)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
