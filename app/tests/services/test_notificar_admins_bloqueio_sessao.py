import pytest
from flask import session, request

from app.services import notificar_admins_bloqueio_sessao

def test_notificar_admins_envia_email(app, monkeypatch):
    chamados = []
    # Mocks das coleções
    class FakeUsuarios:
        def find(self, filtro, proj):
            # Simula dois admins com e-mails
            return [
                {"email": "admin1@empresa.com"},
                {"email": "admin2@empresa.com"}
            ]
    class FakeConfigs:
        def find_one(self, filtro):
            return {
                "tipo": "geral",
                "email_copia": "copi@copia.com",
                "smtp": "smtp.empresa.com",
                "porta": 465,
                "senha_email_smtp": "segredo",
                "meta_empresa": "3500000",
                "email_smtp_principal": "remetente1@empresa.com:true",
                "email_smtp_secundario": "remetente2@empresa.com:false"
            }
    def fake_enviar_email(**kwargs):
        chamados.append(kwargs)

    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuarios())
    monkeypatch.setattr("app.services.configs_collection", FakeConfigs())
    monkeypatch.setattr("app.services.enviar_email", fake_enviar_email)

    with app.test_request_context(environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        session["usuario_tentativa_login"] = "usuario_x"
        notificar_admins_bloqueio_sessao(minutos=5, tentativas=7)

    assert len(chamados) == 2
    for chamado in chamados:
        assert chamado["assunto"].startswith("Bloqueio de sessão")
        assert chamado["email_remetente"] == "remetente1@empresa.com"
        assert chamado["senha_email"] == "segredo"
        assert chamado["email_destinatario"] in ("admin1@empresa.com", "admin2@empresa.com")
        assert "usuario_x" in chamado["corpo"]
        assert "127.0.0.1" not in chamado["corpo"]  # O IP está no corpo? (ajuste conforme seu template)
        assert "minutos" in chamado["corpo"]

def test_notificar_admins_envia_email_erro(app, monkeypatch):
    chamados = []
    # Mocks das coleções
    class FakeUsuarios:
        def find(self, filtro, proj):
            # Simula dois admins com e-mails
            return [
                {"email": "admin1@empresa.com"},
                {"email": "admin2@empresa.com"}
            ]
    class FakeConfigs:
        def find_one(self, filtro):
            return {
                "tipo": "geral",
                "email_copia": "copi@copia.com",
                "smtp": "smtp.empresa.com",
                "porta": 465,
                "senha_email_smtp": "segredo",
                "meta_empresa": "3500000",
                "email_smtp_principal": "remetente1@empresa.com:true",
                "email_smtp_secundario": "remetente2@empresa.com:false"
            }

    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuarios())
    monkeypatch.setattr("app.services.configs_collection", FakeConfigs())
    monkeypatch.setattr("app.services.enviar_email", lambda x: x)

    with app.test_request_context(environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        session["usuario_tentativa_login"] = "usuario_x"
        notificar_admins_bloqueio_sessao(minutos=5, tentativas=7)

    assert len(chamados) == 0

def test_notificar_admins_config_vazio(app, monkeypatch):
    chamados = []
    # Mocks das coleções
    class FakeUsuarios:
        pass

    class FakeConfigs:
        def find_one(self, filtro):
            return {}

    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuarios())
    monkeypatch.setattr("app.services.configs_collection", FakeConfigs())
    monkeypatch.setattr("app.services.enviar_email", lambda x: x)

    with app.test_request_context(environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        session["usuario_tentativa_login"] = "usuario_x"
        notificar_admins_bloqueio_sessao(minutos=5, tentativas=7)

    assert len(chamados) == 0

def test_notificar_admins_nao_envia_sem_admin(app, monkeypatch):
    chamados = []
    class FakeUsuarios:
        def find(self, filtro, proj):
            return []
    class FakeConfigs:
        def find_one(self, filtro):
            return {
                "tipo": "geral",
                "email_copia": "copi@copia.com",
                "smtp": "smtp.empresa.com",
                "porta": 465,
                "senha_email_smtp": "segredo",
                "meta_empresa": "3500000",
                "email_smtp_principal": "remetente1@empresa.com:true",
                "email_smtp_secundario": "remetente2@empresa.com:false"
            }

    monkeypatch.setattr("app.services.usuarios_collection", FakeUsuarios())
    monkeypatch.setattr("app.services.configs_collection", FakeConfigs())
    monkeypatch.setattr("app.services.enviar_email", lambda x: x)

    with app.test_request_context():
        session["usuario_tentativa_login"] = "usuario_x"
        notificar_admins_bloqueio_sessao(minutos=5, tentativas=7)
    # Não deve chamar enviar_email
    assert len(chamados) == 0
