import pytest
from flask import Flask
from app.routes.apiFimExpediente import api_fim_expediente_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_fim_expediente_bp)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_fim_expediente_ok(monkeypatch, client):
    # Simula execução bem-sucedida da função registrar_fim_expediente
    monkeypatch.setattr(
        "app.routes.apiFimExpediente.registrar_fim_expediente",
        lambda: None
    )
    resp = client.post("/api/fim_expediente")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert "Fim do expediente" in data["msg"]

def test_fim_expediente_erro(monkeypatch, client):
    # Simula erro ao registrar o fim do expediente
    def erro():
        raise Exception("Falha no banco")
    monkeypatch.setattr(
        "app.routes.apiFimExpediente.registrar_fim_expediente",
        erro
    )
    resp = client.post("/api/fim_expediente")
    data = resp.get_json()
    assert resp.status_code == 500
    assert data["success"] is False
    assert "Falha no banco" in data["msg"]
