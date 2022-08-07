from arroyo_salesforce.auth import login
from urllib.parse import urljoin


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
        h = {'X-SFDC-Session': self.session.token.get('access_token')}
        if kwargs.get('headers'):
            h.merge(kwargs.get('headers'))
        return self.session.request(method, url, headers=h, **kwargs)
