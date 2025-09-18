from salesforce_tools.async_sf.client import SalesforceAPISelector
from time import sleep
import csv
from io import StringIO

from salesforce_tools.models.bulk import JobInfo, JobStateEnum


class BulkAPI(object):
    def __init__(self, sf: SalesforceAPISelector):
        self.sf = sf.rest
    
    async def query(self, qry):
        backoff = 5
        job = JobInfo.model_validate((await self.sf.post("jobs/query", json={
            "operation": "query",
            "query": qry
        })).json())
        while job.state in (JobStateEnum.UploadComplete, JobStateEnum.InProgress):
            sleep(backoff)
            job = JobInfo.model_validate((await self.sf.get(f"jobs/query/{job.id}")).json())
            if backoff < 5*60:
                backoff = min(int(backoff + 5), 5*60)

        results = await self.sf.get(f"""jobs/query/{job.id}/results""")
        return list(csv.DictReader(StringIO(results.text))), JobInfo.model_validate(job)

