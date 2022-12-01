from authlib.integrations.httpx_client import AsyncOAuth2Client
import json
from salesforce_tools.auth import sfdx_auth_url_to_dict
from subprocess import check_output


class SalesforceAsyncOAuth2Client(AsyncOAuth2Client):
    def __init__(self, *args, **kwargs):
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
        if self.instance_url and self.api_version:
            client_args['base_url'] = f"{self.instance_url}/services/data/v{self.api_version}/"
        client_args['token_endpoint'] = f"{self.instance_url}/services/oauth2/token"
        super().__init__(**client_args)
        self.register_compliance_hook('access_token_response', self._fix_token_response)
        self.register_compliance_hook('refresh_token_response', self._fix_token_response)

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


class SalesforceAPISelector():
    def __init__(self, sf: SalesforceAsyncOAuth2Client):
        self.sf = sf
        self._oauth_user_info_url = f"{sf.instance_url}/services/oauth2/userinfo"
        self._userinfo = None
        self.api_version = sf.api_version

    @property
    async def userinfo(self):
        if not self._userinfo:
            self._userinfo = (await self.sf.get(self._oauth_user_info_url)).json()
        return self._userinfo

    async def __getattr__(self, item):
        return (await self.userinfo).get('urls').get(item).replace('{version}', self.api_version)
