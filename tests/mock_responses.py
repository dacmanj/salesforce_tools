from arroyo_salesforce.util import sf_id_checksum, datetime_as_epoch, datetime_as_str
import string
import random
import json
import sqlite3

API_VERSION = 54.0


def fake_id(prefix='001', instance='8X', reserved='0', id_size=6):
    valid_id_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    unique_id = ''.join(random.choice(valid_id_chars) for i in range(id_size)).zfill(9)
    sf_id_15_char = f"{prefix}{instance}{reserved}{unique_id}"
    return f"{sf_id_15_char}{sf_id_checksum(sf_id_15_char)}"


def get_template(k: str):
    conn = sqlite3.connect('test_data.sqlite')
    cursor = conn.execute(f"SELECT key, value, default_substitutions from mock_api_response_templates where key = '{k}' limit 1")
    for row in cursor:
        return row[1], eval(row[2] or {})


def mock_response(template_name: str, **kwargs) -> str:
    t, kw_defaults = get_template(template_name)
    kwargs = kw_defaults | kwargs
    if kwargs:
        j = json.loads(t)
        for k, v in kwargs.items():
            j[k] = v
        t = json.dumps(j)
    return t
