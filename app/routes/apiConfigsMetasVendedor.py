from flask import Blueprint, jsonify, request
from app.models import salvar_meta_vendedor

api_configs_metas_vendedor_bp = Blueprint('api_configs_metas_vendedor', __name__)

@api_configs_metas_vendedor_bp.route('/api/configs/metas_vendedor', methods=['POST'])
def api_configs_metas_vendedor():
    """
    Cadastra ou atualiza as metas de um vendedor.
    Espera receber via POST (JSON ou form):
        - vendedor_id: ID do vendedor (str)
        - vendedor_nome: Nome completo do vendedor (str)
        - meta_dia_quantidade: Meta diária em quantidade de vendas (int/str)
        - meta_dia_valor: Meta diária em valor (float/str)
        - meta_semana: Meta semanal em valor (float/str)

    Retorna:
        - JSON: {"success": True} em caso de sucesso,
                {"success": False, "erro": "..."} em caso de erro de preenchimento.
    """
    try:
        data = request.json or request.form
        vendedor_id = data.get('vendedor_id', '') or ''
        vendedor_nome = data.get('vendedor_nome', '') or ''
        meta_dia_quantidade = data.get('meta_dia_quantidade') or '0'
        meta_dia_valor = data.get('meta_dia_valor') or '0'
        meta_semana = data.get('meta_semana') or '0'

        # Validação dos campos obrigatórios
        if not vendedor_id or not vendedor_nome:
            return jsonify({"success": False, "erro": "Vendedor não informado"}), 400

        # Salva ou atualiza as metas do vendedor
        salvar_meta_vendedor(vendedor_id, vendedor_nome, meta_dia_quantidade, meta_dia_valor, meta_semana)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
