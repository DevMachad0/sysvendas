from flask import session
from datetime import datetime, timedelta, timezone

from app.services import is_sessao_bloqueada

def test_is_sessao_bloqueada_true(app):
    with app.test_request_context():
        # Simula um bloqueio futuro (3 minutos a partir de agora)
        futuro = datetime.now(timezone.utc) + timedelta(minutes=3)
        session["bloqueado_ate_sessao"] = futuro.isoformat()
        bloqueado, tempo = is_sessao_bloqueada()
        assert bloqueado is True
        assert 170 < tempo <= 180

def test_is_sessao_bloqueada_erro(app):
    with app.test_request_context():
        session["bloqueado_ate_sessao"] = "erro"
        bloqueado, tempo = is_sessao_bloqueada()
        assert bloqueado is False

def test_is_sessao_bloqueada_nao_str(app):
    with app.test_request_context():
        session["bloqueado_ate_sessao"] = datetime.now(timezone.utc) + timedelta(minutes=3)
        bloqueado, tempo = is_sessao_bloqueada()
        assert bloqueado is True
        assert 170 < tempo <= 180

def test_is_sessao_bloqueada_false(app):
    with app.test_request_context():
        # Não há bloqueio registrado
        session.clear()
        bloqueado, tempo = is_sessao_bloqueada()
        assert bloqueado is False
        assert tempo == 0

def test_is_sessao_bloqueada_expirado(app):
    with app.test_request_context():
        # Simula bloqueio passado
        passado = datetime.now(timezone.utc) - timedelta(minutes=1)
        session["bloqueado_ate_sessao"] = passado.isoformat()
        bloqueado, tempo = is_sessao_bloqueada()
        assert bloqueado is False
        assert tempo == 0
