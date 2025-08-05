import pytest

from app.services import enviar_email

def test_enviar_email_monta_e_envia(monkeypatch):
    # Vamos capturar o fluxo SMTP inteiro
    chamado = {}

    class FakeSMTP:
        def __init__(self, servidor, porta):
            chamado["servidor"] = servidor
            chamado["porta"] = porta
            chamado["init"] = True
        def login(self, email, senha):
            chamado["login"] = (email, senha)
        def send_message(self, msg, to_addrs):
            chamado["send_message"] = (msg, to_addrs)
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            chamado["exit"] = True

    # Monkeypatch o smtplib.SMTP_SSL
    monkeypatch.setattr("app.services.smtplib.SMTP_SSL", FakeSMTP)

    # Dados de teste
    assunto = "Teste"
    email_remetente = "rem@x.com"
    corpo = "<h1>Hello</h1>"
    servidor = "smtp.x.com"
    porta = 465
    copias = "copia1@x.com, copia2@x.com"
    email_destinatario = "dest@x.com"
    senha_email = "senha123"

    enviar_email(
        assunto=assunto,
        email_remetente=email_remetente,
        corpo=corpo,
        servidor=servidor,
        porta=porta,
        copias=copias,
        email_destinatario=email_destinatario,
        senha_email=senha_email
    )

    # Verifica o fluxo
    assert chamado["servidor"] == servidor
    assert chamado["porta"] == porta
    assert chamado["login"] == (email_remetente, senha_email)
    assert chamado["exit"] is True
    # Verifica os destinatários
    msg, to_addrs = chamado["send_message"]
    assert email_destinatario in to_addrs
    assert "copia1@x.com" in to_addrs
    assert "copia2@x.com" in to_addrs
    # Verifica assunto e corpo
    assert msg["Subject"] == assunto
    assert msg["From"] == email_remetente
    assert msg["To"] == email_destinatario
    assert msg["Cc"] == "copia1@x.com, copia2@x.com"
    # Confere que corpo HTML foi setado
    payload = msg.get_payload()
    assert any(corpo in part.get_payload(decode=True).decode() for part in payload if part.get_content_subtype() == "html")

def test_enviar_email_sem_copias(monkeypatch):
    chamado = {}

    class FakeSMTP:
        def __init__(self, servidor, porta):
            pass
        def login(self, email, senha):
            pass
        def send_message(self, msg, to_addrs):
            chamado["to"] = to_addrs
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr("app.services.smtplib.SMTP_SSL", FakeSMTP)
    enviar_email(
        assunto="Assunto",
        email_remetente="r@x.com",
        corpo="<p>Oi</p>",
        servidor="smtp.x.com",
        porta=465,
        copias="",
        email_destinatario="d@x.com",
        senha_email="s"
    )
    # Só um destinatário
    assert chamado["to"] == ["d@x.com"]
