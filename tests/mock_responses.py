from salesforce_tools.util import sf_id_checksum, SFDateTime, fake_sf_id
import string
import random
import json
import sqlite3

API_VERSION = 64.0





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
