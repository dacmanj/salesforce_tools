from pydantic import BaseModel, ValidationError, validator, Field, ConfigDict
from typing import List
from enum import Enum
import datetime


class JobStateEnum(str, Enum):
    Open = 'Open'
    Closed = 'Closed'
    Aborted = 'Aborted'
    Failed = 'Failed'
    InProgress = 'InProgress'
    UploadComplete = 'UploadComplete'
    JobComplete = 'JobComplete'


class ContentTypeEnum(str, Enum):
    CSV = 'CSV'
    JSON = 'JSON'
    XML = 'XML'
    ZIP_CSV = 'ZIP_CSV'
    ZIP_JSON = 'ZIP_JSON'
    ZIP_XML = 'ZIP_XML'


class ContentTypeHeaderEnum(str, Enum):
    CSV = 'text/csv'
    JSON = 'application/json'
    XML = 'application/xml'


class ConcurrencyModeEnum(str, Enum):
    Parallel = 'Parallel'
    Serial = 'Serial'


class OperationEnum(str, Enum):
    upsert = 'upsert'
    update = 'update'
    insert = 'insert'
    delete = 'delete'
    hard_delete = 'hardDelete'
    query = 'query'
    query_all = 'queryAll'


class ColumnDelimiterEnum(str, Enum):
    BACKQUOTE = "BACKQUOTE"
    CARET = "CARET"
    COMMA = "COMMA"
    PIPE = "PIPE"
    SEMICOLON = "SEMICOLON"
    TAB = "TAB"


class LineEndingEnum(str, Enum):
    CRLF = 'CRLF'
    LF = 'LF'


class JobTypeEnum(str, Enum):
    V2Ingest = "V2Ingest"
    V2Query = "V2Query"
    Classic = "Classic"
    BigObjectIngest = "BigObjectIngest"


class BatchStateEnum(str, Enum):
    Queued = "Queued"
    InProgress = "InProgress"
    Completed = "Completed"
    Failed = "Failed"
    NotProcessed = "NotProcessed"


class JobInfo(BaseModel):
    api_version: float = Field(alias='apiVersion', default=None)
    apex_processing_time: int = Field(alias='apexProcessingTime', default=None)
    api_active_processing_time: int = Field(alias='apiActiveProcessingTime', default=None)
    assignment_rule_id: str = Field(alias='assignmentRuleId', default=None)
    concurrency_mode: ConcurrencyModeEnum = Field(alias='concurrencyMode', default=None)
    content_type: ContentTypeEnum = Field(alias='contentType', default=ContentTypeEnum.CSV)
    created_by_id: str = Field(alias='createdById', default=None)
    created_date: datetime.datetime = Field(alias='createdDate', default=None)
    external_id_field_name: str = Field(alias='externalIdFieldName', default=None)
    id: str
    number_batches_completed: int = Field(alias='numberBatchesCompleted', default=None)
    number_batches_queued: int = Field(alias='numberBatchesQueued', default=None)
    number_batches_failed: int = Field(alias='numberBatchesFailed', default=None)
    number_batches_in_progress: int = Field(alias='numberBatchesInProgress', default=None)
    number_batches_total: int = Field(alias='numberBatchesTotal', default=None)
    number_records_failed: int = Field(alias='numberRecordsFailed', default=None)
    number_records_processed: int = Field(alias='numberRecordsProcessed', default=None)
    number_retries: int = Field(alias='numberRetries', default=None)
    sobject: str = Field(alias='object')
    operation: OperationEnum
    state: JobStateEnum
    column_delimiter: ColumnDelimiterEnum = Field(alias='columnDelimiter')
    line_ending: LineEndingEnum = Field(alias='lineEnding')
    job_type: JobTypeEnum = Field(alias='jobType', default=JobTypeEnum.Classic)
    total_processing_time: int = Field(alias='totalProcessingTime', default=None)
    systemModstamp: datetime.datetime = Field(alias='systemModstamp')
    content_url: str = Field(alias='contentUrl', default=None)
    query: str = Field(default=None)


    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator('operation')
    def external_id_field_name_required_for_upsert(cls, v, values, **kwargs):
        if v == 'upsert' and not values.get('external_id_field_name'):
            raise ValueError('External Id Field Name is required for upsert')
        if not values.get('sobject') and v != 'query':
            raise ValueError('Object must be specified')
        return v
    model_config = ConfigDict(populate_by_name=True)


class BatchInfo(BaseModel):
    apex_processing_time: int = Field(alias='apexProcessingTime', default=None)
    api_active_processing_time: int = Field(alias='apiActiveProcessingTime', default=None)
    created_date: datetime.datetime = Field(alias='createdDate', default=None)
    id: str
    job_id: str = Field(alias='jobId', default=None)
    number_records_failed: int = Field(alias='numberRecordsFailed', default=None)
    number_records_processed: int = Field(alias='numberRecordsProcessed', default=None)
    state: BatchStateEnum
    state_message: str = Field(alias='stateMessage', default=None)
    system_modstamp: datetime.datetime = Field(alias='systemModstamp', default=None)
    total_processing_time: int = Field(alias='totalProcessingTime', default=None)


class BatchInfoList(BaseModel):
    records: List[BatchInfo] = Field(alias='batchInfo', default=[])
    model_config = ConfigDict(populate_by_name=True)


class JobInfoList(BaseModel):
    records: List[JobInfo] = Field(alias='jobInfo', default=[])
    model_config = ConfigDict(populate_by_name=True)


class APIError(BaseModel):
    code: str = Field(alias='errorCode')
    message: str = Field(alias='message')
    model_config = ConfigDict(populate_by_name=True)


class BulkAPIError(BaseModel):
    code: str = Field(alias='exceptionCode')
    message: str = Field(alias='exceptionMessage')
    model_config = ConfigDict(populate_by_name=True)

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
