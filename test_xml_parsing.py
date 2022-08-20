import xmltodict

xmlt = """<?xml version="1.0" encoding="UTF-8"?>
<batchInfo
   xmlns="http://www.force.com/2009/06/asyncapi/dataload">
    <id>7518X00000bg2U0QAI</id>
    <jobId>7508X00000Rfll9QAB</jobId>
    <state>Queued</state>
    <createdDate>2022-08-13T16:47:02.000Z</createdDate>
    <systemModstamp>2022-08-13T16:47:02.000Z</systemModstamp>
    <numberRecordsProcessed>0</numberRecordsProcessed>
    <numberRecordsFailed>0</numberRecordsFailed>
    <totalProcessingTime>0</totalProcessingTime>
    <apiActiveProcessingTime>0</apiActiveProcessingTime>
    <apexProcessingTime>0</apexProcessingTime>
</batchInfo>"""

rdict = xmltodict.parse(xmlt)

