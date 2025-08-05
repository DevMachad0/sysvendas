from flask import Blueprint, jsonify
from app.models import registrar_fim_expediente

api_fim_expediente_bp = Blueprint('api_fim_expediente', __name__)

@api_fim_expediente_bp.route('/api/fim_expediente', methods=['POST'])
def api_fim_expediente():
    try:
        registrar_fim_expediente()
        return jsonify({"success": True, "msg": "Fim do expediente registrado com sucesso."})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500
