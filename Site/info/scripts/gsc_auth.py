"""Authorize Search Console read-only access. Run interactively once."""
import sys

from seo_common import SCRIPT_DIR, SeoError, write_json

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
TOKEN_FILE = SCRIPT_DIR / 'token.json'
SA_FILE = SCRIPT_DIR / 'service_account.json'


def get_credentials():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import credentials, service_account
    except ImportError as error:
        raise SeoError('Install info/scripts/requirements.txt before using GSC.') from error
    if SA_FILE.exists():
        creds = service_account.Credentials.from_service_account_file(str(SA_FILE), scopes=SCOPES)
    elif TOKEN_FILE.exists():
        creds = credentials.Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    else:
        raise SeoError('GSC access is not configured. Run gsc_auth.py or provide service_account.json.')
    if not creds.valid:
        try:
            creds.refresh(Request())
        except Exception as error:
            raise SeoError('Google authorization failed. Reauthorize; report data has not been replaced.') from error
        if not SA_FILE.exists():
            import json
            write_json(TOKEN_FILE, json.loads(creds.to_json()))
    return creds


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        import json
        path = SCRIPT_DIR / 'credentials.json'
        if not path.exists():
            raise SeoError('Place your Desktop OAuth client file at info/scripts/credentials.json.')
        flow = InstalledAppFlow.from_client_secrets_file(str(path), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
        write_json(TOKEN_FILE, json.loads(creds.to_json()))
        print('Read-only Search Console authorization saved locally.')
        return 0
    except (ImportError, SeoError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
