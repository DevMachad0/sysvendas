from flask import Blueprint, jsonify, request
import smtplib
from email.message import EmailMessage

api_testar_email_bp = Blueprint('api_testar_email', __name__)

@api_testar_email_bp.route('/api/testar_email', methods=['POST'])
def api_testar_email():
    """
    Testa o envio de e-mail SMTP com as configurações fornecidas.
    Envia um e-mail de teste para o e-mail SMTP principal e para os e-mails de cópia.
    """
    try:
        data = request.json or request.form
        smtp = data.get('smtp') or ''
        porta = int(data.get('porta') or 465)
        email_smtp = data.get('email_smtp') or ''
        senha_email_smtp = data.get('senha_email_smtp') or ''
        email_copia = data.get('email_copia', '') or ''

        try:
            msg = EmailMessage()
            msg['Subject'] = 'Teste de E-mail SMTP - Sistema de Vendas'
            msg['From'] = email_smtp
            msg['To'] = email_smtp
            if email_copia:
                copias = [e.strip() for e in email_copia.split(',') if e.strip()]
                msg['Cc'] = ', '.join(copias)
            msg.set_content('Este é um e-mail de teste do sistema de vendas.\nSe você recebeu este e-mail, as configurações estão corretas.')

            with smtplib.SMTP_SSL(smtp, porta, timeout=15) as server:
                server.login(email_smtp, senha_email_smtp)
                server.send_message(msg)
            # Sempre retorna 200 em caso de sucesso
            return jsonify({"success": True, "msg": "E-mail de teste enviado com sucesso!"}), 200
        except Exception as e:
            # Só retorna 400 em caso de erro real
            return jsonify({"success": False, "msg": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
