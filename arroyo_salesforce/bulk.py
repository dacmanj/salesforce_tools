from arroyo_salesforce.salesforce import SalesforceAPI
from enum import Enum
from arroyo_salesforce.bulk_models import JobInfo, JobInfoList, BatchInfo, BatchInfoList, \
    OperationEnum, ContentTypeEnum, ContentTypeHeaderEnum, JobTypeEnum, JobStateEnum, BulkAPIError, APIError,\
    BulkException
from typing import Union, Optional, List
from pydantic import BaseModel, ValidationError, parse_obj_as


class SalesforceBulkJobException(Exception):
    pass


def get_enum_or_val(e):
    return e.value if isinstance(e, Enum) else e


class SalesforceBulkAPI(SalesforceAPI):
    job: Optional[Union[JobInfo, BulkAPIError]]
    batches: List[BatchInfo] = []

    @property
    def job(self):
        return self.__job

    @job.setter
    def job(self, value: JobInfo):
        if value and not value.job_type and value.content_url:
            value.job_type == JobTypeEnum.Classic if 'ingest' not in value.content_url else JobTypeEnum.V2Ingest
            self.job_type = value.job_type
        self.__job = value

    def __init__(self, job_id: str = None, job: JobInfo = None, **kwargs):
        super().__init__(**kwargs)
        self.job = kwargs.get('job', self.set_job(job_id) if job_id else job)

    def create_job(self, job: JobInfo):
        job_type = JobTypeEnum.V2Ingest if job.job_type == JobTypeEnum.V2Ingest else JobTypeEnum.Classic

        url = f'/services/data/v{self.api_version}/jobs/ingest' if job_type == JobTypeEnum.V2Ingest\
            else f'/services/async/{self.api_version}/job'
        if not job.id:
            d = job.dict(by_alias=True, exclude_none=True, exclude={'job_type'})
            job, ok, *_ = self.request(url, method='POST', json=d)
            self.job = self._model_wrap(job, ok, JobInfo, True)
            self.job.job_type = job_type
        return self.job

    # TODO: Where to put "static helper methods"?
    def get_jobs(self):
        jobs, ok, *_ = self.request(f'/services/data/v{self.api_version}/jobs/ingest')
        return self._model_wrap(jobs, ok, JobInfoList, False)

    def create_batch(self, data):
        if isinstance(self.job, BulkAPIError):
            raise BulkException(self.job)
        job_id = self.job.id
        content_type = getattr(ContentTypeHeaderEnum, self.job.content_type).value
        url = f'/services/async/{self.api_version}/job/{job_id}/batch'
        data, ok, *_ = self.request(url, method='POST', data=data, headers={'Content-Type': content_type})
        batch = self._model_wrap(data, ok, BatchInfo, False)
        self.batches.append(batch)
        return batch

    def _model_wrap(self, data: any, ok: bool, model: BaseModel, raise_exception_on_error=False):
        if ok:
            o = parse_obj_as(model, data)
        else:
            if isinstance(data, list):
                try:
                    o = parse_obj_as(List[BulkAPIError], data)
                except ValidationError:
                    o = parse_obj_as(List[APIError], data)
            else:
                if data.get('error'):
                    data = data.get('error')
                try:
                    o = parse_obj_as(BulkAPIError, data)
                except ValidationError:
                    o = parse_obj_as(APIError, data)

            if raise_exception_on_error:
                raise o
        return o

    def close_job(self, job_id: str = None, state: JobStateEnum = JobStateEnum.UploadComplete):
        job_id = job_id or self.job.id
        url = f'/services/async/{self.api_version}/job/{job_id}'
        data, ok, *_ = self.request(url, method='POST', json={"state": state.value})
        job = self._model_wrap(data, ok, JobInfo, False)
        if ok and job.id == self.job.id:
            self.job = job
        return job

    def set_job(self, job_id):
        url = f'/services/async/{self.api_version}/job/{job_id}'
        data, ok, *_ = self.request(url, method='GET')
        self.job = self._model_wrap(data, ok, JobInfo, True)
        return self.job

    def get_batch_info(self, batch: BatchInfo = None, batch_id: str = None):
        url = f'/services/async/{self.api_version}/job/{self.job.id}/batch'
        data, ok, *_ = self.request(url, method='GET')
        return self._model_wrap(data, ok, BatchInfoList, False)

    def get_batches(self, job_id:str = None):
        url = f'/services/async/{self.api_version}/job/{self.job.id}/batch'
        data, ok, *_ = self.request(url, method='GET')
        self.batches = self._model_wrap(data, ok, BatchInfoList, True).records
        return self.batches
