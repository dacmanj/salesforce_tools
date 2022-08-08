import math
from datetime import datetime
from dateutil.relativedelta import relativedelta


def datetime_as_str(d: datetime = datetime.now(), days: int = 0, months: int = 0, years: int = 0, hours: int =12) -> str:
    d = d + relativedelta(days=days, years=years, months=months, hours=hours)
    return d.strftime('%Y-%m-%dT%H:%M:%S.000+0000')


def datetime_as_epoch(d: datetime = datetime.now()) -> int:
    return math.trunc(d.timestamp()*1000)


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
