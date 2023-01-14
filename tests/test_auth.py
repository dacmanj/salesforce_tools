from salesforce_tools.auth import login, TOKEN_REL_URL
from mock_responses import mock_response


def fake_open(url, new=None):
    pass


def fake_auth_code_path(self, state='12345'):
    return f"/callback?code=aPrxT9Lzoezd_72OG18vycl0gdfPS8jLc.IfY2H8ana14w0GZuKFcMApsIf6xyjAm3HbskSaHQ%3D%3D&state={state}"


def test_auth(monkeypatch, requests_mock):
    requests_mock.post(TOKEN_REL_URL,
                       text=mock_response('id_token'),
                       status_code=200)
    monkeypatch.setattr("webbrowser.open", lambda url, new: True, raising=True)
    monkeypatch.setattr("salesforce_tools.auth.OAuth2Session.new_state", lambda x: '12345', raising=True)
    monkeypatch.setattr("salesforce_tools.auth.CallbackServer.get_auth", fake_auth_code_path, raising=True)
    s = login('1234', '12345')