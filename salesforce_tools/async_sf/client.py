from authlib.integrations.httpx_client import AsyncOAuth2Client
import json
from salesforce_tools.auth import sfdx_auth_url_to_dict
from subprocess import check_output
from urllib.parse import quote


class SalesforceAsyncOAuth2Client(AsyncOAuth2Client):
    def __init__(self, *args, **kwargs):
        self.args = kwargs
        if kwargs.get('instance_url'):
            self.instance_url = kwargs.get('instance_url')
        elif kwargs.get('token') and kwargs.get('instance_url'):
            self.instance_url = kwargs.get('token', {}).get('instance_url')
        else:
            default_auth_url = 'https://test.salesforce.com' if kwargs.get(
                'sandbox') else 'https://login.salesforce.com'
            self.instance_url = kwargs.get('auth_url', default_auth_url)
        self.api_version = str(kwargs.get('api_version', '56.0'))
        client_args = {k: v for k, v in kwargs.items() if k not in ['instance_url', 'api_version', 'sandbox']}
        if self.instance_url and self.api_version and not kwargs.get('base_url'):
            client_args['base_url'] = f"{self.instance_url}/services/data/v{self.api_version}/"
        client_args['token_endpoint'] = f"{self.instance_url}/services/oauth2/token"
        super().__init__(**client_args)
        self.register_compliance_hook('access_token_response', self._fix_token_response)
        self.register_compliance_hook('refresh_token_response', self._fix_token_response)

    async def query(self, qry, auto=False):
        if auto:
            results, done, url = [], None, None

            while not done:
                if not url:
                    qr = (await self.get(f'query?q={quote(qry)}')).json()
                else:
                    qr = (await self.get(url, timeout=30)).json()
                done = qr['done']
                url = f"query/{qr.get('nextRecordsUrl', 'query/').split('query/')[1]}"
                results.extend(qr['records'])
        else:
            return await self.get(f'query?q={quote(qry)}')
        return results

    def _fix_token_response(self, resp):
        data = resp.json()
        data['expires_in'] = 3600
        resp.json = lambda: data
        return resp


class SalesforceSfdxAsyncOAuth2Client(SalesforceAsyncOAuth2Client):
    def __init__(self, alias, **kwargs):
        sfdx_auth_url = check_output(f'sfdx force:org:display -u {alias} --json --verbose', shell=True)
        sfdx_auth_url = json.loads(sfdx_auth_url.decode('utf-8'))
        kwargs.update(sfdx_auth_url_to_dict(sfdx_auth_url['result']['sfdxAuthUrl']))
        kwargs['token']['access_token'] = sfdx_auth_url['result']['accessToken']
        super().__init__(**kwargs)


class SalesforceAPISelectorException(Exception):
    pass


class SalesforceAPISelector():
    ALIASES = {
        'tooling': 'tooling_rest'
    }

    def __init__(self, *args, **kwargs):
        self.sf = SalesforceAsyncOAuth2Client(**kwargs)
        self._oauth_user_info_url = f"{self.sf.instance_url}/services/oauth2/userinfo"
        self._userinfo = None
        self.api_version = self.sf.api_version

    @property
    async def userinfo(self):
        if not self._userinfo:
            self._userinfo = (await self.sf.get(self._oauth_user_info_url)).json()
        return self._userinfo

    @property
    async def apis(self):
        return (await self.userinfo).get('urls')

    async def __getattr__(self, item):
        try:
            item = SalesforceAPISelector.ALIASES[item] if item in SalesforceAPISelector.ALIASES.keys() else item
            base_url = (await self.userinfo).get('urls').get(item).replace('{version}', self.api_version)
            args = self.sf.args
            args['base_url'] = base_url
            return SalesforceAsyncOAuth2Client(**args)
        except AttributeError:
            raise SalesforceAPISelectorException('API Not Found')