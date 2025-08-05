from app.models import (
    criar_usuario, nova_venda, usuarios_collection, vendas_collection, produtos_collection, cadastrar_produto, configs_collection, notificacoes_collection
)
import bcrypt  # Biblioteca para hashing seguro de senhas
import smtplib  # Envio de e-mails via SMTP
from email.message import EmailMessage  # Criação de mensagens de e-mail
from datetime import datetime, time, timedelta, timezone  # Manipulação de datas e horas
import plotly.io as pio  # Utilitário para exportar gráficos Plotly
from reportlab.pdfgen import canvas  # Geração de PDFs com ReportLab
from reportlab.lib.pagesizes import landscape, A4  # Tamanho de página padrão A4 para PDFs
from reportlab.lib.utils import ImageReader  # Utilitário para inserir imagens em PDF
import os  # Operações de sistema de arquivos
import tempfile  # Criação de arquivos temporários
from io import BytesIO  # Manipulação de fluxos de bytes em memória
import time  # Utilitário para medições de tempo
from app.download import *  # Importa funções utilitárias de download (ajuste conforme sua estrutura)
from app.utils import soma_vendas
from flask import session, request
from pymongo import ASCENDING

# Coleção para bloqueios de IP (crie no MongoDB se necessário)
from app.models import db
ip_bloqueios_collection = db['ip_bloqueios']

def usuario_logado():
    """
    Retorna se há um usuário logado no sistema.

    Returns:
        bool: False sempre, função exemplo/stub.
    """
    # No momento, retorna sempre False (função stub/exemplo)
    return False

def cadastrar_usuario(data, foto=None):
    """
    Cadastra um novo usuário no sistema.

    Args:
        data (dict): Dicionário contendo os dados do usuário.
        foto (str, optional): Foto do usuário em base64, se fornecida.

    Returns:
        InsertOneResult: Resultado da inserção no banco de dados.
    """
    return criar_usuario(
        nome_completo=data.get('nome_completo'),
        username=data.get('username'),
        email=data.get('email'),
        senha=data.get('senha'),
        fone=data.get('n_vendedor'),
        tipo=data.get('tipo'),
        foto=foto,
        pos_vendas=data.get('pos_vendas'),
        meta_mes=data.get('meta_mes')
    )

def cadastrar_venda(usuario_id, venda_data):
    """
    Cadastra uma nova venda no sistema e envia um e-mail de notificação se a senha de e-mail for fornecida.

    Args:
        usuario_id (ObjectId): ID do usuário responsável pela venda.
        venda_data (dict): Dados da venda.
        senha_email (str, optional): Senha do e-mail do vendedor (necessária para envio do e-mail).
        email_posvendas (str, optional): E-mail do pós-vendas (para cópia).
        copias (str, optional): E-mails adicionais em cópia.

    Returns:
        InsertOneResult: Resultado da inserção no banco de dados.
    """
    # Busca o vendedor atribuído pelo nome (pode ser username ou nome_completo)
    vendedor_nome = venda_data.get("vendedor")
    vendedor_doc = usuarios_collection.find_one({
        "$or": [
            {"nome_completo": vendedor_nome},
            {"username": vendedor_nome}
        ],
        "tipo": {"$in": ["vendedor", "Vendedor"]}
    })

    # Define o posvendas da venda com base no vendedor atribuído
    posvendas_vendedor = ""
    if vendedor_doc:
        posvendas_vendedor = vendedor_doc.get("pos_vendas", "")

    # Garante que o campo posvendas da venda seja preenchido corretamente
    venda_data["posvendas"] = posvendas_vendedor

    condicoes = ''

    # Padroniza os campos para evitar bugs com espaços, maiúsculas/minúsculas e tipos
    valor_entrada = str(venda_data['valor_entrada'] or '').strip()
    condicoes_nome = (venda_data['condicoes'] or '').replace(' ', '').strip().lower()
    condicoes_venda = (venda_data['condicoes_venda'] or '').strip().lower()

    # Testa se tem entrada (> 0 ou diferente de vazio/'0')
    tem_entrada = valor_entrada not in ['', '0', 0, None]

    # Testa se é 1+1 (independente de espaço)
    is_1mais1 = condicoes_nome in ['a/c|1+1']

    # Testa se condição venda é 'entrada + parcela' ou 'à vista'
    is_entrada_parcela = condicoes_venda == 'entrada_parcela'
    is_avista = condicoes_venda in ['à vista', 'avista']

    qtn_parcelas = venda_data['condicoes'].strip().split('|')

    if tem_entrada and is_1mais1 and is_entrada_parcela:
        condicoes = f"Entrada de R${valor_entrada} e uma parcela de R${venda_data['valor_parcelas']}\n"
    elif not tem_entrada and is_1mais1 and is_avista:
        condicoes = f"À vista de R${venda_data['valor_venda_avista']}\n"
    elif not tem_entrada and not is_1mais1:
        condicoes = f"{qtn_parcelas[1]} R${venda_data['valor_parcelas']}\n"
    elif tem_entrada and not is_1mais1:
        condicoes = f"Entrada de R${valor_entrada} e {qtn_parcelas[1]} R${venda_data['valor_parcelas']}\n"

    data_prestacao = venda_data['data_prestacao_inicial'].split('-')


    # Monta o corpo do e-mail com os dados da venda
    corpo_email = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
  </head>
  <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
    <h2>Dados Pessoais</h2>
    <p><strong>NOME/RAZÃO SOCIAL:</strong> {venda_data['nome'].upper()}<br>
       <strong>CONTATO:</strong> {venda_data['nome_do_contato'].upper()}<br>
       <strong>CPF/CNPJ:</strong> {venda_data['cnpj_cpf']}<br>
       <strong>IE:</strong> {venda_data['inscricao_estadual_identidade']}<br>
       <strong>E-MAIL:</strong> {venda_data['email'].lower()}<br>
       <strong>TELEFONES:</strong> {venda_data['fones']}</p>

    <h2>Endereço</h2>
    <p><strong>RUA:</strong> {venda_data['endereco']['rua'].upper()}<br>
       <strong>BAIRRO:</strong> {venda_data['endereco']['bairro'].upper()}<br>
       <strong>NÚMERO:</strong> {venda_data['endereco']['numero'].upper()}<br>
       <strong>CIDADE:</strong> {venda_data['endereco']['cidade'].upper()}<br>
       <strong>ESTADO:</strong> {venda_data['endereco']['estado'].upper()}<br>
       <strong>CEP:</strong> {venda_data['cep']}</p>

    <h2>Dados da Venda</h2>
    <p><strong>PRODUTO:</strong> {venda_data['produto'].upper()}<br>
       <strong>CONDIÇÕES:</strong> {condicoes.upper()}<br>
       <strong>PRESTAÇÃO INICIAL:</strong> {data_prestacao[2]}/{data_prestacao[1]}/{data_prestacao[0]}<br>
       <strong>VALOR TOTAL DO PRODUTO:</strong> R${venda_data['valor_real']}<br>
       <strong>TIPO DE ENVIO DE BOLETO:</strong> {venda_data['tipo_envio_boleto'].upper()}<br>
       <strong>VENDEDOR:</strong> {venda_data['vendedor'].upper()}</p>

    <h2>Observações</h2>
    <p>{venda_data['obs'].upper()}</p><br><br>

    <hr>
    <p style="font-size: 12px; color: gray;">E-mail gerado automaticamente pelo sistema.</p>
  </body>
</html>
"""
    # Se houver senha de e-mail, envia a notificação para o vendedor e cópias
    info_envio = configs_collection.find_one({'tipo': 'geral'})
    email_principal = info_envio['email_smtp_principal'].split(':')[1]
    email_secundario = info_envio['email_smtp_secundario'].split(':')[1]
    servidor = info_envio['smtp']
    porta = info_envio['porta']
    copias = info_envio['email_copia']
    senha_email = info_envio['senha_email_smtp']

    if email_principal == 'true':
        email_remetente = info_envio['email_smtp_principal'].split(':')[0]
    elif email_secundario == 'true':
        email_remetente = info_envio['email_smtp_secundario'].split(':')[0]

    enviar_email(
        assunto=f'{venda_data['nome'].title()}',
        email_remetente=email_remetente,
        corpo=corpo_email,
        copias=copias,
        senha_email=senha_email,
        email_destinatario=vendedor_doc['email'],
        servidor=servidor,
        porta=porta
    )

    # Insere a venda no banco de dados
    return nova_venda(
        usuario_id=usuario_id,
        numero_da_venda=venda_data.get("numero_da_venda"),
        nome=venda_data.get("nome"),
        nome_do_contato=venda_data.get("nome_do_contato"),
        endereco=venda_data.get("endereco"),
        cep=venda_data.get("cep"),
        cnpj_cpf=venda_data.get("cnpj_cpf"),
        razao_social=venda_data.get("razao_social"),
        inscricao_estadual_identidade=venda_data.get("inscricao_estadual_identidade"),
        produto=venda_data.get("produto"),
        valor_tabela=venda_data.get("valor_tabela"),
        condicoes=venda_data.get("condicoes"),
        valor_parcelas=venda_data.get("valor_parcelas"),
        quantidade_acessos=venda_data.get("quantidade_acessos", 2),  # novo campo, padrão 2
        data_prestacao_inicial=venda_data.get("data_prestacao_inicial"),
        tipo_envio_boleto=venda_data.get("tipo_envio_boleto"),
        tipo_remessa=venda_data.get("tipo_remessa"),
        email=venda_data.get("email"),
        fones=venda_data.get("fones"),
        fone_vendedor=venda_data.get("fone_vendedor"),
        email_vendedor=venda_data.get("email_vendedor"),
        vendedor=venda_data.get("vendedor"),
        obs=venda_data.get("obs"),
        status=venda_data.get("status"),
        posvendas=posvendas_vendedor,  # sempre o pós-vendas do vendedor atribuído
        data_criacao=venda_data.get("data_criacao"),
        data_real=venda_data.get("data_real", datetime.now()),
        valor_real=venda_data.get("valor_real"),
        tipo_cliente=venda_data.get("tipo_cliente"),
        logs=venda_data.get("logs"),
        desconto_autorizado=venda_data.get("desconto_autorizado"),  # novo campo
        caminho_arquivos=venda_data.get("caminho_arquivos", ""),
        obs_vendas=venda_data.get("obs_vendas", ""),
        valor_entrada=venda_data.get("valor_entrada"),                 # NOVO
        valor_venda_avista=venda_data.get("valor_venda_avista"),       # NOVO
        condicoes_venda=venda_data.get("condicoes_venda")              # NOVO
    )

def reenviar_venda(data):
    condicoes = ''
    vendedor_nome = data.get("quem")
    vendedor_doc = usuarios_collection.find_one({
        "$or": [
            {"nome_completo": vendedor_nome},
            {"username": vendedor_nome}
        ],
        "tipo": {"$in": ["vendedor", "Vendedor"]}
    })

    # Padroniza os campos para evitar bugs com espaços, maiúsculas/minúsculas e tipos
    valor_entrada = str(data.get('valor_entrada', '')).strip()
    condicoes_nome = (data.get('condicoes', '')).replace(' ', '').strip().lower()
    condicoes_venda = (data.get('condicoes_venda', '')).strip().lower()

    # Testa se tem entrada (> 0 ou diferente de vazio/'0')
    tem_entrada = valor_entrada not in ['', '0', 0, None]

    # Testa se é 1+1 (independente de espaço)
    is_1mais1 = condicoes_nome in ['a/c|1+1']

    # Testa se condição venda é 'entrada + parcela' ou 'à vista'
    is_entrada_parcela = condicoes_venda == 'entrada_parcela'
    is_avista = condicoes_venda in ['à vista', 'avista']

    qtn_parcelas = data.get('condicoes').strip().split('|')

    if tem_entrada and is_1mais1 and is_entrada_parcela:
        condicoes = f"Entrada de R${valor_entrada} e uma parcela de R${data.get('valor_parcelas')}\n"
    elif not tem_entrada and is_1mais1 and is_avista:
        condicoes = f"À vista de R${data.get('valor_venda_avista')}\n"
    elif not tem_entrada and not is_1mais1:
        condicoes = f"{qtn_parcelas[1]} R${data.get('valor_parcelas')}\n"
    elif tem_entrada and not is_1mais1:
        condicoes = f"Entrada de R${valor_entrada} e {qtn_parcelas[1]} R${data.get('valor_parcelas')}\n"

    data_prestacao = data.get('data_prestacao_inicial').split('-')


    # Monta o corpo do e-mail com os dados da venda
    corpo_email = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
    <h2>Dados Pessoais</h2>
    <p><strong>NOME/RAZÃO SOCIAL:</strong> {data.get('nome').upper()}<br>
    <strong>CONTATO:</strong> {data.get('nome_do_contato').upper()}<br>
    <strong>CPF/CNPJ:</strong> {data.get('cnpj_cpf')}<br>
    <strong>IE:</strong> {data.get('inscricao_estadual_identidade')}<br>
    <strong>E-MAIL:</strong> {data.get('email').lower()}<br>
    <strong>TELEFONES:</strong> {data.get('fones')}</p>

    <h2>Endereço</h2>
    <p><strong>RUA:</strong> {data.get('endereco_rua').upper()}<br>
    <strong>BAIRRO:</strong> {data.get('endereco_bairro').upper()}<br>
    <strong>NÚMERO:</strong> {data.get('endereco_numero').upper()}<br>
    <strong>CIDADE:</strong> {data.get('endereco_cidade').upper()}<br>
    <strong>ESTADO:</strong> {data.get('endereco_estado').upper()}<br>
    <strong>CEP:</strong> {data.get('cep')}</p>

    <h2>Dados da Venda</h2>
    <p><strong>PRODUTO:</strong> {data.get('produto').upper()}<br>
    <strong>CONDIÇÕES:</strong> {condicoes.upper()}<br>
    <strong>PRESTAÇÃO INICIAL:</strong> {data_prestacao[2]}/{data_prestacao[1]}/{data_prestacao[0]}<br>
    <strong>VALOR TOTAL DO PRODUTO:</strong> R${data.get('valor_real')}<br>
    <strong>TIPO DE ENVIO DE BOLETO:</strong> {data.get('tipo_envio_boleto').upper()}<br>
    <strong>VENDEDOR:</strong> {data.get('quem').upper()}</p>

    <h2>Observações</h2>
    <p>{data.get('obs').upper()}</p><br><br>

    <hr>
    <p style="font-size: 12px; color: gray;">E-mail gerado automaticamente pelo sistema.</p>
</body>
</html>
"""
    # Se houver senha de e-mail, envia a notificação para o vendedor e cópias
    info_envio = configs_collection.find_one({'tipo': 'geral'})
    email_principal = info_envio['email_smtp_principal'].split(':')[1]
    email_secundario = info_envio['email_smtp_secundario'].split(':')[1]
    servidor = info_envio['smtp']
    porta = info_envio['porta']
    copias = info_envio['email_copia']
    senha_email = info_envio['senha_email_smtp']

    if email_principal == 'true':
        email_remetente = info_envio['email_smtp_principal'].split(':')[0]
    elif email_secundario == 'true':
        email_remetente = info_envio['email_smtp_secundario'].split(':')[0]

    enviar_email(
        assunto=f'REENVIO - {data.get('nome').title()}',
        email_remetente=email_remetente,
        corpo=corpo_email,
        copias=copias,
        senha_email=senha_email,
        email_destinatario=vendedor_doc['email'],
        servidor=servidor,
        porta=porta
    )

def gerar_numero_venda():
    """
    Gera um número sequencial único para uma nova venda, baseado no ano e mês atual.
    O formato é 'yyyymmNNNN', onde NNNN é o sequencial no mês.

    Returns:
        str: Novo número de venda gerado.
    """
    now = datetime.now()
    ano_mes = now.strftime('%Y%m')  # Ex: 202406
    # Busca a última venda cadastrada no mês corrente
    prefixo = f"{ano_mes}"
    ultima = vendas_collection.find_one(
        {"numero_da_venda": {"$regex": f"^{prefixo}"}},
        sort=[("numero_da_venda", -1)]
    )
    # Se encontrou alguma, incrementa o sequencial, senão começa em 1
    if ultima and "numero_da_venda" in ultima:
        ultimo_seq = int(ultima["numero_da_venda"][-4:])
        novo_seq = ultimo_seq + 1
    else:
        novo_seq = 1
    # Retorna no formato: 2024060001, 2024060002, etc
    return f"{prefixo}{novo_seq:04d}"

def incrementar_tentativas_login(username):
    """
    Incrementa o contador de tentativas de login do usuário.
    Se atingir 3 tentativas, bloqueia o usuário automaticamente.
    """
    usuario = usuarios_collection.find_one({"username": username})
    if not usuario:
        return
    tentativas = usuario.get("tentativas_login", 0) + 1
    update = {"tentativas_login": tentativas}
    if tentativas >= 3:
        update["status"] = "bloqueado"
    usuarios_collection.update_one({"username": username}, {"$set": update})

def resetar_tentativas_login(username):
    """
    Reseta o contador de tentativas de login do usuário para zero.
    """
    usuarios_collection.update_one({"username": username}, {"$set": {"tentativas_login": 0}})

def registrar_tentativa_sessao():
    """
    Incrementa tentativas de login inválidas na sessão.
    Se atingir múltiplos de 3, bloqueia a sessão por tempo progressivo:
    1º bloqueio: 3min, 2º: 5min, depois +5min a cada novo bloqueio.
    """
    if "tentativas_login_sessao" not in session:
        session["tentativas_login_sessao"] = 1
        session["bloqueado_ate_sessao"] = None
        session["ultimo_bloqueio_min_sessao"] = 0
    else:
        session["tentativas_login_sessao"] += 1

    tentativas = session["tentativas_login_sessao"]
    ultimo_bloqueio_min = session.get("ultimo_bloqueio_min_sessao", 0)
    bloqueado_ate = session.get("bloqueado_ate_sessao")

    agora = datetime.now(timezone.utc)
    bloqueado_ate_dt = None
    if bloqueado_ate:
        if isinstance(bloqueado_ate, str):
            try:
                bloqueado_ate_dt = datetime.fromisoformat(bloqueado_ate)
            except Exception:
                bloqueado_ate_dt = None
        else:
            bloqueado_ate_dt = bloqueado_ate
    # Se já está bloqueado e ainda não expirou
    if bloqueado_ate_dt and bloqueado_ate_dt > agora:
        return True, (bloqueado_ate_dt - agora).total_seconds()
    # Se atingiu múltiplo de 3 tentativas, bloqueia progressivamente
    if tentativas % 3 == 0:
        # Lógica de bloqueio progressivo: 3min, 5min, depois +5min
        if ultimo_bloqueio_min == 0:
            novo_bloqueio_min = 3
        elif ultimo_bloqueio_min == 3:
            novo_bloqueio_min = 5
        else:
            novo_bloqueio_min = ultimo_bloqueio_min + 5
        bloqueado_ate = agora + timedelta(minutes=novo_bloqueio_min)
        session["bloqueado_ate_sessao"] = bloqueado_ate.isoformat()
        session["ultimo_bloqueio_min_sessao"] = novo_bloqueio_min
        notificar_admins_bloqueio_sessao(novo_bloqueio_min, tentativas)
        return True, novo_bloqueio_min * 60
    else:
        return False, 0

def is_sessao_bloqueada():
    """
    Verifica se a sessão está bloqueada.
    """
    bloqueado_ate = session.get("bloqueado_ate_sessao")
    if bloqueado_ate:
        # Garante que bloqueado_ate seja datetime com timezone
        if isinstance(bloqueado_ate, str):
            try:
                bloqueado_ate_dt = datetime.fromisoformat(bloqueado_ate)
            except Exception:
                bloqueado_ate_dt = None
        else:
            bloqueado_ate_dt = bloqueado_ate
        if bloqueado_ate_dt and bloqueado_ate_dt > datetime.now(timezone.utc):
            return True, (bloqueado_ate_dt - datetime.now(timezone.utc)).total_seconds()
    return False, 0

def notificar_admins_bloqueio_sessao(minutos, tentativas):
    """
    Envia notificação por e-mail para todos admins sobre bloqueio de sessão.
    """
    config = configs_collection.find_one({'tipo': 'geral'})
    if not config:
        return
    servidor = config.get('smtp')
    porta = config.get('porta')
    senha_email = config.get('senha_email_smtp')
    email_principal = config.get('email_smtp_principal', '').split(':')[0]
    admins = list(usuarios_collection.find({"tipo": "admin"}, {"email": 1}))
    emails_admin = [adm["email"] for adm in admins if adm.get("email")]
    if not emails_admin or not email_principal or not senha_email:
        return
    origem = request.remote_addr or "desconhecido"
    usuario_tentado = session.get("usuario_tentativa_login", "desconhecido")
    assunto = f"Bloqueio de sessão por tentativas inválidas"
    corpo = f"""
    <p>Uma sessão foi bloqueada por {minutos} minutos devido a múltiplas tentativas de acesso com usuário inexistente.</p>
    <p>Usuário da tentativa: {usuario_tentado}</p>
    <p>Tentativas acumuladas nesta sessão: {tentativas}</p>
    <p>Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    """
    for email_destinatario in emails_admin:
        try:
            enviar_email(
                assunto=assunto,
                email_remetente=email_principal,
                corpo=corpo,
                copias="",
                senha_email=senha_email,
                email_destinatario=email_destinatario,
                servidor=servidor,
                porta=porta
            )
        except Exception:
            pass

def autenticar_usuario(username, senha):
    """
    Autentica um usuário pelo username e senha.
    Verifica se o usuário está ativo e se a senha está correta.
    Se errar a senha mais de 3 vezes, bloqueia o usuário automaticamente.
    Se o usuário não existir, controla tentativas por sessão e bloqueia progressivamente.
    """
    session["usuario_tentativa_login"] = username  # Salva o último username tentado na sessão
    usuario = usuarios_collection.find_one({"username": username})
    if not usuario:
        bloqueado, tempo = registrar_tentativa_sessao()
        if bloqueado:
            return {"sessao_bloqueada": True, "tempo": tempo}
        return None
    if usuario.get("status") != "ativo":
        return None
    # Verifica senha
    if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario['senha']):
        resetar_tentativas_login(username)
        # Limpa tentativas da sessão ao sucesso (zera bloqueio e tentativas)
        session.pop("tentativas_login_sessao", None)
        session.pop("bloqueado_ate_sessao", None)
        session.pop("ultimo_bloqueio_min_sessao", None)
        session.pop("usuario_tentativa_login", None)
        return usuario
    else:
        incrementar_tentativas_login(username)
        return None

def enviar_email(assunto, email_remetente, corpo, servidor, porta, copias, email_destinatario, senha_email):
    """
    Envia um e-mail de confirmação de venda.

    Args:
        email_vendedor (str): E-mail do remetente (vendedor).
        corpo (str): Conteúdo do e-mail.
        copias (str): E-mails de cópia separados por vírgula. Opcional.
        senha_email (str): Senha do e-mail do remetente.
        email_posvendas (str): E-mail do pós-vendas (destinatário principal).
    """
    # Cria mensagem de e-mail
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = email_remetente
    msg['To'] = email_destinatario

    # Adiciona destinatários em cópia, se houver
    todos_destinatarios = [email_destinatario]
    if copias:
        copias = copias.split(',')
        copias_limpa = [c.strip() for c in copias if c.strip()]
        msg['Cc'] = ', '.join(copias_limpa)
        todos_destinatarios += copias_limpa

    # Corpo alternativo em HTML
    msg.set_content("Este e-mail contém uma versão em HTML. Por favor, habilite a visualização de conteúdo.")
    msg.add_alternative(corpo, subtype='html')

    # Envia o e-mail via SMTP (usando Hostinger/simplobr)
    with smtplib.SMTP_SSL(servidor, porta) as smtp:
        smtp.login(email_remetente, senha_email)
        smtp.send_message(msg, to_addrs=todos_destinatarios)


def cadastrar_produto_service(data):
    """
    Serviço para cadastrar um novo produto na coleção de produtos do banco de dados.

    Args:
        data (dict): Dicionário contendo os dados do produto.
            Espera as chaves: 'codigo' (str), 'nome' (str), 'formas_pagamento' (list, até 13 itens).

    Returns:
        InsertOneResult: Resultado da operação de inserção do MongoDB.
    """
    codigo = data.get('codigo')
    nome = data.get('nome')
    formas_pagamento = data.get('formas_pagamento', [])
    # Filtra apenas condições com todos os campos preenchidos
    formas_pagamento_filtradas = [
        fp for fp in formas_pagamento
        if fp.get('valor_total') not in [None, '', 0, '0']
        and fp.get('parcelas') not in [None, '', 0, '0']
        and fp.get('valor_parcela') not in [None, '', 0, '0']
    ]
    return cadastrar_produto(codigo, nome, formas_pagamento_filtradas)

def dados_valores_venda():
    """
    Retorna um dicionário com os produtos cadastrados e suas condições de pagamento,
    formatado para facilitar a escolha de condições e valores na tela de cadastro de vendas.

    Returns:
        dict: Um dicionário no formato:
            {
                'Nome do Produto': [
                    {'condicao': 'TIPO | PARCELAS', 'valor': valor_total},
                    ...
                ],
                ...
            }
    """
    # Busca todos os produtos cadastrados no banco (sem o campo _id)
    produtos = list(produtos_collection.find({}, {'_id': 0}))
    
    dict_produtos = {}
    # Para cada produto, monta uma lista de condições de pagamento formatadas
    for produto in produtos:
        lista_condicoes = []
        for condicoes in produto.get('formas_pagamento', []):
            condicao_formatada = {
                'condicao': f"{condicoes['tipo']} | {condicoes['parcelas']}",
                'valor': condicoes['valor_total']
            }
            lista_condicoes.append(condicao_formatada)
        
        dict_produtos[produto['nome']] = lista_condicoes
    
    return dict_produtos

def gerar_pdf_graficos(selecao, nome_base, ano, mes):
    """
    Gera um arquivo PDF contendo os gráficos selecionados pelo usuário, para o período (ano/mes) informado.
    Salva temporariamente as imagens dos gráficos e monta o PDF com cada gráfico em uma página.

    Args:
        selecao (list): Lista de chaves de gráficos selecionados (ex: ['vendas_geral', ...]).
        nome_base (str): Nome base do arquivo PDF gerado.
        ano (int): Ano dos dados a serem exibidos.
        mes (int): Mês dos dados a serem exibidos.

    Returns:
        tuple: (buffer_pdf, nome_arquivo)
            buffer_pdf: arquivo PDF em memória (BytesIO)
            nome_arquivo: nome sugerido para download
    """
    start = time.time()
    data = session.get('data_grafico_vendas_diarias')
    print(data)

    graficos_disponiveis = {
        "vendas_geral": ("grafico_vendas_geral.png", lambda a, m: gerar_fig_vendas_geral(soma_vendas)),
        "metas_diarias_vendedor": ("grafico_metas_diarias_vendedor.png", gerar_fig_metas_diarias_vendedor),
        "metas_semanais_vendedor": ("grafico_metas_semanais_vendedor.png", gerar_fig_metas_semanais_vendedor),
        "banco_vendedores": ("grafico_banco_vendedores.png", gerar_fig_banco_vendedores),
        "vendas_vendedor": ("grafico_vendas_vendedor.png", lambda a, m: gerar_fig_vendas_vendedor(soma_vendas)),
        "vendas_diarias": ("grafico_vendas_diarias.png", lambda a, m: gerar_fig_vendas_diarias(data_escolhida=data)),
        "status_vendas_vendedor": ("grafico_status_vendas_vendedor.png", gerar_fig_status_vendas_vendedor),
        "metas_vendedor": ("grafico_metas_vendedor.png", gerar_fig_metas_vendedor),
        "verdes_vermelhos_geral": ("grafico_verdes_vermelhos_geral.png", gerar_fig_verdes_vermelhos_geral),
        "verdes_vermelhos_vendedor": ("grafico_verdes_vermelhos_vendedor.png", gerar_fig_verdes_vermelhos_vendedor),
        "tipo_vendas_geral": ("grafico_tipo_vendas_geral.png", gerar_fig_tipo_vendas_geral),
        "tipo_vendas_por_vendedor": ("grafico_tipo_vendas_por_vendedor.png", gerar_fig_tipo_vendas_por_vendedor),
        "mapa_vendas_por_estado": ("grafico_mapa_vendas_por_estado.png", gerar_fig_mapa_vendas_por_estado),
        "prazo_vendas_vendedor": ("grafico_prazo_vendas_vendedor.png", gerar_fig_prazo_vendas_vendedor),
        "produtos_mais_vendidos": ("grafico_produtos_mais_vendidos.png", gerar_fig_produtos_mais_vendidos),
        "vendas_diarias_linhas": ("grafico_vendas_diarias_linhas.png", gerar_fig_vendas_diarias_linhas),
        "quantidade_vendas_diarias": ("grafico_quantidade_vendas_diarias.png", gerar_fig_quantidade_vendas_diarias),
        "vendas_fim_de_semana": ("grafico_vendas_fim_de_semana.png", gerar_fig_vendas_fim_de_semana),
        "quantidade_vendas_fim_de_semana": ("grafico_quantidade_vendas_fim_de_semana.png", gerar_fig_quantidade_vendas_fim_de_semana)
    }

    graficos_escolhidos = [
        (nome, func(ano, mes)) for chave, (nome, func) in graficos_disponiveis.items() if chave in selecao
    ]

    if not graficos_escolhidos:
        return "Nenhum gráfico selecionado.", None

    buffer = BytesIO()

    data_geracao = datetime.now().strftime("Gerado em: %d/%m/%Y %H:%M")

    with tempfile.TemporaryDirectory() as temp_dir:
        for nome_arquivo, figura in graficos_escolhidos:
            caminho = os.path.join(temp_dir, nome_arquivo)
            pio.write_image(figura, caminho, format='png', width=1600, height=800, scale=4)

        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        largura, altura = landscape(A4)

        margem_lateral = 30
        margem_vertical = 30

        for i in range(0, len(graficos_escolhidos), 2):
            if i < len(graficos_escolhidos):
                img1_path = os.path.join(temp_dir, graficos_escolhidos[i][0])
                img1 = ImageReader(img1_path)

                if i + 1 < len(graficos_escolhidos):
                    # Dois gráficos na mesma página
                    img2_path = os.path.join(temp_dir, graficos_escolhidos[i + 1][0])
                    img2 = ImageReader(img2_path)

                    largura_img = largura - 40
                    altura_img = (altura - 60) / 2  # espaço para dois gráficos

                    c.drawImage(img1, 20, altura / 2 + 20, width=largura_img, height=altura_img, preserveAspectRatio=True)
                    c.drawImage(img2, 20, 20, width=largura_img, height=altura_img, preserveAspectRatio=True)

                else:
                    # Apenas um gráfico: ocupa quase toda a página
                    largura_img = largura - 40
                    altura_img = altura - 60
                    c.drawImage(img1, 20, 30, width=largura_img, height=altura_img, preserveAspectRatio=True)

            # Rodapé com data
            c.setFont("Helvetica", 9)
            c.drawRightString(largura - 20, 10, data_geracao)
            c.showPage()

        c.save()

    buffer.seek(0)
    nome_arquivo = f"{nome_base}_{mes}_{ano}.pdf"
    return buffer, nome_arquivo

def verificar_permissao_acesso(username):
    """
    Verifica se o usuário está com permissão de acesso ('aceito') ou bloqueado ('logo').

    Parâmetros:
        username (str, opcional): Nome de usuário.

    Retorno:
        bool: True se acesso aceito, False se bloqueado ou não encontrado.
    """
    print(f"Verificando permissão de acesso para o usuário: {username}")
    filtro = {}
    if username:
        filtro["username"] = username
    else:
        return False

    usuario = usuarios_collection.find_one(filtro, {"permissa_acesso": 1})
    if usuario and usuario.get("permissa_acesso") == "aceito":
        return True
    return False

def verifica_email(email_list: list) -> tuple:
    for i, email in enumerate(email_list):
        if '@' not in email:
            return (False, i)  # Encontrou o primeiro inválido
    return (True, None) if email_list else (True, None)  # Todos são válidos (ou lista vazia)

def verifica_fone(fones_list: list) -> tuple:
    for i, fone in enumerate(fones_list):
        if len(fone) < 17:
            return (False, i)  # Primeiro inválido
    return (True, None) if fones_list else (True, None)

def verifica_produto(produto: str) -> bool:
    todos_produtos = list(produtos_collection.find({}, {'_id': 0, 'nome': 1}))
    nomes_produtos = [p['nome'] for p in todos_produtos]

    if produto.startswith('Personalizado:'):
        # Considera "Personalizado: Produto X, Produto Y"
        produtos_personalizados = produto.replace('Personalizado:', '').strip()
        lista_personalizados = [p.strip() for p in produtos_personalizados.split(',') if p.strip()]
        # Retorna False se não houver nenhum personalizado listado!
        if not lista_personalizados:
            return False
        # Retorna True só se TODOS os personalizados estiverem no banco
        return all(p in nomes_produtos for p in lista_personalizados)

    # Produto normal
    return produto in nomes_produtos
        
def verifica_condicoes(condicoes: str) -> bool:
    todas_condicoes = list(produtos_collection.find({}, {'_id': 0, 'formas_pagamento': 1}))

    validacao = []

    for produto in todas_condicoes:
        formas_pagamento = produto.get('formas_pagamento', [])
        for forma in formas_pagamento:
            tipo = forma.get('tipo', '').strip()
            parcelas = forma.get('parcelas', '').strip()
            validacao.append(f"{tipo} | {parcelas}")
    
    return condicoes in validacao

def verifica_tipo_cliente(tipo_cliente:str) -> bool:
    possiveis_tipos_clientes = ['', 'verde', 'vermelho']
    if tipo_cliente == None:
        return True

    return tipo_cliente.strip().lower() in possiveis_tipos_clientes

def eh_numero(valor_real, valor_tabela, valor_entrada, valor_venda_avista, valor_parcelas):
    if valor_real == None or valor_tabela == None or valor_entrada == None or valor_venda_avista == None or valor_parcelas == None:
        return False
    try:
        float(valor_real)
        float(valor_tabela)
        float(valor_entrada)
        float(valor_venda_avista)
        float(valor_parcelas)
        return True
    except ValueError:
        return False

def verifica_status_vendas(status_venda:str) -> bool:
    possiveis_tipos_status = ['', 'aguardando', 'aprovada', 'faturado', 'cancelada', 'refazer']
    if status_venda == None:
        return True

    return status_venda.strip().lower() in possiveis_tipos_status

def normalizar_valor(valor, padrao="0"):
    """
    Converte valores para string com separador decimal ".", removendo ","
    Se estiver vazio ou None, retorna o valor padrão.
    """
    if not valor:
        return padrao
    try:
        # Substitui vírgula por ponto e remove espaços
        valor_str = str(valor).replace(",", ".").strip()
        float(valor_str)  # valida se é um número
        return valor_str
    except ValueError:
        return padrao

from datetime import datetime, time as dt_time

def desligar_permissao_acesso_usuarios():
    agora = datetime.now()
    hora_atual = dt_time(agora.hour, agora.minute, agora.second)  # pega só hora e minuto

    lista_horarios = [
        dt_time(19, 30, 5),
        dt_time(20, 30, 5),
        dt_time(21, 30, 5),
        dt_time(23, 30, 5),
        dt_time(0, 30, 5),
        dt_time(1, 30, 5),
        dt_time(2, 30, 5),
        dt_time(3, 30, 5),
        dt_time(4, 30, 5),
        dt_time(5, 30, 5),
    ]

    if hora_atual in lista_horarios:
        usuarios_collection.update_many(
            {"permissa_acesso": {"$ne": "desligado"}},
            {"$set": {"permissa_acesso": "desligado"}}
        )
        print("Todos deslogados")
        return True
    return False

def registrar_notificacao(tipo, mensagem, venda=None, envolvidos=None):
    """
    Registra uma nova notificação no banco de dados, associada a vendas, edições ou outros eventos.

    Parâmetros:
        tipo (str): Tipo da notificação, ex: 'venda', 'edicao', etc.
        mensagem (str): Texto a ser exibido na notificação.
        venda (dict, opcional): Dicionário com os dados da venda associada (pode ser None).
        envolvidos (list, opcional): Lista de usernames dos envolvidos que devem receber a notificação.

    O campo 'lida_por' inicia vazio e será preenchido conforme usuários visualizarem a notificação.
    O campo 'venda_numero' registra o número da venda se informado.
    """
    notificacao = {
        "tipo": tipo,                                # Tipo do evento (ex: venda, edição)
        "mensagem": mensagem,                        # Texto da notificação
        "data_hora": datetime.now(),                 # Data e hora de registro
        "lida_por": [],                              # Usuários que já visualizaram (inicia vazio)
        "envolvidos": envolvidos or [],              # Usernames que devem receber o aviso
        "venda_numero": venda.get("numero_da_venda") if venda else None  # Número da venda, se aplicável
    }
    notificacoes_collection.insert_one(notificacao)   # Salva a notificação na collection