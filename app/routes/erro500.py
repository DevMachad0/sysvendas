from flask import Blueprint, render_template, request

erro_bp = Blueprint('erro', __name__)

@erro_bp.errorhandler(500)
def erro_500(e):
    """
    Handler para erro 500. Redireciona para a página erro.html informando a página que apresentou erro.
    """
    pagina = getattr(request, "endpoint", None) or request.path or "desconhecida"
    return render_template('erro.html', pagina_erro=pagina), 500
