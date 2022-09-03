from requests_oauthlib import OAuth2Session
import json
from oauthlib.common import to_unicode
from datetime import datetime, timedelta
import webbrowser
from oauth_server import CallbackServer
from urllib.parse import urlsplit, urljoin
import os
from typing import Callable
from oauthlib.oauth2 import WebApplicationClient

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
AUTH_URL = 'https://login.salesforce.com/services/oauth2/authorize'
TOKEN_URL = 'https://login.salesforce.com/services/oauth2/token'
REDIRECT_URI = 'http://localhost:8000/callback'


def login(client_id: str = None, client_secret: str = None, token: dict = None,
          token_updater: Callable = lambda x: True, callback_port: int = 8000):
    salesforce = salesforce_compliance_fix(
        OAuth2Session(token=token,
                      client=SalesforceOAuthClient(client_id),
                      redirect_uri=REDIRECT_URI,
                      scope='refresh_token openid web full' if not token else None,
                      auto_refresh_url=TOKEN_URL,
                      auto_refresh_kwargs={'client_id': client_id, 'client_secret': client_secret},
                      token_updater=token_updater
                      )
    )
    if not token or not token.get('refresh_token'):
        authorization_url, state = salesforce.authorization_url(AUTH_URL)
        webbrowser.open(authorization_url, new=1)
        authorization_response = CallbackServer().get_auth(port=callback_port)
        ruri = urlsplit(REDIRECT_URI)
        ruri_base_url = ruri.scheme + '://' + ruri.netloc
        authorization_response = urljoin(ruri_base_url, authorization_response)
        salesforce.fetch_token(TOKEN_URL, client_secret=client_secret,
                               authorization_response=authorization_response)
    return salesforce


def salesforce_compliance_fix(sess):
    token = ''
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


class SalesforceOAuthClient(WebApplicationClient):
    def _add_bearer_token(self, uri, http_method='GET', body=None,
                          headers=None, token_placement=None):
        uri, headers, body = super()._add_bearer_token(
            uri,
            http_method=http_method,
            body=body,
            headers=headers,
            token_placement=token_placement
        )

        headers['X-SFDC-Session'] = self.token.get('access_token')
        return uri, headers, body