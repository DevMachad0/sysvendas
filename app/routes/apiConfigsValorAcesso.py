from flask import Blueprint, request, jsonify
from app.models import configs_collection

api_configs_valor_acesso_bp = Blueprint('api_configs_valor_acesso', __name__)

@api_configs_valor_acesso_bp.route('/api/configs/valor_acesso', methods=['GET', 'POST'])
def valor_acesso():
    try:
        if request.method == 'GET':
            doc = configs_collection.find_one({'tipo': 'valor_acesso'}, {'_id': 0})
            if not doc:
                # Retorna valores padrão se não existir
                return jsonify({
                    "valor_acesso_nova_venda": "",
                    "valor_acesso_atualizacao": ""
                })
            return jsonify({
                "valor_acesso_nova_venda": doc.get("valor_acesso_nova_venda", ""),
                "valor_acesso_atualizacao": doc.get("valor_acesso_atualizacao", "")
            })
        elif request.method == 'POST':
            data = request.json or request.form
            valor_nova = data.get("valor_acesso_nova_venda", "0") or "0"
            valor_atualizacao = data.get("valor_acesso_atualizacao", "0") or "0"
            configs_collection.update_one(
                {"tipo": "valor_acesso"},
                {"$set": {
                    "valor_acesso_nova_venda": valor_nova,
                    "valor_acesso_atualizacao": valor_atualizacao,
                    "tipo": "valor_acesso"
                }},
                upsert=True
            )
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
