from arroyo_salesforce.auth import login
from urllib.parse import urljoin, urlencode
import webbrowser


class SalesforceAPI(object):
    session = None
    api_version = None
    instance_url = 'https://login.salesforce.com'
    args = {}

    def __init__(self, api_version='54.0', **kwargs):
        self.session = login(**kwargs)
        self.instance_url = self.session.token.get('instance_url')
        self.api_version = api_version
        self.args = kwargs

    def request(self, url, method='GET', **kwargs):
        url = urljoin(self.instance_url, url)
        return self.session.request(method, url, **kwargs)

    def open_sf(self, url=None):
        sid = self.session.token.get('access_token')
        qs = urlencode({'sid': sid, 'retURL': url})
        url = urljoin(self.instance_url, f'/secur/frontdoor.jsp?{qs}')
        webbrowser.open(url)

