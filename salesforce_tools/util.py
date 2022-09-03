import math
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


"""
Adapted from 
https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/using_regular_expressions_to_validate_email_addresses.html
"""
EMAIL_ADDRESS_REGEX = r"""^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"""


class SFDateTime(datetime):
    @property
    def sf_iso(self):
        return self.strftime('%Y-%m-%dT%H:%M:%S.000+0000')

    @property
    def sf_epoch(self):
        return math.trunc(self.timestamp()*1000)

    @staticmethod
    def datetime_to_str(d: datetime = datetime.now(), days: int = 0, months: int = 0, years: int = 0, hours: int = 12) -> str:
        d = d + relativedelta(days=days, years=years, months=months, hours=hours)
        return d.strftime('%Y-%m-%dT%H:%M:%S.000+0000')

    @staticmethod
    def datetime_to_epoch(d: datetime = datetime.now()) -> int:
        return math.trunc(d.timestamp()*1000)


class EmailValidator:
    def __init__(self):
        self.evp = re.compile(EMAIL_ADDRESS_REGEX)

    def is_valid(self, email):
        return True if re.match(self.evp, email) else False


def sf_id_checksum(sf_id: str) -> str:
    s = ""
    for i in range(3):
        f = 0
        for j in range(5):
            c = sf_id[i * 5 + j]
            if "A" <= c <= "Z":
                f += 1 << j
        s += "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"[f]
    return s
