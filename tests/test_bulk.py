import pytest
from arroyo_salesforce.bulk import SalesforceBulkAPI
from arroyo_salesforce.auth import TOKEN_URL
from mock_responses import mock_response, API_VERSION


def fake_open(url, new=None):
    pass

@pytest.fixture()
def fake_auth_code_path(state='12345'):
    return


@pytest.fixture
def mock_func1():
    def mock_ret(*args, **kwargs):
        return 2


def mock_auth(func):
    def inner(monkeypatch, requests_mock, *args, **kwargs):
        state = '12345'
        auth_code_redirect_url = f"/callback?code=aPrxT9Lzoezd_72OG18vycl0gdfPS8jLc.IfY2H8ana14w0GZuKFcMApsIf6xyjAm3HbskSaHQ%3D%3D&state={state}"
        requests_mock.post(TOKEN_URL,
                           text=mock_response('id_token'),
                           status_code=200)
        monkeypatch.setattr("webbrowser.open", lambda url, new: True, raising=True)
        monkeypatch.setattr("arroyo_salesforce.auth.OAuth2Session.new_state", lambda x: state, raising=True)
        monkeypatch.setattr("arroyo_salesforce.auth.CallbackServer.get_auth", lambda x: auth_code_redirect_url, raising=True)
        return func(monkeypatch, requests_mock, *args, **kwargs)
    return inner


@mock_auth
def test_bulk(monkeypatch, requests_mock):
    requests_mock.post(f'/services/async/{API_VERSION}/job',
                       text=mock_response('bulk_api_job_detail'),
                       status_code=200)
    s = SalesforceBulkAPI()
    s.create_job(operation='insert', sf_object='Contact')