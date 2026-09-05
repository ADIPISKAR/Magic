#!/usr/bin/env bash
# Deploy the SEO visualization stage to the Magic production server.
#
# WHY THIS SCRIPT EXISTS: Claude could not run this itself -- neither the
# cloud workspace (HTTPS-proxy-only egress, port 22 blocked) nor the Linux
# bridge on your desktop (no general internet access) can reach the server.
# Run this from a real terminal that has normal internet access (your own
# machine's terminal/PowerShell/WSL -- not the Cowork sandbox).
#
# WHAT IT DOES
#   1. discover  -- read-only. SSHes in and reports the current state
#                   (paths, PHP/Python versions, existing services, disk
#                   space) so you can sanity-check REMOTE_ROOT below before
#                   touching anything.
#   2. backup    -- tars up the current on-server copy of every path this
#                   deploy will touch, timestamped, so you can roll back.
#   3. apply     -- extracts magic-seo-visual-deploy.tar.gz over the server,
#                   then runs the safe post-deploy steps (cache clears, pip
#                   install, systemd timers). Refuses to run without an
#                   explicit --yes-i-checked-discover flag.
#
# WHAT IT DELIBERATELY DOES NOT DO
#   - It never touches /etc/magia/seo-telegram.env (your real secrets) --
#     that file must already exist on the server with the right values.
#   - It does not deploy TelegramWorker/ -- that is a Cloudflare Worker, not
#     something SSH can reach. Deploy it separately with your own Cloudflare
#     credentials:
#       cd TelegramWorker && npx wrangler deploy
#   - It does not delete anything on the server (tar extraction only adds/
#     overwrites files present in the bundle).
#   - It never hardcodes your SSH password. You'll be prompted by ssh/scp
#     each time, exactly like typing `ssh root@host` yourself.
#
# USAGE
#   chmod +x deploy.sh
#   ./deploy.sh discover                  # read-only, do this first
#   ./deploy.sh backup                    # tars the current server state
#   ./deploy.sh apply --yes-i-checked-discover
#
# Adjust the variables below if `discover` shows REMOTE_ROOT is wrong.

set -euo pipefail

HOST="${SEO_DEPLOY_HOST:-root@5.129.192.224}"
REMOTE_ROOT="${SEO_DEPLOY_ROOT:-/var/www/magia}"          # confirmed via Site/info/systemd/*.service (WorkingDirectory=/var/www/magia/Site)
REMOTE_TMP="/tmp/magic-seo-visual-deploy"
BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/magic-seo-visual-deploy.tar.gz"
BACKUP_NAME="magic-seo-visual-predeploy-$(date +%Y%m%d-%H%M%S).tar.gz"

# TelegramBot/'s deployed path was NOT confirmed by anything I could read
# (only Site/'s path is nailed down by the systemd units) -- 'discover'
# below checks whether $REMOTE_ROOT/TelegramBot looks right before 'apply'
# writes to it. If it's wrong, set SEO_DEPLOY_ROOT or edit this script.

cmd="${1:-}"

case "$cmd" in
  discover)
    echo "==> Read-only discovery on $HOST"
    ssh "$HOST" REMOTE_ROOT="$REMOTE_ROOT" bash -s <<'REMOTE'
set -x
echo "--- top-level layout ---"
ls -la /var/www/ 2>&1 || true
echo "--- REMOTE_ROOT ($REMOTE_ROOT) contents ---"
ls -la "$REMOTE_ROOT" 2>&1 || true
echo "--- Site/ contents ---"
ls -la "$REMOTE_ROOT/Site" 2>&1 | head -30 || true
echo "--- TelegramBot/ contents (path is an assumption -- confirm it looks right) ---"
ls -la "$REMOTE_ROOT/TelegramBot" 2>&1 || echo "  (not found at this path -- fix SEO_DEPLOY_ROOT before 'apply', or that subtree just isn't deployed here)"
echo "--- PHP ---"
php -v 2>&1 || true
echo "--- Python / matplotlib ---"
python3 -V 2>&1 || true
python3 -c "import matplotlib; print('matplotlib', matplotlib.__version__)" 2>&1 || true
echo "--- existing seo-analytics storage ---"
ls -la "$REMOTE_ROOT/Site/storage/app/private/seo-analytics" 2>&1 || true
echo "--- env file for the systemd services (not read, just checked for existence) ---"
ls -la /etc/magia/seo-telegram.env 2>&1 || true
echo "--- current systemd timers ---"
systemctl list-timers 'magia-seo-*' --all 2>&1 || true
echo "--- disk space ---"
df -h /var/www 2>&1 || true
echo "--- is REMOTE_ROOT a git repo? ---"
git -C "$REMOTE_ROOT" status --short 2>&1 | head -20 || echo "(not a git repo, or git not available)"
REMOTE
    echo
    echo "==> Review the output above. If REMOTE_ROOT ($REMOTE_ROOT) or the"
    echo "    TelegramBot path look wrong, set SEO_DEPLOY_ROOT (and/or"
    echo "    SEO_DEPLOY_HOST) before running 'apply', e.g.:"
    echo "      SEO_DEPLOY_ROOT=/srv/magia $0 discover"
    ;;

  backup)
    echo "==> Backing up current server state to $HOST:$REMOTE_TMP/$BACKUP_NAME"
    ssh "$HOST" REMOTE_ROOT="$REMOTE_ROOT" REMOTE_TMP="$REMOTE_TMP" BACKUP_NAME="$BACKUP_NAME" bash -s <<'REMOTE'
set -euo pipefail
mkdir -p "$REMOTE_TMP"
cd "$REMOTE_ROOT"
tar czf "$REMOTE_TMP/$BACKUP_NAME" --ignore-failed-read \
    Site/app/Http/Controllers/SeoTelegramController.php \
    Site/app/Http/Controllers/SeoDashboardController.php \
    Site/config/services.php \
    Site/routes/api.php \
    Site/routes/web.php \
    Site/info/scripts \
    Site/resources/views/seo-dashboard.blade.php \
    Site/resources/views/seo-dashboard-login.blade.php \
    Site/resources/js/seo-dashboard.js \
    Site/resources/css/seo-dashboard.css \
    2>&1 | grep -v '^tar:.*No such file' || true
ls -la "$REMOTE_TMP/$BACKUP_NAME"
REMOTE
    echo "==> Backup written to $HOST:$REMOTE_TMP/$BACKUP_NAME -- copy it somewhere safe:"
    echo "    scp $HOST:$REMOTE_TMP/$BACKUP_NAME ."
    ;;

  apply)
    if [[ "${2:-}" != "--yes-i-checked-discover" ]]; then
      echo "Refusing to touch the live server without --yes-i-checked-discover." >&2
      echo "Run '$0 discover' first, confirm REMOTE_ROOT is right, then:" >&2
      echo "  $0 apply --yes-i-checked-discover" >&2
      exit 1
    fi
    if [[ ! -f "$BUNDLE" ]]; then
      echo "Bundle not found: $BUNDLE" >&2
      exit 1
    fi

    echo "==> Copying bundle to $HOST:$REMOTE_TMP/"
    ssh "$HOST" "mkdir -p '$REMOTE_TMP'"
    scp "$BUNDLE" "$HOST:$REMOTE_TMP/bundle.tar.gz"

    echo "==> Extracting and running post-deploy steps on $HOST"
    ssh "$HOST" REMOTE_ROOT="$REMOTE_ROOT" REMOTE_TMP="$REMOTE_TMP" bash -s <<'REMOTE'
set -euo pipefail
echo "--- extracting bundle over $REMOTE_ROOT ---"
tar xzf "$REMOTE_TMP/bundle.tar.gz" -C "$REMOTE_ROOT"

echo "--- fixing ownership (Site/ runs as www-data per the systemd units) ---"
chown -R www-data:www-data "$REMOTE_ROOT/Site" 2>&1 || echo "  (chown skipped -- run manually if needed)"

cd "$REMOTE_ROOT/Site"

# Blade resolves @vite() through public/build/manifest.json, which ships
# with the bundle only if it was rebuilt. Deploying CSS/JS sources without
# rebuilding leaves the manifest missing those entries and every page that
# uses them throws a 500 -- that is how the SEO dashboard broke.
echo "--- rebuilding frontend assets ---"
if npm run build 2>&1 | tail -3; then
    chown -R www-data:www-data public/build
else
    echo "  npm run build FAILED -- pages using @vite will 500 until this is fixed" >&2
fi

echo "--- Laravel cache clears ---"
php artisan config:clear 2>&1 || true
php artisan route:clear 2>&1 || true
php artisan cache:clear 2>&1 || true
php artisan view:clear 2>&1 || true

echo "--- ensuring matplotlib (and the rest of requirements.txt) is installed ---"
python3 -m pip install -r info/scripts/requirements.txt --break-system-packages 2>&1 \
  || python3 -m pip install -r info/scripts/requirements.txt 2>&1 \
  || echo "  pip install failed -- check manually, charts will not render without matplotlib"

echo "--- installing/refreshing the daily+weekly systemd timers ---"
cp info/systemd/magia-seo-daily.service info/systemd/magia-seo-daily.timer \
   info/systemd/magia-seo-weekly.service info/systemd/magia-seo-weekly.timer \
   /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now magia-seo-daily.timer magia-seo-weekly.timer
systemctl list-timers 'magia-seo-*'

echo "--- sanity-checking the new charts package builds cleanly ---"
cd info/scripts
sudo -u www-data python3 seo_dashboard.py build 2>&1 | tail -5 || echo "  (build check failed -- inspect manually before trusting the bot)"

echo "--- done. Remember: TelegramWorker is NOT deployed by this script. ---"
echo "    From a machine with your Cloudflare credentials:"
echo "      cd TelegramWorker && npx wrangler deploy"
REMOTE
    echo
    echo "==> Deploy finished. Sanity-check the Telegram bot for real, then"
    echo "    separately run 'npx wrangler deploy' inside TelegramWorker/"
    echo "    from a machine with your Cloudflare login."
    ;;

  *)
    echo "Usage: $0 {discover|backup|apply --yes-i-checked-discover}" >&2
    exit 1
    ;;
esac
