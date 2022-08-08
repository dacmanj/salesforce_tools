from arroyo_salesforce.salesforce import SalesforceAPI
from enum import Enum
import sqlite3


class SalesforceJobStatus(Enum):
    ABORTED = 'Aborted'
    CLOSED = 'Closed'
    OPEN = 'Open'


class SalesforceBulkContentType(Enum):
    CSV = 'CSV'
    JSON = 'JSON'


class SalesforceBulkConcurrencyMode(Enum):
    PARALLEL = 'Parallel'
    SERIAL = 'Serial'


class SalesforceBulkOperation(Enum):
    UPSERT = 'upsert'
    UPDATE = 'update'
    INSERT = 'insert'
    DELETE = 'delete'
    HARD_DELETE = 'hardDelete'
    QUERY = 'query'
    QUERY_ALL = 'queryAll'


class SalesforceBulkJobException(Exception):
    pass


def get_enum_or_val(e):
    return e.value if isinstance(e, Enum) else e


class SalesforceBulkAPI(SalesforceAPI):
    def create_job(self, operation=None, sf_object=None,
                   content_type=SalesforceBulkContentType.CSV,
                   external_id_field_name=None):
        url = f'/services/async/{self.api_version}/job'
        if not (operation and sf_object) or (get_enum_or_val(operation) == SalesforceBulkOperation.UPSERT.value
                                             and not external_id_field_name):
            raise SalesforceBulkJobException('Job must have operation and Salesforce object specified. '
                                             'If job is an upsert then an external id must be specified.')

        d = {
          "operation": get_enum_or_val(operation),
          "object": sf_object,
          "contentType": get_enum_or_val(content_type)
        }
        if external_id_field_name:
            d['externalIdFieldName'] = external_id_field_name
        return self.request(url, method='POST', json=d)

    def create_batch(self, job_id):
        url = f'/services/async/{self.api_version}/job/{job_id}/batch'

    def close_job(self, job_id, state=SalesforceJobStatus.CLOSED.value):
        url = f'/services/async/{self.api_version}/job/{job_id}'
        return self.request(url, method='POST', json={"state": state})