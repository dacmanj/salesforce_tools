from pydantic import BaseModel, ValidationError, validator, Field
from typing import Literal, Optional, List
from enum import Enum
import datetime


class JobStateEnum(str, Enum):
    Open = 'Open'
    Closed = 'Closed'
    Aborted = 'Aborted'
    Failed = 'Failed'
    UploadComplete = 'UploadComplete'


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
    Classic = "Classic"
    BigObjectIngest = "BigObjectIngest"


class BatchStateEnum(str, Enum):
    Queued = "Queued"
    InProgress = "InProgress"
    Completed = "Completed"
    Failed = "Failed"
    NotProcessed = "NotProcessed"


class JobInfo(BaseModel):
    api_version: Optional[float] = Field(alias='apiVersion')
    apex_processing_time: Optional[int] = Field(alias='apexProcessingTime')
    api_active_processing_time: Optional[int] = Field(alias='apiActiveProcessingTime')
    assignment_rule_id: Optional[str] = Field(alias='assignmentRuleId')
    concurrency_mode: Optional[ConcurrencyModeEnum] = Field(alias='concurrencyMode')
    content_type: ContentTypeEnum = Field(alias='contentType', default=ContentTypeEnum.CSV)
    created_by_id: Optional[str] = Field(alias='createdById')
    created_date: Optional[datetime.datetime] = Field(alias='createdDate')
    external_id_field_name: Optional[str] = Field(alias='externalIdFieldName')
    id: Optional[str]
    number_batches_completed: Optional[int] = Field(alias='numberBatchesCompleted')
    number_batches_queued: Optional[int] = Field(alias='numberBatchesQueued')
    number_batches_failed: Optional[int] = Field(alias='numberBatchesFailed')
    number_batches_in_progress: Optional[int] = Field(alias='numberBatchesInProgress')
    number_batches_total: Optional[int] = Field(alias='numberBatchesTotal')
    number_records_failed: Optional[int] = Field(alias='numberRecordsFailed')
    number_records_processed: Optional[int] = Field(alias='numberRecordsProcessed')
    number_retries: Optional[int] = Field(alias='numberRetries')
    sobject: Optional[str] = Field(alias='object')
    operation: OperationEnum
    state: Optional[JobStateEnum]
    column_delimiter: Optional[ColumnDelimiterEnum] \
        = Field(alias='columnDelimiter')
    line_ending: Optional[LineEndingEnum] = Field(alias='lineEnding')
    job_type: Optional[JobTypeEnum] = Field(alias='jobType', default=JobTypeEnum.Classic)
    total_processing_time: Optional[int] = Field(alias='totalProcessingTime')
    systemModstamp: Optional[datetime.datetime] = Field(alias='systemModstamp')
    content_url: Optional[str] = Field(alias='contentUrl')
    query: Optional[str]


    @validator('operation')
    def external_id_field_name_required_for_upsert(cls, v, values, **kwargs):
        if v == 'upsert' and not values.get('external_id_field_name'):
            raise ValueError('External Id Field Name is required for upsert')
        if not values.get('sobject') and v != 'query':
            raise ValueError('Object must be specified')
        return v

    class Config:
        allow_population_by_field_name = True


class BatchInfo(BaseModel):
    apex_processing_time: Optional[int] = Field(alias='apexProcessingTime')
    api_active_processing_time: Optional[int] = Field(alias='apiActiveProcessingTime')
    created_date: Optional[datetime.datetime] = Field(alias='createdDate')
    id: Optional[str]
    job_id: Optional[str] = Field(alias='jobId')
    number_records_failed: Optional[int] = Field(alias='numberRecordsFailed')
    number_records_processed: Optional[int] = Field(alias='numberRecordsProcessed')
    state: Optional[BatchStateEnum]
    state_message: Optional[str] = Field(alias='stateMessage')
    system_modstamp: Optional[datetime.datetime] = Field(alias='systemModstamp')
    total_processing_time: Optional[int] = Field(alias='totalProcessingTime')


class BatchInfoList(BaseModel):
    records: List[BatchInfo] = Field(alias='batchInfo', default=[])

    class Config:
        allow_population_by_field_name = True


class JobInfoList(BaseModel):
    records: List[JobInfo] = Field(alias='jobInfo', default=[])

    class Config:
        allow_population_by_field_name = True


class APIError(BaseModel):
    code: str = Field(alias='errorCode')
    message: str = Field(alias='message')

    class Config:
        allow_population_by_field_name = True


class BulkAPIError(BaseModel):
    code: str = Field(alias='exceptionCode')
    message: str = Field(alias='exceptionMessage')

    class Config:
        allow_population_by_field_name = True

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
