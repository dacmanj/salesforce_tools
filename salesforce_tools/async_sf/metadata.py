import asyncio
import tqdm
from salesforce_tools.async_sf.client import SalesforceAsyncOAuth2Client


class SalesforceMetadataFetcherAsync:
    def __init__(self, client: SalesforceAsyncOAuth2Client, cache_file: str = None):
        self.client = client
        self._cache_sobject = {}
        self._cache_sobjects_list = []
        self.cache_file = cache_file
        if self.cache_file:
            self.load_cache(self.cache_file)

    async def get_sobject_describe(self, obj, cache=True):
        if not cache or not self._cache_sobject.get(obj):
            self._cache_sobject[obj] = (await self.client.get(f'sobjects/{obj}/describe')).json()
        return self._cache_sobject.get(obj)

    async def get_picklist_values(self, obj, field):
        obj_md = await self.get_sobject_describe(obj)
        return [f for f in obj_md['fields'] if f['name'] == field][0]['picklistValues']

    async def get_permissionable_fields(self, normalize=True):
        permissionable_fields = {}
        pv = await self.get_picklist_values('FieldPermissions', 'Field')
        pv = [p['value'] for p in pv]
        if normalize:
            for f in pv:
                sf_obj, fld = f.split('.')
                if not permissionable_fields.get(sf_obj):
                    permissionable_fields[sf_obj] = []
                permissionable_fields[sf_obj].append(fld)
            return permissionable_fields
        return pv

    async def get_all_sobjects(self, cache=True):
        if not cache or not self._cache_sobjects_list:
            self._cache_sobjects_list = (await self.client.get("sobjects")).json()['sobjects']
        return self._cache_sobjects_list

    async def get_all_sobject_request_coroutines(self, unfiltered=True, cache=True):
        objects_to_fetch = await self.get_all_sobjects(cache)
        tasks = []
        if not unfiltered:
            objects_to_fetch = [o for o in objects_to_fetch if
                                o['associateEntityType'] not in ['Share', 'ChangeEvent', 'Feed', 'History']]
        if cache:
            objects_to_fetch = [o for o in objects_to_fetch if o['name'] not in self._cache_sobject.keys()]
        if objects_to_fetch:
            tasks = [self.get_sobject_describe(o['name']) for o in objects_to_fetch]
        return tasks

    async def get_all_sobject_metadata(self, unfiltered=True, cache=True):
        tasks = await self.get_all_sobject_request_coroutines(unfiltered, cache)
        [await t for t in asyncio.as_completed(tasks)]
        return self._cache_sobject

    def save_cache(self, filename: str = None):
        filename = filename or self.cache_file
        output_format = {"_cache_sobjects_list": self._cache_sobjects_list,
                         "_cache_sobject": self._cache_sobject}
        with open(filename, 'w') as f:
            json.dump(output_format, f, indent=4)

    def load_cache(self, filename: str = None):
        filename = filename or self.cache_file
        try:
            with open(filename, 'r') as f:
                c = json.load(f)
                self._cache_sobjects_list, self._cache_sobject = c['_cache_sobjects_list'], c['_cache_sobject']
        except FileNotFoundError:
            pass
