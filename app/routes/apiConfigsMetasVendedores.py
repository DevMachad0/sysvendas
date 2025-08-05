from flask import Blueprint, jsonify
from app.models import consultar_metas_vendedores

api_configs_metas_vendedores_bp = Blueprint('api_configs_metas_vendedores', __name__)

@api_configs_metas_vendedores_bp.route('/api/configs/metas_vendedores')
def api_configs_metas_vendedores():
    """
    Retorna todas as metas de dia, semana e mês cadastradas por vendedor.

    GET:
        - Sem parâmetros.

    Retorno:
        - JSON com uma lista de metas (um dicionário por vendedor):
            [
                {
                    "tipo": "meta_vendedor",
                    "vendedor_id": ...,
                    "vendedor_nome": ...,
                    "meta_dia_quantidade": ...,
                    "meta_dia_valor": ...,
                    "meta_semana": ...
                },
                ...
            ]
    """
    try:
        metas = consultar_metas_vendedores()
        return jsonify(metas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
