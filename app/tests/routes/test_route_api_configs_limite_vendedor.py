import pytest
from flask import Flask
from app.routes.apiConfigsLimiteVendedor import api_configs_limite_vendedor_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(api_configs_limite_vendedor_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_post_limite_vendedor_ok(client, monkeypatch):
    chamado = {}
    def fake_salvar_limite(v_id, v_nome, limite):
        chamado.update(dict(id=v_id, nome=v_nome, limite=limite))
    monkeypatch.setattr(
        "app.routes.apiConfigsLimiteVendedor.salvar_limite_vendedor",
        fake_salvar_limite
    )
    resp = client.post("/api/configs/limite_vendedor", json={
        "vendedor_id": "123",
        "vendedor_nome": "Maria",
        "limite": 5000
    })
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"success": True}
    assert chamado == dict(id="123", nome="Maria", limite=5000)

def test_post_limite_vendedor_campo_faltando(client, monkeypatch):
    # Simula chamada mesmo faltando algum campo (deve passar, mas com valor default)
    capturado = {}
    def fake_salvar_limite(v_id, v_nome, limite):
        capturado.update(dict(id=v_id, nome=v_nome, limite=limite))
    monkeypatch.setattr(
        "app.routes.apiConfigsLimiteVendedor.salvar_limite_vendedor",
        fake_salvar_limite
    )
    resp = client.post("/api/configs/limite_vendedor", json={
        "vendedor_id": "789"
        # vendedor_nome e limite ausentes
    })
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"success": True}
    assert capturado == dict(id="789", nome='', limite="0")

def test_post_limite_vendedor_erro(client, monkeypatch):
    def fake_salvar_limite(*a, **kw):
        raise Exception("Falha no banco")
    monkeypatch.setattr(
        "app.routes.apiConfigsLimiteVendedor.salvar_limite_vendedor",
        fake_salvar_limite
    )
    resp = client.post("/api/configs/limite_vendedor", json={
        "vendedor_id": "123",
        "vendedor_nome": "Maria",
        "limite": 9000
    })
    # Por padrão, sem tratamento, Flask devolve erro 500 e HTML, não JSON
    assert resp.status_code == 500
    assert resp.is_json
    assert "error" in resp.get_json()
