from dataclasses import field
from enum import Enum
from salesforce_tools.models.sf_dataclasses import salesforce_api_dataclass
from typing import List
from salesforce_tools.models.bulk_xsd import JobInfo


@salesforce_api_dataclass
class APIError:
    error_code: str = field(metadata={'alias': 'errorCode'})
    message: str = field(metadata={'alias': 'message'})


@salesforce_api_dataclass
class BulkAPIError:
    exception_code: str = field(metadata={'alias': 'exceptionCode'})
    exception_message: str = field(metadata={'alias': 'exceptionMessage'})


class BulkException(Exception):
    error: BulkAPIError


class ExceptionCode(str, Enum):
    ClientInputError = 'ClientInputError'
    ExceededQuota = 'ExceededQuota'
    FeatureNotEnabled = 'FeatureNotEnabled'
    InvalidBatch = 'InvalidBatch'
    InvalidJob = 'InvalidJob'
    InvalidJobState = 'InvalidJobState'
    InvalidOperation = 'InvalidOperation'
    InvalidSessionId = 'InvalidSessionId'
    InvalidUrl = 'InvalidUrl'
    InvalidUser = 'InvalidUser'
    InvalidXML = 'InvalidXML'
    Timeout = 'Timeout'
    TooManyLockFailure = 'TooManyLockFailure'
    Unknown = 'Unknown'
