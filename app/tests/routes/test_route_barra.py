import pytest
from flask import Flask, session, template_rendered
from app.routes.barra import barra_bp
import app.routes.barra as barra_mod

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = "test"
    app.register_blueprint(barra_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def grafico_mocks(monkeypatch):
    # Mock todas as funções de gráfico chamadas nos endpoints
    names = [
        "gerar_grafico_vendas_diarias", "gerar_grafico_vendas_geral", "gerar_grafico_vendas_vendedor",
        "gerar_grafico_status_vendas_vendedor", "gerar_grafico_metas_vendedor", "gerar_grafico_verdes_vermelhos_geral",
        "gerar_grafico_verdes_vermelhos_vendedor", "gerar_grafico_banco_vendedores", "gerar_grafico_tipo_vendas_geral",
        "gerar_grafico_tipo_vendas_por_vendedor", "gerar_grafico_metas_diarias_vendedor", "gerar_grafico_metas_semanais_vendedor",
        "gerar_grafico_mapa_vendas_por_estado", "gerar_grafico_prazo_vendas_vendedor", "gerar_grafico_produtos_mais_vendidos",
        "gerar_grafico_vendas_diarias_linhas", "gerar_grafico_quantidade_vendas_diarias",
        "gerar_grafico_vendas_fim_de_semana", "gerar_grafico_quantidade_vendas_fim_de_semana"
    ]
    for n in names:
        monkeypatch.setattr(f"app.routes.barra.{n}", lambda *a, **kw: f"<div>{n}</div>")

def test_grafico_nome_valido(client, grafico_mocks):
    nomes = [
        "vendas_geral", "vendas_vendedor", "status_vendas", "metas_vendedor", "verdes_vermelhos_geral",
        "verdes_vermelhos_vendedor", "banco_vendedores", "tipo_vendas_geral", "tipo_vendas_por_vendedor",
        "metas_diarias_vendedor", "metas_semanais_vendedor", "prazo_vendas_vendedor", "produtos_mais_vendidos",
        "vendas_diarias_linhas", "quantidade_vendas_diarias", "vendas_fim_de_semana", "quantidade_vendas_fim_de_semana"
    ]
    for nome in nomes:
        resp = client.get(f"/grafico/{nome}")
        assert resp.status_code == 200
        js = resp.get_json()
        assert "grafico_html" in js
        assert js["grafico_html"].startswith("<div>")

def test_grafico_nome_invalido(client):
    resp = client.get("/grafico/inexistente")
    assert resp.status_code == 404
    js = resp.get_json()
    assert "erro" in js
    assert js["erro"] == "Gráfico não encontrado"

def test_grafico_funcao_erro(monkeypatch, client):
    # Força exception dentro da função de gráfico
    monkeypatch.setattr("app.routes.barra.gerar_grafico_vendas_geral", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("erro fake")))
    resp = client.get("/grafico/vendas_geral")
    assert resp.status_code == 500
    js = resp.get_json()
    assert "erro" in js
    assert "Erro ao gerar gráfico" in js["erro"]

@pytest.mark.parametrize("method", ["GET", "POST"])
def test_inicio_renderiza_template(client, grafico_mocks, method):
    # Espiona render_template para conferir se template correto foi chamado
    recorded = {}
    def fake_render_template(nome, **kwargs):
        recorded["template"] = nome
        recorded["args"] = kwargs
        return "<html>OK</html>"
    barra_mod.render_template = fake_render_template

    if method == "POST":
        resp = client.post("/", data={"data": "2025-07-20"})
        # Deve redirecionar para GET com ?data=...
        assert resp.status_code == 302
        assert "data=2025-07-20" in resp.location
    else:
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.data == b"<html>OK</html>"
        # Garante que template foi renderizado
        assert recorded["template"] == "inicio.html"
        assert "grafico_vendas_diarias" in recorded["args"]
        assert "grafico_mapa_vendas_por_estado" in recorded["args"]

def test_inicio_get_com_querystring(client, grafico_mocks):
    # Testa GET com ano e mes customizados
    result = {}
    def fake_render_template(nome, **kwargs):
        result.update(kwargs)
        return "<html>Filtros</html>"
    barra_mod.render_template = fake_render_template

    resp = client.get("/?ano=2030&mes=12&data=2025-07-01")
    assert resp.status_code == 200
    assert b"Filtros" in resp.data
    assert result["ano"] == 2030
    assert result["mes"] == 12
    assert result["grafico_vendas_diarias"].startswith("<div>")
    assert result["grafico_mapa_vendas_por_estado"].startswith("<div>")

def test_inicio_post_redireciona(client, grafico_mocks):
    # POST deve redirecionar e salvar no session
    resp = client.post("/", data={"data": "2025-07-31"})
    assert resp.status_code == 302
    assert "data=2025-07-31" in resp.location
