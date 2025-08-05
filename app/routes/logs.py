from flask import Blueprint, redirect, render_template, session
from app.models import logs_collection
from app.services import verificar_permissao_acesso
from datetime import datetime

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs', methods=['GET'])
def logs():
    """
    Rota para exibir o histórico de logs do sistema.

    - Busca todos os registros da coleção de logs.
    - Ordena os logs por data e hora em ordem decrescente (mais recentes primeiro).
    - Renderiza o template 'logs.html', passando a lista de logs.

    Returns:
        - Página HTML com o histórico dos logs.
    """
    user = session.get('user')
    if not user or not verificar_permissao_acesso(username=user.get('username')):
        return redirect('/index.html')
    
    # Busca todos os logs sem o campo _id
    logs = list(logs_collection.find({}, {"_id": 0}))

    # Ordena pela data e hora (mais recentes primeiro)
    def parse_data_hora(log):
        # Tenta extrair data e hora no formato brasileiro
        data = log.get('data', '') or ''
        hora = log.get('hora', '') or ''
        try:
            # Suporta formatos: DD/MM/YYYY e HH:MM (24h)
            dt = datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M:%S")
        except Exception:
            try:
                dt = datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
            except Exception:
                dt = datetime.min
        return dt

    logs = sorted(logs, key=parse_data_hora, reverse=True)

    return render_template('logs.html', logs=logs)
