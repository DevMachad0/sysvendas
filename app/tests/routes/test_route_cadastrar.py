import io
import base64
import pytest
from flask import Flask, session, template_rendered
import app.routes.cadastrar as cadastra_mod
from app.routes.cadastrar import cadastra_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(cadastra_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth(monkeypatch):
    # Permite autenticar um usuário válido para os testes
    def do_login(sess, tipo="admin"):
        sess["user"] = {"username": "admin", "tipo": tipo}
    return do_login

@pytest.fixture
def usuario_pos_vendas_mock(monkeypatch):
    usuarios = [
        {"username": "pos1", "nome_completo": "Pós 1", "nome": "P1", "tipo": "pos_vendas"},
        {"username": "pos2", "nome_completo": "Pós 2", "nome": "P2", "tipo": "pos_vendas"},
    ]
    monkeypatch.setattr("app.routes.cadastrar.usuarios_collection.find", lambda *a, **k: usuarios)

@pytest.fixture
def cadastrar_usuario_mock(monkeypatch):
    monkeypatch.setattr("app.routes.cadastrar.cadastrar_usuario", lambda dados, foto: None)

@pytest.fixture
def verificar_permissao_true(monkeypatch):
    monkeypatch.setattr("app.routes.cadastrar.verificar_permissao_acesso", lambda username: True)

@pytest.fixture
def verificar_permissao_false(monkeypatch):
    monkeypatch.setattr("app.routes.cadastrar.verificar_permissao_acesso", lambda username: False)

def test_get_cadastrar_autenticado(client, auth, usuario_pos_vendas_mock, verificar_permissao_true):
    with client.session_transaction() as sess:
        auth(sess)
    rendered = {}
    def fake_render(tpl, **kwargs):
        rendered["tpl"] = tpl
        rendered["args"] = kwargs
        return "<html>OK</html>"
    
    cadastra_mod.render_template = fake_render

    resp = client.get("/cadastrar")
    assert resp.status_code == 200
    assert rendered["tpl"] == "cadastrar.html"
    assert "pos_vendas_usuarios" in rendered["args"]
    assert len(rendered["args"]["pos_vendas_usuarios"]) >= 1

def test_get_cadastrar_sem_login(client, verificar_permissao_true):
    resp = client.get("/cadastrar", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/index.html")

def test_get_cadastrar_sem_permissao(client, auth, verificar_permissao_false):
    with client.session_transaction() as sess:
        auth(sess)
    resp = client.get("/cadastrar", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/index.html")

def test_post_cadastrar_dados_basicos(client, auth, usuario_pos_vendas_mock, cadastrar_usuario_mock, verificar_permissao_true):
    with client.session_transaction() as sess:
        auth(sess)
    rendered = {}
    def fake_render(tpl, **kwargs):
        rendered["tpl"] = tpl
        rendered["args"] = kwargs
        return "<html>Pós</html>"
    
    cadastra_mod.render_template = fake_render

    # POST sem foto e com múltiplos pos_vendas
    resp = client.post(
        "/cadastrar",
        data={
            "username": "novo",
            "nome": "Novo Usuário",
            "pos_vendas": ["pos1", "pos2"],
            "email": "teste@teste.com"
        }
    )
    # Vai renderizar novamente o template
    assert resp.status_code == 200
    assert rendered["tpl"] == "cadastrar.html"
    # Garantir que os dados da view chegaram corretamente
    assert "pos_vendas_usuarios" in rendered["args"]

def test_post_cadastrar_sem_pos_vendas(client, auth, usuario_pos_vendas_mock, cadastrar_usuario_mock, verificar_permissao_true):
    with client.session_transaction() as sess:
        auth(sess)
    rendered = {}
    def fake_render(tpl, **kwargs):
        rendered["tpl"] = tpl
        rendered["args"] = kwargs
        return "<html>Pós</html>"
    
    cadastra_mod.render_template = fake_render

    resp = client.post(
        "/cadastrar",
        data={
            "username": "novo",
            "nome": "Novo Usuário",
            "pos_vendas": None,
            "email": "teste@teste.com"
        }
    )
    # Vai renderizar novamente o template
    assert resp.status_code == 200
    assert rendered["tpl"] == "cadastrar.html"
    # Garantir que os dados da view chegaram corretamente
    assert "pos_vendas_usuarios" in rendered["args"]

def test_post_cadastrar_com_foto(client, auth, usuario_pos_vendas_mock, cadastrar_usuario_mock, verificar_permissao_true):
    with client.session_transaction() as sess:
        auth(sess)
    rendered = {}
    def fake_render(tpl, **kwargs):
        rendered["tpl"] = tpl
        rendered["args"] = kwargs
        return "<html>FotoOK</html>"
    
    cadastra_mod.render_template = fake_render

    foto_bytes = b"12345img"
    data = {
        "username": "novo",
        "nome": "Novo Usuário",
        "pos_vendas": ["pos1"],
        "email": "foto@teste.com",
        "foto": (io.BytesIO(foto_bytes), "foto.jpg")
    }

    resp = client.post("/cadastrar", data=data, content_type="multipart/form-data", follow_redirects=True, buffered=True)
    assert resp.status_code == 200
    assert rendered["tpl"] == "cadastrar.html"

def test_post_cadastrar_sem_login(client, verificar_permissao_true):
    resp = client.post("/cadastrar", data={"username": "sem_login"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/index.html")

def test_post_cadastrar_sem_permissao(client, auth, verificar_permissao_false):
    with client.session_transaction() as sess:
        auth(sess)
    resp = client.post("/cadastrar", data={"username": "sem_permissao"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/index.html")
