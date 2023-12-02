from salesforce_tools.auth import login
from urllib.parse import urljoin, urlencode
import webbrowser
import xmltodict


class SalesforceAPI(object):
    session = None
    api_root = None
    instance_url = None
    args = {}

    def __init__(self, api_version=None, api_root=None, **kwargs):
        self.args = kwargs
        self.args['api_version'] = api_version
        self.api_root = api_root.format(api_version=self.api_version, version=self.api_version) if api_root else None
        self.session = login(**kwargs)
        self.session.api_root = self.api_root
        self.instance_url = self.session.instance_url

    @property
    def api_version(self):
        return self.args.get('api_version') or '56.0'

    def request(self, url, method='GET', **kwargs):
        kwargs['headers'] = kwargs.get('headers', {'Content-Type': 'application/json',
                                                   'Accepts': 'application/json',
                                                   'charset': 'UTF-8'})
        req = self.session.request(method, url, **kwargs)
        return self._force_dict_response(req)

    def get(self, url, auto_next=False, **kwargs):
        t = self.request(url, **kwargs)
        try:
            next_records_url = t[0].get('nextRecordsUrl')
            while auto_next and t[0].get('records') and next_records_url:
                t2 = self.request(next_records_url)
                next_records_url = t2[0].get('nextRecordsUrl')
                t[0]['records'] = t[0]['records'] + t2[0]['records']
        except AttributeError:
            pass

        return t

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            kwargs['method'] = name.upper()
            return self.request(*args, **kwargs)
        return wrapper

    def _force_dict_response(self, resp):
        if 'application/xml' in resp.headers.get('Content-Type', ''):
            data = xmltodict.parse(resp.text)
        elif 'application/json' in resp.headers.get('Content-Type', ''):
            data = resp.json()
        else:
            data = resp.text
        return data, resp.ok, resp.status_code, resp

    def open_sf(self, url=''):
        sid = self.session.token.get('access_token')
        qs = urlencode({'sid': sid, 'retURL': url})
        url = urljoin(self.instance_url, f'/secur/frontdoor.jsp?{qs}')
        webbrowser.open(url)


class RestAPI(SalesforceAPI):
    def __init__(self, **kwargs):
        super().__init__(api_root='/services/data/v{api_version}/', **kwargs)

    def get_metadata(self, sobject):
        return self.request(f'sobjects/{sobject}/describe/')

    def get_record(self, sobject, sfid):
        return self.request(f'sobjects/{sobject}/{sfid}')

    def query(self, query, **kwargs):
        qs = urlencode({'q': query})
        return self.get(f'query?{qs}', **kwargs)


class ToolingAPI(SalesforceAPI):
    def __init__(self, **kwargs):
        super().__init__(api_root='/services/data/v{api_version}/tooling/', **kwargs)

    def query(self, query, **kwargs):
        qs = urlencode({'q': query})
        return self.get(f'query?{qs}', **kwargs)

