from requests_oauthlib import OAuth2Session
from flask.json import jsonify
import json
from oauthlib.common import to_unicode
from datetime import datetime, timedelta
import webbrowser
from arroyo_salesforce.oauth_server import CallbackServer
from urllib.parse import urlsplit, urljoin
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
AUTH_URL = 'https://login.salesforce.com/services/oauth2/authorize'
TOKEN_URL = 'https://login.salesforce.com/services/oauth2/token'
REDIRECT_URI = 'http://localhost:8000/callback'


def create_session(sid='1234', client_id=None, client_secret=None, refresh_token=None, port=8080, **kwargs):
    salesforce = salesforce_compliance_fix(
        OAuth2Session(token={
            'access_token': sid,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': (7200 if not refresh_token else -30)
        },
            client_id=client_id,
            auto_refresh_url=TOKEN_URL,
            auto_refresh_kwargs={'client_id': client_id, 'client_secret': client_secret},
            token_updater=lambda x: True)
    )
    resp = salesforce.get('https://login.salesforce.com/services/oauth2/userinfo')
    return jsonify(resp.json())


def login(client_id, client_secret):
    salesforce = salesforce_compliance_fix(OAuth2Session(client_id,
                                                         redirect_uri=REDIRECT_URI,
                                                         scope='refresh_token openid web full'
                                                         )
                                           )
    authorization_url, state = salesforce.authorization_url(AUTH_URL)
    webbrowser.open(authorization_url, new=1)
    authorization_response = CallbackServer().get_auth()
    ruri = urlsplit(REDIRECT_URI)
    ruri_base_url = ruri.scheme + '://' + ruri.netloc
    authorization_response = urljoin(ruri_base_url, authorization_response)
    salesforce.fetch_token(TOKEN_URL, client_secret=client_secret,
                           authorization_response=authorization_response)
    return salesforce


def salesforce_compliance_fix(sess):
    def _compliance_fix(response):
        token = json.loads(response.text)
        if token.get('issued_at'):
            iat = int(token["issued_at"]) / 1000
            token["expires_in"] = (datetime.fromtimestamp(iat) + timedelta(hours=2) - datetime.now()).seconds
        fixed_token = json.dumps(token)
        response._content = to_unicode(fixed_token).encode("utf-8")

        return response

    sess.register_compliance_hook("access_token_response", _compliance_fix)
    sess.register_compliance_hook("refresh_token_response", _compliance_fix)

    return sess


