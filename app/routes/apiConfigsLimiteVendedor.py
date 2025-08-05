from flask import Blueprint, jsonify, request
from app.models import salvar_limite_vendedor

api_configs_limite_vendedor_bp = Blueprint('api_configs_limite_vendedor', __name__)

@api_configs_limite_vendedor_bp.route('/api/configs/limite_vendedor', methods=['POST'])
def api_configs_limite_vendedor():
    """
    Rota para salvar/atualizar o limite do banco de um vendedor específico nas configurações.

    Requisição:
        - Método: POST
        - Parâmetros esperados (JSON ou form):
            vendedor_id: str  -> ID do vendedor.
            vendedor_nome: str -> Nome completo do vendedor.
            limite: float      -> Valor do limite de banco.

    Retorno:
        - JSON: {"success": True} em caso de sucesso.
    """
    try:
        data = request.json or request.form
        vendedor_id = data.get('vendedor_id', '') or ''
        vendedor_nome = data.get('vendedor_nome', '') or ''
        limite = data.get('limite') or '0'
        salvar_limite_vendedor(vendedor_id, vendedor_nome, limite)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
