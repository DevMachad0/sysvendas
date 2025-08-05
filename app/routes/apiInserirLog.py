from flask import Blueprint, request, jsonify
from app.models import inserir_log

api_inserir_log_bp = Blueprint('api_inserir_log', __name__)

@api_inserir_log_bp.route('/api/inserir_log', methods=['POST'])
def api_inserir_log():
    """
    Endpoint para inserir um novo registro de log no sistema via API.

    Espera receber no body da requisição (JSON ou formulário):
        - data: Data do log (string, formato livre)
        - hora: Hora do log (string, formato livre)
        - modificacao: Descrição da modificação realizada
        - usuario: Usuário responsável pela alteração

    Retorna:
        - JSON {"success": True} se inserção for bem-sucedida
        - JSON {"success": False, "erro": "..."} com status 400 se faltarem dados
    """
    try:
        data = request.json or request.form
        data_log = data.get('data')
        hora = data.get('hora')
        modificacao = data.get('modificacao')
        usuario = data.get('usuario')
        if not (data_log and hora and modificacao and usuario):
            return jsonify({"success": False, "erro": "Dados incompletos"}), 400
        inserir_log(data_log, hora, modificacao, usuario)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
