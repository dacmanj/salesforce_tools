import asyncio
from salesforce_tools.async_sf.client import SalesforceAPISelector
from salesforce_tools.metadata import split_api_name
from urllib.parse import quote
import itertools
import pickle
import re


class InvalidQueryException(Exception):
    pass

class InvalidFieldException(Exception):
    pass
class InvalidRelationshipException(Exception):
    pass

class SalesforceMetadataFetcherAsync:
    def __init__(self, apis: SalesforceAPISelector, cache_file: str = None):
        self.rest_api = apis.rest
        self.tooling_api = apis.tooling
        self._cache_sobject = {}
        self._cache_sobjects_list = None
        self._tooling_api_custom_objects_cache = []
        self._cache_tooling_object_describe = {}
        self._cache_entity_definitions = None
        self._cache_field_definitions = {}
        self._cache_field_definition = {}
        self.cache_file = cache_file
        if self.cache_file:
            self.load_cache(self.cache_file)

    async def get_all_sobjects(self, cache=True, timeout=30):
        if not cache or not self._cache_sobjects_list:
            self._cache_sobjects_list = (await self.rest_api.get("sobjects", timeout=timeout))
        return self._cache_sobjects_list.json()['sobjects']
    
    async def get_entity_definitions(self, cache=True, timeout=30, custom_settings = False, customizable = True):
        if not cache or not self._cache_entity_definitions:
            sobjects = []
            limit = 2000
            filters = []
            if customizable:
                filters.append("IsCustomizable = true") 
            if not custom_settings:
                filters.append("IsCustomSetting = false")
            where = f"WHERE {' and '.join(filters)}" if filters else ''
            order_by = f"ORDER BY DurableId LIMIT {limit}"
            while True:
                results = (await self.query_tooling_api_object('EntityDefinition', where=where, order_by=order_by, exclude_fields=('Metadata', 'FullName')))[0]
                sobjects.append(results)
                r_json = results.json()
                if r_json['size'] == 2000:
                    where = f"WHERE DurableId > '{r_json['records'][-1]['DurableId']}'"
                else:
                    break
            self._cache_entity_definitions = sobjects
        return list(itertools.chain.from_iterable([r.json()['records'] for r in self._cache_entity_definitions]))

    
    async def get_fields_for_tooling_api_object(self, sf_object, exclude_fields=None):
        if not exclude_fields:
            exclude_fields = []
        return [f['name'] for f in (await self.get_tooling_object_describe(sf_object))['fields'] if f['name'] not in exclude_fields]

    async def query_tooling_api_object(self, sf_object, where='', order_by='', exclude_fields=None):
        if not exclude_fields:
            exclude_fields = []
        flds = ','.join(await self.get_fields_for_tooling_api_object(sf_object, exclude_fields=exclude_fields))
        return (await self.tooling_api.query_all_pages(f"SELECT {flds} FROM {sf_object} {where} {order_by}"))

    async def get_sobject_describe(self, obj, cache=True, timeout=30):
        if not cache or not self._cache_sobject.get(obj):
            self._cache_sobject[obj] = (await self.rest_api.get(f'sobjects/{obj}/describe', timeout=timeout))
        return self._cache_sobject.get(obj).json()

    async def get_picklist_values(self, obj, field):
        obj_md = await self.get_sobject_describe(obj)
        return [f for f in obj_md['fields'] if f['name'] == field][0]['picklistValues']

    async def get_permissionable_fields(self, normalize=True):        
        pv = await self.get_picklist_values('FieldPermissions', 'Field')
        pv = [p['value'] for p in pv]
        if normalize:
            permissionable_fields = {}
            for f in pv:
                sf_obj, fld = f.split('.')
                if not permissionable_fields.get(sf_obj):
                    permissionable_fields[sf_obj] = []
                permissionable_fields[sf_obj].append(fld)
            return permissionable_fields
        return pv

    async def get_all_sobject_request_coroutines(self, unfiltered=False, cache=True):
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

    async def get_all_sobject_rest_metadata(self, unfiltered=True, cache=True):
        tasks = await self.get_all_sobject_request_coroutines(unfiltered, cache)
        [await t for t in asyncio.as_completed(tasks)]
        return self._cache_sobject

    def save_cache(self, filename: str = None):
        filename = filename or self.cache_file
        output_format = {"_cache_sobjects_list": self._cache_sobjects_list,
                         "_cache_sobject": self._cache_sobject,
                         "_cache_tooling_object_describe": self._cache_tooling_object_describe,
                         "_cache_entity_definitions": self._cache_entity_definitions,
                         "_cache_field_definitions": self._cache_field_definitions,
                         "_cache_field_definition": self._cache_field_definition
                         }
        with open(filename, 'wb') as f:
            pickle.dump(output_format, f)

    def load_cache(self, filename: str = None):
        filename = filename or self.cache_file
        try:
            with open(filename, 'rb') as f:
                c = pickle.load(f)
                self._cache_sobjects_list = c.get('_cache_sobjects_list', None)
                self._cache_sobject = c.get('_cache_sobject', {})
                self._cache_tooling_object_describe = c.get("_cache_tooling_object_describe", {})
                self._cache_entity_definitions = c.get('_cache_entity_definitions', [])
                self._cache_field_definitions = c.get('_cache_field_definitions', {})
                self._cache_field_definition = c.get('_cache_field_definition', {})
        except FileNotFoundError:
            pass

    async def get_custom_obj_id(self, api_name=None, namespace=None, basename=None, custom=False, suffix=None):
        if api_name:
            (namespace, basename, custom, suffix) = split_api_name(api_name).values()
        if custom or suffix:
            try:
                namespace = namespace if namespace else None
                obj_search = [o for o in (await self.get_entity_definitions()) if o['NamespacePrefix'] == namespace and o['DeveloperName'] == basename]
                obj_id = obj_search[0]['Id']
            except IndexError as e:
                pass
        else:
            obj_id = basename
        return obj_id
    
    async def get_tooling_object_describe(self, tooling_object):
        if not self._cache_tooling_object_describe.get('tooling_object'):
            self._cache_tooling_object_describe[tooling_object] = (await self.tooling_api.get(f'sobjects/{tooling_object}/describe'))
        return self._cache_tooling_object_describe[tooling_object].json()

    async def get_entity_definition(self, sf_object):
        return [ed for ed in (await self.get_entity_definitions()) if ed['QualifiedApiName'] == sf_object][0]

    async def get_field_definitions(self, sf_object):
        fields = ','.join(await self.get_fields_for_tooling_api_object('FieldDefinition', exclude_fields=('Metadata', 'FullName')))
        if not self._cache_field_definitions.get(sf_object):
            self._cache_field_definitions[sf_object] = (await self.tooling_api.query_all_pages(f"""SELECT {fields} FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName='{sf_object}'"""))
        try:
            return list(itertools.chain.from_iterable([r.json()['records'] for r in self._cache_field_definitions[sf_object]]))
        except TypeError:
            return []


    async def get_field_definition(self, durable_id):
        fields = ','.join(await self.get_fields_for_tooling_api_object('FieldDefinition'))
        if not self._cache_field_definition.get(durable_id):
            self._cache_field_definition[durable_id] = (await self.tooling_api.query(f"""SELECT {fields} FROM FieldDefinition WHERE DurableId='{durable_id}'"""))
        try:
            return self._cache_field_definition[durable_id].json()['records'][0]
        except (AttributeError, IndexError):
            return {}
    
    async def get_field_durable_id(self, sf_object, field):
        return [f['DurableId'] for f in (await self.get_field_definitions(sf_object)) if f['QualifiedApiName'] == field][0]

    async def get_field_definition_by_api_name(self, sf_object, field):
        durable_id = await self.get_field_durable_id(sf_object, field)
        try:
            return (await self.get_field_definition(durable_id))
        except (AttributeError, IndexError):
            return {}
        
    async def get_all_picklist_fields_tooling_api(self):
        entities = (await self.get_entity_definitions())
        tasks = [
            asyncio.create_task(
                self.get_picklist_fields_for_object_tooling_api(
                    e['QualifiedApiName']
                )
            )
            for e in entities
        ]
        return {k:v for d in [await t for t in asyncio.as_completed(tasks)] for k,v in d.items()}

    
    async def get_picklist_value_set_name(self, obj, field):
        pmd = (await self.get_field_definition_by_api_name(obj, field))
        return obj, field, pmd['Metadata']['valueSet']['valueSetName']
        
    async def get_picklist_fields_for_object_tooling_api(self, sobject):
        picklist_values = []
        import tqdm
        fields = (await self.get_field_definitions(sobject))
        for f in fields:
            is_standard = f['DurableId'] == f['EntityDefinitionId'] + '.' + f['QualifiedApiName']
            if not is_standard and f['DataType'] in ('Picklist', 'Picklist (Multi-Select)'):
                fmd = (await self.get_field_definition_by_api_name(sobject, f['QualifiedApiName']))
                picklist_values.append(
                    {
                        "Object": sobject,
                        "Field": fmd['QualifiedApiName'],
                        "Values": fmd['Metadata']['valueSet'].get('valueSetDefinition', {}).get('value'),
                        "ValueSetName": fmd['Metadata']['valueSet']['valueSetName'],
                    }
                )
        return {sobject: picklist_values}

    async def check_fields(self, qry_objects, fields_to_check, exception_on_invalid=True):
        valid_fields = []
        if not isinstance(qry_objects, list):
            qry_objects = [qry_objects]
        if not isinstance(fields_to_check, list):
            fields_to_check = [fields_to_check]

        objs_fields = [(await self.get_sobject_describe(obj)) for obj in qry_objects]
        for f in fields_to_check:
            p = f.split('.', 1)
            is_rel = len(p)>1
            for obj_fields in objs_fields:
                fields = obj_fields['fields']
                if is_rel:
                    relationship = [f for f in fields if (f.get('relationshipName') or '').casefold() == p[0].casefold()]
                    if relationship:
                        try:
                            await self.check_fields(relationship[0]['referenceTo'], p[1], exception_on_invalid=True)
                        except (InvalidFieldException, InvalidRelationshipException) as e:
                            if exception_on_invalid:
                                raise e
                            continue
                    else:
                        if exception_on_invalid:
                            raise InvalidRelationshipException(f"Invalid relationship {p[0]} on {obj_fields['name']}")                        
                        else:
                            continue
                else:
                    if not [f['name'] for f in fields if f['name'].casefold() == p[0].casefold()]:
                        if exception_on_invalid:
                            raise InvalidFieldException(p[0].upper())
                        else:
                            continue
                valid_fields.append('.'.join(p))
        return valid_fields
    
    @staticmethod
    def get_fields_from_query(qry):
        qry = qry.replace('\n','').replace('\r','')
        try:
            from_kw = re.findall('FROM', qry, flags=re.IGNORECASE)[0]
        except IndexError as e:
            raise InvalidQueryException(f'Missing FROM Keyword in Query {qry}')
        try:
            select_kw = re.findall('SELECT', qry, flags=re.IGNORECASE)[0]
        except IndexError as e:
            raise InvalidQueryException(f'Missing SELECT Keyword in Query {qry}')

        return [r.strip() for r in qry.split(from_kw)[0].split(select_kw)[1].strip().split(',')]

    @staticmethod
    def get_table_from_query(qry):
        qry = qry.replace('\n','').replace('\r','')
        try:
            from_kw = re.findall('FROM', qry, flags=re.IGNORECASE)[0]
        except IndexError as e:
            raise InvalidQueryException(f'Missing FROM Keyword in Query {qry}')
        return qry.split(from_kw)[1].split(' ')[1]




    

