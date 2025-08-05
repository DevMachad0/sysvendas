import pytest

from app.services import gerar_pdf_graficos

def test_gerar_pdf_graficos_nenhum_selecionado(app):
    with app.test_request_context():
        resposta = gerar_pdf_graficos([], "relatorio", 2025, 7)
        assert resposta == ("Nenhum gráfico selecionado.", None)

def test_gerar_pdf_graficos_gera_pdf(monkeypatch, app):
    # Mocks dos gráficos
    fake_figura = object()
    def fake_gerar_fig_vendas_geral(soma_vendas):
        return fake_figura

    # Mock do write_image
    chamado_write = {}
    def fake_write_image(figura, caminho, format, width, height, scale):
        chamado_write[caminho] = figura

    # Mock do canvas.Canvas e seus métodos
    class FakeCanvas:
        def __init__(self, buffer, pagesize):
            self.salvou = False
        def setFont(self, *a, **kw): pass
        def drawRightString(self, *a, **kw): pass
        def showPage(self): pass
        def drawImage(self, *a, **kw): pass
        def save(self): self.salvou = True

    # Mock do TemporaryDirectory
    class FakeTempDir:
        def __enter__(self): return "/tmp"
        def __exit__(self, *a): pass

    # Patching!
    monkeypatch.setattr("app.services.gerar_fig_vendas_geral", fake_gerar_fig_vendas_geral)
    monkeypatch.setattr("app.services.soma_vendas", lambda x: x)
    monkeypatch.setattr("app.services.pio.write_image", fake_write_image)
    monkeypatch.setattr("app.services.canvas.Canvas", FakeCanvas)
    monkeypatch.setattr("app.services.ImageReader", lambda p: object())
    monkeypatch.setattr("app.services.tempfile.TemporaryDirectory", lambda: FakeTempDir())

    # Chama a função com um gráfico válido
    with app.test_request_context():
        selecao = ["vendas_geral"]
        buffer_pdf, nome_arquivo = gerar_pdf_graficos(selecao, "relatorio", 2025, 7)
        assert hasattr(buffer_pdf, "read")  # É um buffer, deve ter read()
        assert nome_arquivo == "relatorio_7_2025.pdf"
        # Confere que o write_image foi chamado
        assert any("grafico_vendas_geral.png" in k for k in chamado_write)

def test_gerar_pdf_graficos_gera_pdf_mais_de_um_escolhido(monkeypatch, app):
    # Mocks dos gráficos
    fake_figura = object()
    def fake_gerar_fig_vendas_geral(soma_vendas):
        return fake_figura

    # Mock do write_image
    chamado_write = {}
    def fake_write_image(figura, caminho, format, width, height, scale):
        chamado_write[caminho] = figura

    # Mock do canvas.Canvas e seus métodos
    class FakeCanvas:
        def __init__(self, buffer, pagesize):
            self.salvou = False
        def setFont(self, *a, **kw): pass
        def drawRightString(self, *a, **kw): pass
        def showPage(self): pass
        def drawImage(self, *a, **kw): pass
        def save(self): self.salvou = True

    # Mock do TemporaryDirectory
    class FakeTempDir:
        def __enter__(self): return "/tmp"
        def __exit__(self, *a): pass

    # Patching!
    monkeypatch.setattr("app.services.gerar_fig_vendas_geral", fake_gerar_fig_vendas_geral)
    monkeypatch.setattr("app.services.soma_vendas", lambda x: x)
    monkeypatch.setattr("app.services.pio.write_image", fake_write_image)
    monkeypatch.setattr("app.services.canvas.Canvas", FakeCanvas)
    monkeypatch.setattr("app.services.ImageReader", lambda p: object())
    monkeypatch.setattr("app.services.tempfile.TemporaryDirectory", lambda: FakeTempDir())

    # Chama a função com um gráfico válido
    with app.test_request_context():
        selecao = ["vendas_geral", "banco_vendedores"]
        buffer_pdf, nome_arquivo = gerar_pdf_graficos(selecao, "relatorio", 2025, 7)
        assert hasattr(buffer_pdf, "read")  # É um buffer, deve ter read()
        assert nome_arquivo == "relatorio_7_2025.pdf"
        # Confere que o write_image foi chamado
        assert any("grafico_vendas_geral.png" in k for k in chamado_write)
