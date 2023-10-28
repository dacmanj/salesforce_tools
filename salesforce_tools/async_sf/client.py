import webbrowser
from authlib.integrations.httpx_client import AsyncOAuth2Client
import json
from salesforce_tools.auth import sfdx_auth_url_to_dict
from subprocess import check_output
from urllib.parse import quote, urlencode, urljoin

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

    async def _query_all_pages(self, qry):
        qry = self.sanitize_query(qry)
        done, url = None, None
        while not done:
            url = url or f'query?q={qry}'
            qr = (await self.get(url, timeout=300))
            qrj = qr.json()
            try:
                done = qrj.get('done', True)
                url = f"query/{qrj.get('nextRecordsUrl', 'query/').split('query/')[1]}"
            except AttributeError:
                done = True
            yield qr

    async def query_all_pages(self, qry):
        results = []
        async for i in self._query_all_pages(qry):
            results.append(i)
        return results
    
    @staticmethod
    def sanitize_query(str):
        return str.replace('\n', '').replace('\r', '')

    async def query(self, qry, auto=False):
        qry = self.sanitize_query(qry)
        if auto:
            pages = await self.query_all_pages(qry)
            results = pages.pop(-1).json()
            for p in pages:
                pr = p.json()
                results['records'].extend(pr['records'])
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

    API_CACHE = {
        'enterprise': '{instance_url}/services/Soap/c/{version}/{organization_id}',
        'metadata': '{instance_url}/services/Soap/m/{version}/{organization_id}',
        'partner': '{instance_url}/services/Soap/u/{version}/{organization_id}',
        'rest': '{instance_url}/services/data/v{version}/',
        'sobjects': '{instance_url}/services/data/v{version}/sobjects/',
        'search': '{instance_url}/services/data/v{version}/search/',
        'query': '{instance_url}/services/data/v{version}/query/',
        'recent': '{instance_url}/services/data/v{version}/recent/',
        'tooling_soap': '{instance_url}/services/Soap/T/{version}/{organization_id}',
        'tooling_rest': '{instance_url}/services/data/v{version}/tooling/',
        'tooling': '{instance_url}/services/data/v{version}/tooling/',
        'profile': '{instance_url}/{user_id}',
        'feeds': '{instance_url}/services/data/v{version}/chatter/feeds',
        'groups': '{instance_url}/services/data/v{version}/chatter/groups',
        'users': '{instance_url}/services/data/v{version}/chatter/users',
        'feed_items': '{instance_url}/services/data/v{version}/chatter/feed-items',
        'feed_elements': '{instance_url}/services/data/v{version}/chatter/feed-elements',
        'custom_domain': '{instance_url}'
    }

    def __init__(self, *args, base_url_parameters=None, sfdx_alias=None, **kwargs):
        if sfdx_alias:
            kwargs |= self.sfdx_login(sfdx_alias)
        self.sf = SalesforceAsyncOAuth2Client(**kwargs)
        self._oauth_user_info_url = f"{self.sf.instance_url}/services/oauth2/userinfo"
        self._userinfo = None
        self.api_version = self.sf.api_version
        self.base_url_parameters = {
            "instance_url": self.sf.instance_url,
            "version": self.sf.api_version,
            "organization_id": kwargs.get("organization_id", None)
        }
        if base_url_parameters:
            self.base_url_parameters |= base_url_parameters

    def sfdx_login(self, org, sfdx_cmd='sf'):
        import subprocess
        import re

        result = subprocess.run([sfdx_cmd, 'org', 'display', '-o', org, '--json', '--verbose'], stdout=subprocess.PIPE)
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        result = ansi_escape.sub('', result.stdout.decode(encoding='utf-8', errors='strict'))
        result = json.loads(result)['result']
        auth_args = sfdx_auth_url_to_dict(result['sfdxAuthUrl'])
        auth_args['token']['access_token'] = result['accessToken']
        del auth_args['token']['expires_at']
        return auth_args

    @property
    async def userinfo(self):
        if not self._userinfo:
            self._userinfo = (await self.sf.get(self._oauth_user_info_url)).json()
        return self._userinfo

    @property
    async def apis(self):
        return (await self.userinfo).get('urls')

    def __getattr__(self, item):
        item = SalesforceAPISelector.ALIASES[item] if item in SalesforceAPISelector.ALIASES.keys() else item or self.API_CACHE.get('rest')
        args = self.sf.args
        try:
            base_url = self.API_CACHE.get(item).format(**self.base_url_parameters)
            args['base_url'] = base_url
        except (AttributeError, KeyError) as e:
            args['base_url'] = self.base_url_parameters['instance_url']
        return SalesforceAsyncOAuth2Client(**args)

    def open_sf(self, url=''):
        sid = self.session.token.get('access_token')
        qs = urlencode({'sid': sid, 'retURL': url})
        url = urljoin(self.base_url_parameters['instance_url'], f'/secur/frontdoor.jsp?{qs}')
        webbrowser.open(url)
