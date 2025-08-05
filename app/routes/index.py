from flask import Blueprint, render_template

index_bp = Blueprint('index', __name__)

@index_bp.route('/index.html', methods=['GET', 'POST'])
def index_html():
    """
    Rota auxiliar para renderizar o template 'index.html'.

    Esta rota pode ser usada para servir uma página estática inicial, 
    de apresentação ou tela de login personalizada, dependendo da estrutura do projeto.
    """

    return render_template('index.html')