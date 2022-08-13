from arroyo_salesforce.auth import login
from urllib.parse import urljoin, urlencode
import webbrowser
import xmltodict


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
        kwargs['headers'] = kwargs.get('headers', {'Content-Type': 'application/json',
                                                   'Accepts': 'application/json',
                                                   'charset': 'UTF-8'})
        url = urljoin(self.instance_url, url)
        req = self.session.request(method, url, **kwargs)
        return self._force_dict_response(req)

    def _force_dict_response(self, resp):
        if 'application/xml' in resp.headers['Content-Type']:
            data = xmltodict.parse(resp.text)
        elif 'application/json' in resp.headers['Content-Type']:
            data = resp.json()
        else:
            data = resp.text
        return data, resp.ok, resp.status_code, resp

    def open_sf(self, url=''):
        sid = self.session.token.get('access_token')
        qs = urlencode({'sid': sid, 'retURL': url})
        url = urljoin(self.instance_url, f'/secur/frontdoor.jsp?{qs}')
        webbrowser.open(url)

