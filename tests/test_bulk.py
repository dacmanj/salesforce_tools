from arroyo_salesforce.bulk import SalesforceBulkAPI
from arroyo_salesforce.auth import TOKEN_URL
from mock_responses import mock_response, API_VERSION


def fake_open(url, new=None):
    pass


def fake_auth_code_path(self, state='12345'):
    return f"/callback?code=aPrxT9Lzoezd_72OG18vycl0gdfPS8jLc.IfY2H8ana14w0GZuKFcMApsIf6xyjAm3HbskSaHQ%3D%3D&state={state}"


def test_bulk(monkeypatch, requests_mock):
    requests_mock.post(f'/services/async/{API_VERSION}/job',
                       text=mock_response('bulk_api_job_detail'),
                       status_code=200)
    requests_mock.post(TOKEN_URL,
                       text=mock_response('id_token'),
                       status_code=200)
    monkeypatch.setattr("webbrowser.open", lambda url, new: True, raising=True)
    monkeypatch.setattr("arroyo_salesforce.auth.OAuth2Session.new_state", lambda x: '12345', raising=True)
    monkeypatch.setattr("arroyo_salesforce.auth.CallbackServer.get_auth", fake_auth_code_path, raising=True)
    s = SalesforceBulkAPI()
    s.create_job(operation='insert', sf_object='Contact')