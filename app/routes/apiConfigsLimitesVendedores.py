from flask import Blueprint, jsonify
from app.models import consultar_limites_vendedores

api_configs_limites_vendedores_bp = Blueprint('api_configs_limites_vendedores', __name__)

@api_configs_limites_vendedores_bp.route('/api/configs/limites_vendedores')
def api_configs_limites_vendedores():
    """
    Rota para retornar todos os limites de banco dos vendedores cadastrados nas configurações.

    Retorno:
        - JSON: Lista de limites de vendedores, cada item contendo:
            {
                "tipo": "limite_vendedor",
                "vendedor_id": <str>,
                "vendedor_nome": <str>,
                "limite": <valor>
            }
    """
    # Consulta todos os limites cadastrados para vendedores
    try:
        limites = consultar_limites_vendedores()
        return jsonify(limites)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
