import pytest
from app.routes.erro500 import erro_bp

@pytest.fixture
def app_with_erro_bp(app):
    # Registra explicitamente o erro_bp (caso não esteja já no app principal)
    app.register_blueprint(erro_bp)
    return app

def test_erro_500_renderiza_template(client, app_with_erro_bp):
    # Cria rota fake que gera erro
    @app_with_erro_bp.route('/rota_erro_500')
    def rota_erro():
        raise Exception("Falha de propósito!")
    
    # Desabilita a propagação de exceções para que o Flask trate o erro
    app_with_erro_bp.config['PROPAGATE_EXCEPTIONS'] = False

    resp = client.get('/rota_erro_500')
    assert resp.status_code == 500
    assert b'erro.html' in resp.data or b'erro' in resp.data

def test_erro_500_fallback_path(client, app_with_erro_bp):
    @app_with_erro_bp.route('/falha')
    def falha():
        raise Exception("Crash!")
    app_with_erro_bp.config['PROPAGATE_EXCEPTIONS'] = False
    resp = client.get('/falha')
    assert resp.status_code == 500
    assert b'falha' in resp.data or b'desconhecida' in resp.data
