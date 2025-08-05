import pytest

def test_index_html_get(client, app):
    # GET deve retornar 200 e renderizar index.html
    resp = client.get('/index.html')
    assert resp.status_code == 200
    assert b'index' in resp.data or b'login' in resp.data or b'Index' in resp.data
    # Opcional: checa se é HTML
    assert 'text/html' in resp.content_type

def test_index_html_post(client, app):
    # POST deve funcionar igual ao GET (pois a view trata os dois do mesmo jeito)
    resp = client.post('/index.html')
    assert resp.status_code == 200
    assert b'index' in resp.data or b'login' in resp.data or b'Index' in resp.data
    assert 'text/html' in resp.content_type

def test_index_html_render(client):
    resp = client.get('/index.html')
    assert resp.status_code == 200
    assert b'<html' in resp.data or b'index' in resp.data
    assert 'text/html' in resp.content_type
