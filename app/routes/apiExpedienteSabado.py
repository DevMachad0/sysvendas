from flask import Blueprint, jsonify, request
from app.models import configs_collection

api_expediente_sabado_bp = Blueprint('api_expediente_sabado', __name__)

@api_expediente_sabado_bp.route('/api/expediente_sabado', methods=['GET', 'POST'])
def api_expediente_sabado():
    """
    GET: Retorna o valor atual do campo trabalho_sabado do doc tipo=fim_expediente.
    POST: Atualiza (ou cria) o campo trabalho_sabado no doc tipo=fim_expediente.
    """
    try:
        if request.method == 'GET':
            doc = configs_collection.find_one({"tipo": "fim_expediente"})
            trabalho_sabado = False
            if doc and "trabalho_sabado" in doc:
                trabalho_sabado = bool(doc["trabalho_sabado"])
            return jsonify({"trabalho_sabado": trabalho_sabado})
        else:
            data = request.json or request.form
            trabalho_sabado = bool(data.get("trabalho_sabado", False))
            configs_collection.update_one(
                {"tipo": "fim_expediente"},
                {"$set": {"trabalho_sabado": trabalho_sabado}},
                upsert=True
            )
            return jsonify({"success": True, "trabalho_sabado": trabalho_sabado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
