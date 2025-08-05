import pytest
from flask import Flask
from app.routes.apiInserirLog import api_inserir_log_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_inserir_log_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_inserir_log_ok(monkeypatch, client):
    # Mock para inserção bem sucedida
    monkeypatch.setattr(
        "app.routes.apiInserirLog.inserir_log",
        lambda data, hora, mod, usuario: None
    )
    resp = client.post(
        "/api/inserir_log",
        json={
            "data": "2024-07-01",
            "hora": "08:45",
            "modificacao": "Atualizou o registro",
            "usuario": "admin"
        }
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True

def test_inserir_log_dados_incompletos(client):
    # Envia apenas parte dos campos
    resp = client.post(
        "/api/inserir_log",
        json={
            "data": "2024-07-01",
            "modificacao": "Faltou hora e usuario"
        }
    )
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False
    assert "incompletos" in data["erro"]

def test_inserir_log_excecao(monkeypatch, client):
    # Mock gera exceção
    def erro(*args, **kwargs):
        raise Exception("Erro inesperado")
    monkeypatch.setattr(
        "app.routes.apiInserirLog.inserir_log",
        erro
    )
    resp = client.post(
        "/api/inserir_log",
        json={
            "data": "2024-07-01",
            "hora": "09:15",
            "modificacao": "Teste erro",
            "usuario": "user1"
        }
    )
    data = resp.get_json()
    assert resp.status_code == 500
    assert data["error"].startswith("Erro inesperado")
