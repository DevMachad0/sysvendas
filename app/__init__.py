from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from app.routes.apiConfigsGeral import api_configs_geral_bp
from app.routes.apiConfigsLimitesVendedores import api_configs_limites_vendedores_bp
from app.routes.apiConfigsLimiteVendedor import api_configs_limite_vendedor_bp
from app.routes.apiConfigsMetasVendedor import api_configs_metas_vendedor_bp
from app.routes.apiConfigsMetasVendedores import api_configs_metas_vendedores_bp
from app.routes.apiConfigsVendedores import api_configs_vendedores_bp
from app.routes.apiExpedienteSabado import api_expediente_sabado_bp
from app.routes.apiFimExpediente import api_fim_expediente_bp
from app.routes.apiInserirLog import api_inserir_log_bp
from app.routes.apiListaProdutos import api_lista_produtos_bp
from app.routes.apiNotificacoes import api_notificacoes_bp
from app.routes.apiNotificacoesMarcarLida import api_notificacoes_marcar_lida_bp
from app.routes.apiProdutoDetalhe import api_produto_detalhe_bp
from app.routes.apiProdutoUpdate import api_produto_update_bp
from app.routes.apiTestarEmail import api_testar_email_bp
from app.routes.apiUsuarios import api_usuarios_bp
from app.routes.apiVendedores import api_vendedores_bp
from app.routes.atualizarUsuario import atualizar_usuario_bp
from app.routes.baixarPdfGraficos import baixar_pdf_graficos_bp
from app.routes.barra import barra_bp
from app.routes.cadastrar import cadastra_bp
from app.routes.cadastrarVendas import cadastra_vendas_bp
from app.routes.configs import configs_bp
from app.routes.editarVenda import editar_venda_bp
from app.routes.index import index_bp
from app.routes.login import login_bp
from app.routes.logs import logs_bp
from app.routes.produtos import produtos_bp
from app.routes.receberDadosLocalstorage import recebe_dados_ls_bp
from app.routes.robots import robots_bp
from app.routes.salvarEdicaoVenda import salvar_edicao_venda_bp
from app.routes.usuarioEdicao import usuario_edicao_bp
from app.routes.usuarioEdicaoDados import usuario_edicao_dados_bp
from app.routes.usuarios import usuarios_bp
from app.routes.vendas import vendas_bp
from app.routes.erro500 import erro_500
from app.routes.apiConfigsValorAcesso import api_configs_valor_acesso_bp

def create_app(testing=False):
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()

    # Cria uma instância da aplicação Flask
    app = Flask(__name__)
    app.config['ENV'] = os.environ.get("FLASK_ENV", "production")  # Define o ambiente da aplicação (development ou production)
    app.config['DEBUG'] = os.environ.get("FLASK_DEBUG", "False") == "True"  # Ativa/desativa o modo debug com base na variável de ambiente
    app.secret_key = os.environ.get('SENHA_SESSION')  # Define a chave secreta da sessão a partir da variável de ambiente

    # Configurações de segurança para cookies de sessão
    app.config['SESSION_COOKIE_SECURE'] = True         # Só envia cookie por HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True       # Não acessível via JavaScript
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'      # Ou 'Strict' se preferir mais restrito

    if testing:
        app.config["TESTING"] = True

    # Middleware para bloquear IPs externos
    @app.before_request
    def bloquear_ips_externos():
        ip = request.remote_addr
        # Permite apenas localhost IPv4 e IPv6
        if ip not in ('127.0.0.1', '::1'):
            abort(403)

    app.register_blueprint(api_configs_geral_bp)
    app.register_blueprint(api_configs_limites_vendedores_bp)
    app.register_blueprint(api_configs_limite_vendedor_bp)
    app.register_blueprint(api_configs_metas_vendedor_bp)
    app.register_blueprint(api_configs_metas_vendedores_bp)
    app.register_blueprint(api_configs_vendedores_bp)
    app.register_blueprint(api_expediente_sabado_bp)
    app.register_blueprint(api_fim_expediente_bp)
    app.register_blueprint(api_inserir_log_bp)
    app.register_blueprint(api_lista_produtos_bp)
    app.register_blueprint(api_notificacoes_bp)
    app.register_blueprint(api_notificacoes_marcar_lida_bp)
    app.register_blueprint(api_produto_detalhe_bp)
    app.register_blueprint(api_produto_update_bp)
    app.register_blueprint(api_testar_email_bp)
    app.register_blueprint(api_usuarios_bp)
    app.register_blueprint(api_vendedores_bp)
    app.register_blueprint(atualizar_usuario_bp)
    app.register_blueprint(baixar_pdf_graficos_bp)
    app.register_blueprint(barra_bp)
    app.register_blueprint(cadastra_bp)
    app.register_blueprint(cadastra_vendas_bp)
    app.register_blueprint(configs_bp)
    app.register_blueprint(editar_venda_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(recebe_dados_ls_bp)
    app.register_blueprint(robots_bp)
    app.register_blueprint(salvar_edicao_venda_bp)
    app.register_blueprint(usuario_edicao_bp)
    app.register_blueprint(usuario_edicao_dados_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(vendas_bp)
    app.register_blueprint(api_configs_valor_acesso_bp)

    app.register_error_handler(500, erro_500)

    return app
