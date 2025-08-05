import pytest
from flask import Flask
from app.routes.apiConfigsMetasVendedor import api_configs_metas_vendedor_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_configs_metas_vendedor_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_post_metas_vendedor_ok(monkeypatch, client):
    def fake_salvar_meta(v_id, v_nome, meta_qtd, meta_valor, meta_semana):
        # Checa que os dados foram repassados
        assert v_id == "123"
        assert v_nome == "Maria"
        assert meta_qtd == "10"
        assert meta_valor == "5000"
        assert meta_semana == "20000"
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedor.salvar_meta_vendedor", fake_salvar_meta)
    resp = client.post("/api/configs/metas_vendedor", json={
        "vendedor_id": "123",
        "vendedor_nome": "Maria",
        "meta_dia_quantidade": "10",
        "meta_dia_valor": "5000",
        "meta_semana": "20000"
    })
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True

def test_post_metas_vendedor_campos_faltando(client):
    # Campos obrigatórios não enviados
    resp = client.post("/api/configs/metas_vendedor", json={
        "vendedor_id": "123"
        # vendedor_nome ausente
    })
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False
    assert "Vendedor não informado" in data["erro"]

    resp2 = client.post("/api/configs/metas_vendedor", json={
        "vendedor_nome": "Fulano"
        # vendedor_id ausente
    })
    data2 = resp2.get_json()
    assert resp2.status_code == 400
    assert data2["success"] is False
    assert "Vendedor não informado" in data2["erro"]

def test_post_metas_vendedor_erro(monkeypatch, client):
    def fake_salvar_meta(*args, **kwargs):
        raise Exception("Falha ao salvar")
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedor.salvar_meta_vendedor", fake_salvar_meta)
    resp = client.post("/api/configs/metas_vendedor", json={
        "vendedor_id": "1",
        "vendedor_nome": "Zezinho",
        "meta_dia_quantidade": "1",
        "meta_dia_valor": "1",
        "meta_semana": "1"
    })
    data = resp.get_json()
    assert resp.status_code == 500
    assert data["error"] == "Falha ao salvar"

def test_post_metas_vendedor_com_valores_zerados(monkeypatch, client):
    """Testa o envio explícito de zeros como strings (válido!)"""
    called = {}

    monkeypatch.setattr("app.routes.apiConfigsMetasVendedor.salvar_meta_vendedor", lambda x: x)
    resp = client.post("/api/configs/metas_vendedor", json={
        "vendedor_id": "",
        "vendedor_nome": "",
        "meta_dia_quantidade": "",
        "meta_dia_valor": "",
        "meta_semana": ""
    })
    assert resp.status_code == 400

def test_post_metas_vendedor_com_metas_zeradas(monkeypatch, client):
    """Testa o envio explícito de zeros como strings (válido!)"""
    called = {}
    def fake_salvar_meta(v_id, v_nome, meta_qtd, meta_valor, meta_semana):
        called["v_id"] = v_id
        called["v_nome"] = v_nome
        called["meta_qtd"] = meta_qtd
        called["meta_valor"] = meta_valor
        called["meta_semana"] = meta_semana
    monkeypatch.setattr("app.routes.apiConfigsMetasVendedor.salvar_meta_vendedor", fake_salvar_meta)
    resp = client.post("/api/configs/metas_vendedor", json={
        "vendedor_id": "123",
        "vendedor_nome": "João",
        "meta_dia_quantidade": "",
        "meta_dia_valor": "",
        "meta_semana": ""
    })
    assert resp.status_code == 200
    assert called["v_id"] == "123"
    assert called["v_nome"] == "João"
    assert called["meta_qtd"] == "0"
    assert called["meta_valor"] == "0"
    assert called["meta_semana"] == "0"
