from flask import Blueprint, jsonify, request
from app.models import configs_collection, consultar_config_geral

api_configs_geral_bp = Blueprint('api_configs_geral', __name__)

@api_configs_geral_bp.route('/api/configs/geral', methods=['GET', 'POST'])
def api_configs_geral():
    """
    API para consultar e atualizar as configurações gerais do sistema.
    """
    try:
        if request.method == 'POST':
            data = request.json or request.form
            smtp = data.get('smtp', '') or ''
            porta = data.get('porta', '') or ''
            email_copia = data.get('email_copia', '') or ''
            meta_empresa = data.get('meta_empresa') or '0'
            senha_email_smtp = data.get('senha_email_smtp', '') or ''
            email_smtp_principal = data.get('email_smtp_principal', '') or ''
            email_smtp_secundario = data.get('email_smtp_secundario', '') or ''

            if email_smtp_principal == '' and email_smtp_secundario == '':
                return jsonify({"error": "Precisa de um email smtp."}), 500

            update_dict = {
                "smtp": smtp,
                "porta": porta,
                "email_copia": email_copia,
                "meta_empresa": meta_empresa,
                "senha_email_smtp": senha_email_smtp
            }
            # Só atualiza se vier preenchido (não sobrescreve com string vazia)
            if email_smtp_principal is not None and email_smtp_principal.strip() != "":
                update_dict["email_smtp_principal"] = email_smtp_principal
            # Se vier string vazia explicitamente, remove do banco
            elif email_smtp_principal == "":
                update_dict["email_smtp_principal"] = ""

            if email_smtp_secundario is not None and email_smtp_secundario.strip() != "":
                update_dict["email_smtp_secundario"] = email_smtp_secundario
            elif email_smtp_secundario == "":
                update_dict["email_smtp_secundario"] = ""

            configs_collection.update_one(
                {"tipo": "geral"},
                {"$set": update_dict},
                upsert=True
            )
            return jsonify({"success": True})
        else:
            config = consultar_config_geral() or {}

            def parse_emailI(val):
                if isinstance(val, str) and ":" in val:
                    email, ativo = val.split(":")
                    email = email.strip()
                    ativo = ativo.strip().lower() == "true"
                    return email, ativo
                return "", False

            email_smtp_principal, email_smtp_principal_ativo = parse_emailI(config.get("email_smtp_principal", ""))
            email_smtp_secundario, email_smtp_secundario_ativo = parse_emailI(config.get("email_smtp_secundario", ""))

            config["email_smtp"] = email_smtp_principal
            config["email_smtp_principal_ativo"] = email_smtp_principal_ativo
            config["email_smtp_secundario"] = email_smtp_secundario
            config["email_smtp_secundario_ativo"] = email_smtp_secundario_ativo

            return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
