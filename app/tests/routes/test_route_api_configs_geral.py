import pytest
from flask import Flask
from app.routes.apiConfigsGeral import api_configs_geral_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(api_configs_geral_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_config_geral_ok(monkeypatch, client):
    def fake_consultar_config_geral():
        return {
            "smtp": "smtp.exemplo.com",
            "porta": "587",
            "email_copia": "a@b.com",
            "meta_empresa": "99999",
            "senha_email_smtp": "secreta",
            "email_smtp_principal": "principal@x.com:True",
            "email_smtp_secundario": "sec@x.com:False"
        }
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.consultar_config_geral",
        fake_consultar_config_geral
    )
    resp = client.get('/api/configs/geral')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["smtp"] == "smtp.exemplo.com"
    assert data["email_smtp"] == "principal@x.com"
    assert data["email_smtp_principal_ativo"] is True
    assert data["email_smtp_secundario"] == "sec@x.com"
    assert data["email_smtp_secundario_ativo"] is False

def test_get_config_geral_vazio(monkeypatch, client):
    # Caso config vazio
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.consultar_config_geral",
        lambda: {}
    )
    resp = client.get('/api/configs/geral')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "email_smtp" in data
    assert "email_smtp_secundario" in data
    assert data["email_smtp_principal_ativo"] is False

def test_get_config_geral_erro(monkeypatch, client):
    # Força exception
    def fake_erro():
        raise Exception("Falha DB")
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.consultar_config_geral",
        fake_erro
    )
    resp = client.get('/api/configs/geral')
    assert resp.status_code == 500
    data = resp.get_json()
    assert "Falha DB" in data["error"]

def test_post_config_geral_ok(monkeypatch, client):
    update_args = {}
    def fake_update_one(filtro, update, upsert):
        update_args["filtro"] = filtro
        update_args["update"] = update
        update_args["upsert"] = upsert
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        fake_update_one
    )
    payload = {
        "smtp": "smtp.novo.com",
        "porta": "465",
        "email_copia": "c@d.com",
        "meta_empresa": "33333",
        "senha_email_smtp": "outrasecreta",
        "email_smtp_principal": "novo@x.com",
        "email_smtp_secundario": "segundo@x.com"
    }
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    # Garante que todos os campos vieram corretamente
    for campo in ["smtp", "porta", "email_copia", "meta_empresa", "senha_email_smtp",
                  "email_smtp_principal", "email_smtp_secundario"]:
        assert campo in update_args["update"]["$set"]

def test_post_config_geral_campo_principal_vazio(monkeypatch, client):
    # Se email_smtp_principal = "", sobrescreve
    captured = {}
    
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        lambda: False
    )
    payload = {"smtp": "x", "email_smtp_principal": ""}
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Precisa de um email smtp."
    assert captured == {}

def test_post_config_geral_parcial(monkeypatch, client):
    # Alguns campos não enviados (testa default)
    captured = {}
    
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        lambda: False
    )
    payload = {"smtp": "z"}
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Precisa de um email smtp."
    assert captured == {}

def test_post_config_geral_erro(monkeypatch, client):
    
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        lambda: False
    )
    resp = client.post('/api/configs/geral', json={"smtp": "fail"})
    assert resp.status_code == 500
    data = resp.get_json()
    assert "Precisa de um email smtp." in data["error"]

def test_post_config_geral_principal_vazio_ok(monkeypatch, client):
    """Testa o caso em que só o email_smtp_principal está vazio, mas secundário está OK."""
    captured = {}
    def fake_update_one(filtro, update, upsert):
        captured.update(update["$set"])
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        fake_update_one
    )
    payload = {
        "smtp": "smtp.exemplo.com",
        "porta": "465",
        "email_copia": "teste@exemplo.com",
        "meta_empresa": "10000",
        "senha_email_smtp": "123",
        "email_smtp_principal": "",   # <-- força o elif da linha destacada!
        "email_smtp_secundario": "secundario@exemplo.com"
    }
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    # Verifica que de fato o campo foi setado para vazio
    assert captured["email_smtp_principal"] == ""

def test_post_config_geral_secundario_vazio_ok(monkeypatch, client):
    """Testa o caso em que só o email_smtp_secundario está vazio, mas principal está OK."""
    captured = {}
    def fake_update_one(filtro, update, upsert):
        captured.update(update["$set"])
    monkeypatch.setattr(
        "app.routes.apiConfigsGeral.configs_collection.update_one",
        fake_update_one
    )
    payload = {
        "smtp": "smtp.exemplo.com",
        "porta": "465",
        "email_copia": "teste@exemplo.com",
        "meta_empresa": "10000",
        "senha_email_smtp": "123",
        "email_smtp_principal": "principal@exemplo.com",
        "email_smtp_secundario": ""   # <-- força o elif da linha destacada!
    }
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    # Verifica que de fato o campo foi setado para vazio
    assert captured["email_smtp_secundario"] == ""

def test_post_config_geral_erro_ambos_vazios(client):
    """Testa o caso obrigatório: nenhum email preenchido"""
    payload = {
        "smtp": "smtp.exemplo.com",
        "porta": "465",
        "email_copia": "teste@exemplo.com",
        "meta_empresa": "10000",
        "senha_email_smtp": "123",
        "email_smtp_principal": "",   # <-- ambos vazios
        "email_smtp_secundario": ""
    }
    resp = client.post('/api/configs/geral', json=payload)
    assert resp.status_code == 500
    data = resp.get_json()
    assert "Precisa de um email smtp" in data["error"]