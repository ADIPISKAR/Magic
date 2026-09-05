"""Read-only daily SEO checks. No publishing, sitemap rewrites or indexing submissions."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from seo_common import SCRIPT_DIR
from seo_sources import load_source_config
from seo_telegram import TelegramError, send_event


def telegram_enabled(flag):
    return flag or os.environ.get('SEO_TELEGRAM_ENABLED', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def analytics_enabled():
    return os.environ.get('SEO_ANALYTICS_ENABLED', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def dashboard_photos(kind):
    """PNG paths to attach to a daily/weekly Telegram notification, per spec
    sections 11-12 (dashboard image + short text, not a text wall). Best
    effort: any problem here just means the notification goes out as text
    only, same as before charts existed.
    """
    try:
        config = load_source_config()
        dashboard = json.loads(Path(config['dashboard_path']).read_text(encoding='utf-8'))
    except (OSError, ValueError, KeyError):
        return []
    charts = dashboard.get('charts') or {}
    if kind == 'weekly':
        weekly = charts.get('weekly') or {}
        candidates = [weekly.get('dashboard'), weekly.get('positions'), weekly.get('traffic')]
    else:
        candidates = [(charts.get('dashboard') or {}).get('1')]
    return [path for path in candidates if path and Path(path).is_file()]


def notify(kind, message, *, photos=None):
    try:
        send_event(kind, message, photos=photos)
        return True
    except TelegramError as error:
        print(f'SEO TELEGRAM FAILED: {error}', file=sys.stderr)
        return False


def run_script(script, *arguments):
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', str(SCRIPT_DIR / script), *arguments],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-gsc', action='store_true', help='Requires configured read-only Google access')
    parser.add_argument('--telegram', action='store_true', help='Send the result to the configured SEO topic')
    parser.add_argument('--notification-kind', choices=('daily', 'weekly', 'manual_check'), default='daily')
    args = parser.parse_args()
    use_analytics = analytics_enabled()
    analytics_report = ''
    if use_analytics:
        for script, arguments in (
            ('seo_sources.py', ('sync-all',)),
            ('seo_dashboard.py', ('build',)),
        ):
            result = run_script(script, *arguments)
            if result.returncode:
                detail = (result.stderr or result.stdout).strip()
                if telegram_enabled(args.telegram):
                    notify('service_error', f'{script}: FAIL\n{detail}')
                return result.returncode
        report_days = '7' if args.notification_kind == 'weekly' else '1'
        result = run_script('seo_dashboard.py', 'report', '--days', report_days)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            if telegram_enabled(args.telegram):
                notify('service_error', f'seo_dashboard.py: FAIL\n{detail}')
            return result.returncode
        analytics_report = result.stdout.strip()

    scripts = ['seo_audit.py'] + (['gsc_coverage.py', 'gsc_stats.py'] if args.with_gsc else [])
    summaries = []
    for script in scripts:
        result = run_script(script)
        detail = (result.stdout if result.returncode == 0 else result.stderr or result.stdout).strip()
        summaries.append(f'{script}: {"OK" if result.returncode == 0 else "FAIL"}\n{detail}')
        if result.returncode:
            if telegram_enabled(args.telegram):
                notify('service_error', '\n\n'.join(summaries))
            return result.returncode
    message = '\n\n'.join(summaries)
    if use_analytics:
        message = analytics_report + '\n\n🛠 Technical SEO\n' + message
    photos = dashboard_photos(args.notification_kind) if use_analytics else []
    if telegram_enabled(args.telegram) and not notify(args.notification_kind, message, photos=photos):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
