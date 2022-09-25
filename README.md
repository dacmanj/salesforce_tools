# Examples

## Generic Connection
```
from salesforce_tools import SalesforceAPI
from dotenv import load_dotenv, set_key
import os
import json
load_dotenv()
cid = os.getenv('CLIENT_ID')
sec = os.getenv('CLIENT_SECRET')

def token_saver(s):
    set_key('.env', 'TOKEN', json.dumps(s))

# jwt
# s = SalesforceAPI(client_id=cid, private_key_filename='cert/serverkey.pem', token_updater=token_saver)
# refresh_token
tk = json.loads(os.getenv('TOKEN', '{}'))
s = SalesforceAPI(client_id=cid, client_secret=sec, token=tk, token_updater=token_saver)
# s.session is a requests session
s.session.get("https://login.salesforce.com/services/oauth2/userinfo")
s.open_sf()
```

## BulkAPI
```
from dotenv import load_dotenv, set_key
from salesforce_tools import BulkAPI, JobInfo, OperationEnum, ContentTypeEnum

# 
import pandas as pd
load_dotenv()
cid = os.getenv('CLIENT_ID')
sec = os.getenv('CLIENT_SECRET')

def token_saver(s):
    set_key('.env', 'TOKEN', json.dumps(s))

csv_data = """LastName,FirstName,Title,LeadSource,Description,Birthdate,Email
Cat,Tom,DSH,Interview,Imported from XYZ.csv,1940-02-10Z,tomcat@disney.com
Mouse,Jerry,House Mouse,Import,Imported from XYZ.csv,1940-02-10Z,jerry@disney.com
"""
headers = csv_data.split("\n")[0].split(",")
rows = csv_data.split("\n")[1::]
json_data = [dict(zip(headers, r.split(','))) for r in rows]
tk = json.loads(os.getenv('TOKEN', '{}'))
s = BulkAPI(client_id=cid, client_secret=sec, token=tk, token_updater=token_saver)
j_json = s.create_job(JobInfo(operation=OperationEnum.upsert,
                              object='Contact',
                              external_id_field_name='Email',
                              content_type=ContentTypeEnum.JSON))
b_json = s.upload_data(json.dumps(json_data))
s.close_job()
                              
```

