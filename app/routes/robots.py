import os
from flask import Blueprint, send_from_directory

robots_bp = Blueprint('robots', __name__)

@robots_bp.route('/robots.txt')
def robots_txt():
    # Caminho absoluto do diretório "app"
    app_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(app_dir, 'robots.txt')