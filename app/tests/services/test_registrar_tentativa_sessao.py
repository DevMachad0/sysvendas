import pytest
from datetime import datetime, timezone
from flask import session

from app.services import registrar_tentativa_sessao

def test_registrar_tentativa_sessao_progressiva(app, monkeypatch):
    # Mock para bloquear notificação real!
    chamado = {}
    def fake_notificar_admins_bloqueio_sessao(minutos, tentativas):
        chamado["foi_chamado"] = (minutos, tentativas)

    # Substitua pelo caminho exato do seu projeto! Exemplo:
    monkeypatch.setattr("app.services.notificar_admins_bloqueio_sessao", fake_notificar_admins_bloqueio_sessao)

    with app.test_request_context():
        session.clear()
        bloqueado, tempo = registrar_tentativa_sessao()
        assert not bloqueado
        assert session["tentativas_login_sessao"] == 1

        # Simula tentativas para chegar ao bloqueio progressivo
        for _ in range(2):
            registrar_tentativa_sessao()
        bloqueado, tempo = registrar_tentativa_sessao()
        assert bloqueado
        assert 170 <= tempo <= 180

        # Verifica que o mock foi chamado!
        assert "foi_chamado" in chamado
        minutos, tentativas = chamado["foi_chamado"]
        assert minutos == 3 or minutos == 5  # depende do ciclo de bloqueio
        assert tentativas >= 3

        bloqueado, tempo_restante = registrar_tentativa_sessao()
        assert bloqueado
        assert tempo_restante > 0

def test_registrar_tentativa_sessao_bloqueio_ate_dt_erro(app, monkeypatch):
    # Mock para bloquear notificação real!
    chamado = {}
    def fake_notificar_admins_bloqueio_sessao(minutos, tentativas):
        chamado["foi_chamado"] = (minutos, tentativas)

    # Substitua pelo caminho exato do seu projeto! Exemplo:
    monkeypatch.setattr("app.services.notificar_admins_bloqueio_sessao", fake_notificar_admins_bloqueio_sessao)

    with app.test_request_context():
        session.clear()
        session["tentativas_login_sessao"] = 1
        session["bloqueado_ate_sessao"] = 'Erro'
        bloqueado, tempo = registrar_tentativa_sessao()
        assert not bloqueado
        assert session["tentativas_login_sessao"] == 2

        # Simula tentativas para chegar ao bloqueio progressivo
        for _ in range(2):
            registrar_tentativa_sessao()
        bloqueado, tempo = registrar_tentativa_sessao()
        assert bloqueado
        assert 170 <= tempo <= 180

        # Verifica que o mock foi chamado!
        assert "foi_chamado" in chamado
        minutos, tentativas = chamado["foi_chamado"]
        assert minutos == 3 or minutos == 5  # depende do ciclo de bloqueio
        assert tentativas >= 3

        bloqueado, tempo_restante = registrar_tentativa_sessao()
        assert bloqueado
        assert tempo_restante > 0

def test_registrar_tentativa_sessao_bloqueio_ate_dt_nao_str(app, monkeypatch):
    # Mock para bloquear notificação real!
    chamado = {}
    def fake_notificar_admins_bloqueio_sessao(minutos, tentativas):
        chamado["foi_chamado"] = (minutos, tentativas)

    # Substitua pelo caminho exato do seu projeto! Exemplo:
    monkeypatch.setattr("app.services.notificar_admins_bloqueio_sessao", fake_notificar_admins_bloqueio_sessao)

    with app.test_request_context():
        session.clear()
        session["tentativas_login_sessao"] = 1
        session["bloqueado_ate_sessao"] = datetime.now(timezone.utc)
        bloqueado, tempo = registrar_tentativa_sessao()
        assert not bloqueado
        assert session["tentativas_login_sessao"] == 2

        # Simula tentativas para chegar ao bloqueio progressivo
        for _ in range(2):
            registrar_tentativa_sessao()
        bloqueado, tempo = registrar_tentativa_sessao()
        assert bloqueado
        assert 170 <= tempo <= 180

        # Verifica que o mock foi chamado!
        assert "foi_chamado" in chamado
        minutos, tentativas = chamado["foi_chamado"]
        assert minutos == 3 or minutos == 5  # depende do ciclo de bloqueio
        assert tentativas >= 3

        bloqueado, tempo_restante = registrar_tentativa_sessao()
        assert bloqueado
        assert tempo_restante > 0

def test_registrar_tentativa_sessao_3_tentativas(app, monkeypatch):
    # Mock para bloquear notificação real!
    chamado = {}
    def fake_notificar_admins_bloqueio_sessao(minutos, tentativas):
        chamado["foi_chamado"] = (minutos, tentativas)

    # Substitua pelo caminho exato do seu projeto! Exemplo:
    monkeypatch.setattr("app.services.notificar_admins_bloqueio_sessao", fake_notificar_admins_bloqueio_sessao)

    with app.test_request_context():
        session.clear()
        session["tentativas_login_sessao"] = 2
        session["bloqueado_ate_sessao"] = datetime.now(timezone.utc)
        session["ultimo_bloqueio_min_sessao"] = 3
        bloqueado, tempo = registrar_tentativa_sessao()
        assert bloqueado
        assert session["tentativas_login_sessao"] == 3

def test_registrar_tentativa_sessao_3_tentativas_mais_5min(app, monkeypatch):
    # Mock para bloquear notificação real!
    chamado = {}
    def fake_notificar_admins_bloqueio_sessao(minutos, tentativas):
        chamado["foi_chamado"] = (minutos, tentativas)

    # Substitua pelo caminho exato do seu projeto! Exemplo:
    monkeypatch.setattr("app.services.notificar_admins_bloqueio_sessao", fake_notificar_admins_bloqueio_sessao)

    with app.test_request_context():
        session.clear()
        session["tentativas_login_sessao"] = 2
        session["bloqueado_ate_sessao"] = datetime.now(timezone.utc)
        session["ultimo_bloqueio_min_sessao"] = 5
        bloqueado, tempo = registrar_tentativa_sessao()
        assert bloqueado
        assert session["tentativas_login_sessao"] == 3
