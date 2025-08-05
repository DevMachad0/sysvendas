import os
import pytest
from flask import Flask

# Mock das blueprints e handler para registrar (não precisa importar os reais para teste de criação básica)
import app

def test_create_app_basico(monkeypatch):
    # Define variáveis de ambiente para testar
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("FLASK_DEBUG", "True")
    monkeypatch.setenv("SENHA_SESSION", "segredo123")

    app_obj = app.create_app(testing=True)

    # Testa se é Flask
    assert isinstance(app_obj, Flask)
    # Testa config básica
    assert app_obj.config["ENV"] == "development"
    assert app_obj.config["DEBUG"] is True
    assert app_obj.secret_key == "segredo123"
    assert app_obj.config["SESSION_COOKIE_SECURE"] is True
    assert app_obj.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app_obj.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app_obj.config["TESTING"] is True

    # Testa se o middleware existe
    assert any(f.__name__ == "bloquear_ips_externos" for f in app_obj.before_request_funcs[None])

def test_create_app_bloqueio_ip(monkeypatch):
    monkeypatch.setenv("SENHA_SESSION", "123")

    flask_app = app.create_app(testing=True)
    client = flask_app.test_client()

    # Testa se bloqueia IP externo
    response = client.get("/", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert response.status_code == 403

    # Testa se permite localhost
    response2 = client.get("/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    # O status será 404 se a rota não existe, mas não pode ser 403
    assert response2.status_code != 403
