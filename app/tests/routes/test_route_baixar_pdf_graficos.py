import io
import pytest
import importlib
import sys
import types

from flask import Flask
from app.routes.baixarPdfGraficos import baixar_pdf_graficos_bp

@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(baixar_pdf_graficos_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_not_allowed(client):
    # Teste para GET, deve retornar 405
    resp = client.get('/baixar-pdf-graficos')
    assert resp.status_code == 405
    assert "Método não permitido" in resp.get_data(as_text=True)

def test_post_faltando_graficos_ou_nome(client):
    # Teste para POST sem gráficos selecionados
    resp = client.post('/baixar-pdf-graficos', data={"nome": "relatorio"})
    assert resp.status_code == 400
    assert "Selecione ao menos um gráfico" in resp.get_data(as_text=True)

    # Teste para POST sem nome_base
    resp = client.post('/baixar-pdf-graficos', data={"graficos": ["graf1"]})
    assert resp.status_code == 400
    assert "Nenhum gráfico selecionado." in resp.get_data(as_text=True)

def test_post_pdf_ok(monkeypatch, client):
    # Mock para simular PDF gerado
    def fake_gerar_pdf_graficos(selecao, nome_base, ano, mes):
        return io.BytesIO(b"%PDF-1.4 test pdf"), f"{nome_base}.pdf"
    monkeypatch.setattr("app.routes.baixarPdfGraficos.gerar_pdf_graficos", fake_gerar_pdf_graficos)

    resp = client.post('/baixar-pdf-graficos', data={
        "nome": "relatorio",
        "graficos": ["graf1", "graf2"],
        "ano": 2025,
        "mes": 7
    })
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.headers["Content-Disposition"].endswith('.pdf')

def test_post_pdf_erro_string(monkeypatch, client):
    # Mock que retorna uma string (erro na geração do PDF)
    def fake_gerar_pdf_graficos(selecao, nome_base, ano, mes):
        return "Erro ao gerar PDF", None
    monkeypatch.setattr("app.routes.baixarPdfGraficos.gerar_pdf_graficos", fake_gerar_pdf_graficos)

    resp = client.post('/baixar-pdf-graficos', data={
        "nome": "relatorio",
        "graficos": ["graf1"],
        "ano": 2025,
        "mes": 7
    })
    assert resp.status_code == 400
    assert "Erro ao gerar PDF" in resp.get_data(as_text=True)

def test_post_pdf_exception(monkeypatch, client):
    # Mock que levanta exceção (simula erro interno)
    def fake_gerar_pdf_graficos(selecao, nome_base, ano, mes):
        raise RuntimeError("Falha inesperada")
    monkeypatch.setattr("app.routes.baixarPdfGraficos.gerar_pdf_graficos", fake_gerar_pdf_graficos)

    resp = client.post('/baixar-pdf-graficos', data={
        "nome": "relatorio",
        "graficos": ["graf1"]
    })
    assert resp.status_code == 500
    assert "Erro ao gerar o PDF dos gráficos" in resp.get_data(as_text=True)

def test_pdf_reload_matplotlib(client, monkeypatch):
    # Simula que 'matplotlib.pyplot' já está em sys.modules
    sys.modules['matplotlib'] = importlib.import_module('matplotlib')
    sys.modules['matplotlib.pyplot'] = types.ModuleType('matplotlib.pyplot')

    # Agora, quando a rota for chamada, ela vai cair no if!
    resp = client.post('/baixar-pdf-graficos', data={
        'ano': 2025,
        'mes': 7,
        'nome': 'teste',
        'graficos': ['grafico1']
    })
    # Aqui pode checar o status, ou apenas rodar para cobrir a linha
    assert resp.status_code in (200, 400)  # depende da lógica, só não pode dar erro

    # Limpa para não afetar outros testes!
    del sys.modules['matplotlib.pyplot']
