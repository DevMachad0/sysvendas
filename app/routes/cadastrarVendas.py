from flask import Blueprint, jsonify, request, session, redirect, render_template
from app.models import usuarios_collection, configs_collection
from app.services import verificar_permissao_acesso, dados_valores_venda, verifica_email, verifica_fone, gerar_numero_venda, verifica_condicoes, verifica_produto, verifica_status_vendas, verifica_tipo_cliente, eh_numero, normalizar_valor, registrar_notificacao, cadastrar_venda
from bson import ObjectId
from datetime import datetime, timedelta

cadastra_vendas_bp = Blueprint('cadastra_vendas', __name__)

@cadastra_vendas_bp.route('/cadastrar_vendas', methods=['GET', 'POST'])
def cadastrar_vendas():
    """
    Rota para cadastro de novas vendas no sistema.

    GET:
        - Renderiza o formulário de cadastro de vendas com as informações necessárias.

    POST:
        - Recebe dados do formulário ou JSON.
        - Gera número único para a venda.
        - Processa campos de usuário, vendedor, telefones e endereço.
        - Gera campo de logs de criação.
        - Trata produto personalizado.
        - Monta dict de dados da venda.
        - Busca e configura os dados do vendedor e pós-vendas para notificações.
        - Salva a venda no banco.
        - Dispara notificação para envolvidos (vendedor, pós-vendas, admin).
        - Retorna JSON de sucesso ou erro.

    Returns:
        - GET: HTML do formulário
        - POST: JSON {"success": True/False, ...}
    """
    user = session.get('user')
    if not user or not verificar_permissao_acesso(username=user.get('username')):
        return redirect('/index.html')
    if user['tipo'].strip().lower() == 'faturamento':
        return redirect('vendas')
    
    info_vendas = dados_valores_venda()

    if request.method == 'POST':
        data = request.json or request.form        

        # --- Validação obrigatória dos campos de e-mail e telefone ---
        emails = data.get("emails", "")
        fones = data.get("fones", "")
        # Aceita tanto string quanto lista (JS pode enviar dos dois jeitos)
        if isinstance(emails, str):
            emails_list = [x.strip() for x in emails.split(",") if x.strip()]
        else:
            emails_list = [x.strip() for x in emails if x and x.strip()]
        
        if not emails_list:
            return jsonify({"success": False, "erro": "É obrigatório informar pelo menos um e-mail."}), 400
        
        verificando_emails, indice_email = verifica_email(emails_list)
        if not verificando_emails:
            return jsonify({"success": False, "erro": f"O email {emails_list[indice_email]} não é válido."}), 400

        
        if isinstance(fones, str):
            fones_list = [x.strip() for x in fones.split(",") if x.strip()]
        else:
            fones_list = [x.strip() for x in fones if x and x.strip()]
        
        if not fones_list:
            return jsonify({"success": False, "erro": "É obrigatório informar pelo menos um telefone."}), 400

        verificando_numeros, indice_fone = verifica_fone(fones_list)
        if not verificando_numeros:
            return jsonify({"success": False, "erro": f"O número {fones_list[indice_fone]} não é válido."}), 400

        # ------------------------------------------------------------

        # Gera número da venda
        numero_da_venda = gerar_numero_venda()

        usuario_id = data.get('usuario_id')
        if usuario_id:
            usuario_id = ObjectId(usuario_id)

        # Descobre quem está logado
        quem_log = data.get('user_username') or data.get('quem') or ""
        if not quem_log:
            user = session.get('user', {})
            quem_log = user.get('username') or user.get('nome_vendedor') or ""

        vendedor_nome = data.get('nome_vendedor') or ""
        email_vendedor = data.get('email_vendedor')
        fone_vendedor = data.get('fone_vendedor')

        # Processa os telefones e os emails
        if isinstance(fones, list):
            fones_str = ", ".join(fones)
        else:
            fones_str = ", ".join([tel.strip() for tel in fones.split(",") if tel.strip()])
        
        if isinstance(emails, list):
            email_str = ", ".join(emails)
        else:
            email_str = ", ".join([email.strip() for email in emails.split(",") if email.strip()])

        endereco = {
            "rua": data.get("rua"),
            "bairro": data.get("bairro"),
            "numero": data.get("numero"),
            "cidade": data.get("cidade"),
            "estado": data.get("estado", "") if data.get("estado", "") else "FO"
        }

        tipo_cliente = data.get("tipo_cliente")
        verificando_tipo_cliente = verifica_tipo_cliente(tipo_cliente)
        if not verificando_tipo_cliente:
            return jsonify({"success": False, "erro": f"O tipo de cliente {tipo_cliente} não existe."}), 400

        # Monta log de criação
        logs = [{
            "data_hora": datetime.now().strftime('%d/%m/%Y %H:%M'),
            "quem": quem_log,
            "modificacao": "Criação da venda"
        }]

        # Campo de desconto autorizado (bool)
        desconto_autorizado = data.get("desconto_autorizado")
        if isinstance(desconto_autorizado, str):
            desconto_autorizado = desconto_autorizado.lower() in ("true", "on", "1")

        # Produto personalizado
        produto = data.get("produto")
        produtos_personalizados = data.get("produtos_personalizados", "")
        if produto == "" and produtos_personalizados:
            produtos_lista = [p.strip() for p in produtos_personalizados.split(",") if p.strip()]
            produto_final = "Personalizado: " + ", ".join(produtos_lista)
        else:
            produto_final = produto

        verificando_produto = verifica_produto(produto_final)
        if not verificando_produto:
            return jsonify({"success": False, "erro": f"O produto {produto_final} não está cadastrado."}), 400

        # NOVOS CAMPOS
        caminho_arquivos = data.get("caminho_arquivos", "")
        obs_vendas = data.get("obs_vendas", "")

        valor_entrada = data.get("valor_entrada", "") if data.get("valor_entrada", "") else "0"
        valor_venda_avista = data.get("valor_venda_avista", "") if data.get("valor_venda_avista", "") else "0"
        condicoes_venda = data.get("condicoes_venda", "") if data.get("condicoes_venda", "") else "Nenhuma escolhida"

        verificando_valores = eh_numero(
                                data.get('valor_real'),
                                data.get("valor_tabela"),
                                valor_entrada,
                                valor_venda_avista,
                                data.get("valor_parcelas")
                             )
        if not verificando_valores:
            return jsonify({"success": False, "erro": f"Algum valor não é um número. Verifique os valores da venda."}), 400 

        # ---------------- VENDAS DEPOIS DO FIM DO EXPEDIENTE -------------------
        # Consulta ao MongoDB
        config = configs_collection.find_one(
            {'tipo': 'fim_expediente'},
            {'_id': 0, 'data': 1, 'hora': 1, 'trabalha_sabado': 1}
        )

        try:
            agora = datetime.now()
            data_str = agora.strftime('%d/%m/%Y')
            hora_padrao = '18:15:00'

            data_real = agora

            # Converte os horários de string para objetos datetime.time
            hora_atual = agora.time()
            hora_config_time = datetime.strptime(config['hora'], "%H:%M:%S").time()
            hora_padrao_time = datetime.strptime(hora_padrao, "%H:%M:%S").time()

            dia_semana = agora.weekday()  # segunda=0, ..., sábado=5, domingo=6
            trabalha_sabado = config.get('trabalha_sabado', False)  # padrão: False

            match dia_semana:
                case 5:  # sábado
                    if trabalha_sabado:
                        data_criacao = agora
                    else:
                        data_criacao = (agora + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)

                case 6:  # domingo
                    data_criacao = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

                case 4:  # sexta-feira
                    if config.get('data') and data_str == config['data']:
                        if hora_atual > hora_config_time or hora_atual > hora_padrao_time:
                            if trabalha_sabado:
                                # registra para sábado
                                data_criacao = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                            else:
                                # registra para segunda
                                data_criacao = (agora + timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
                        else:
                            data_criacao = agora
                    elif hora_atual > hora_padrao_time:
                        if trabalha_sabado:
                            # registra para sábado
                            data_criacao = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                        else:
                            # registra para segunda
                            data_criacao = (agora + timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        data_criacao = agora

                case _:  # segunda a quinta
                    if config.get('data') and data_str == config['data']:
                        if hora_atual < hora_config_time and hora_atual < hora_padrao_time:
                            data_criacao = agora
                        else:
                            data_criacao = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        if hora_atual < hora_padrao_time:
                            data_criacao = agora
                        else:
                            data_criacao = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        except  Exception as e:
            print("ERRO AO CALCULAR FIM DE EXPEDIENTE:", e)
            data_criacao = datetime.now()
        # --------------- FIM DA VERIFICAÇÃO FIM DO EXPEDIENTE ------------------

        condicoes = data.get("condicoes", "") or "1"
        verificando_condicoes = verifica_condicoes(condicoes)
        if not verificando_condicoes:
            return jsonify({"success": False, "erro": f"A condição {condicoes} não está cadastrada."}), 400
        
        status_venda = data.get("status", "")
        verificando_status_venda = verifica_status_vendas(status_venda)
        if not verificando_status_venda:
            return jsonify({"success": False, "erro": f"O Status da Venda {status_venda} não existe."}), 400
        
        quantidade_acessos = data.get("quantidade_acessos", 2)  # NOVO: quantidade de acessos padrão é 2
        try:
            quantidade_acessos = int(quantidade_acessos)
            if quantidade_acessos < 1:
                return jsonify({"success": False, "erro": "A quantidade de acessos não pode ser menor que um."}), 400
        except:
                return jsonify({"success": False, "erro": "A quantidade de acessos deve ser um número inteiro."}), 400

        venda_data = {
            "numero_da_venda": numero_da_venda,
            "nome": data.get("nome", ""),
            "nome_do_contato": data.get("nome_do_contato", ""),
            "endereco": endereco,
            "cep": data.get("cep", ""),
            "cnpj_cpf": data.get("cnpj_cpf", ""),
            "razao_social": data.get("razao_social", ""),
            "inscricao_estadual_identidade": data.get("inscricao_estadual_identidade", ""),
            "produto": produto_final if produto_final else "",
            "valor_tabela": normalizar_valor(data.get("valor_tabela", "") if data.get("valor_tabela", "") else "0"),
            "condicoes": data.get("condicoes", "") if data.get("condicoes", "") else "1",
            "valor_parcelas": normalizar_valor(data.get("valor_parcelas", "") if data.get("valor_parcelas", "") else "0"),
            "data_prestacao_inicial": data.get("data_prestacao_inicial", "") or datetime.now().strftime("%Y-%m-%d"),
            "tipo_envio_boleto": 'EMAIL',
            "tipo_remessa": data.get("tipo_remessa", ""),
            "email": data.get("email", ""),
            "fones": fones_str if fones_str else "",
            "fone_vendedor": fone_vendedor if fone_vendedor else "",
            "email_vendedor": email_vendedor if email_vendedor else "",
            "vendedor": vendedor_nome if vendedor_nome else "",
            "obs": data.get("obs", ""),
            "status": "Aguardando",
            "posvendas": data.get("posvendas", ""),
            "data_criacao": data_criacao,
            "data_real": data_real,
            "valor_real": (normalizar_valor(data.get("valor_real", "")) if data.get("valor_real", "") else "0"),
            "tipo_cliente": tipo_cliente,
            "logs": logs,
            "desconto_autorizado": desconto_autorizado,
            "caminho_arquivos": caminho_arquivos,
            "obs_vendas": obs_vendas,
            "valor_entrada": (normalizar_valor(valor_entrada) if valor_entrada else "0"),
            "valor_venda_avista": (normalizar_valor(valor_venda_avista) if valor_venda_avista else "0"),
            "condicoes_venda": condicoes_venda,
            "quantidade_acessos": quantidade_acessos,
            }

        # Busca dados do vendedor (username, pos_vendas, etc) para notificação
        vendedor = list(usuarios_collection.find({'nome_completo': vendedor_nome}, {'_id': 0, 'username': 1, 'pos_vendas': 1, 'senha_email': 1}))
        try:
            if vendedor:
                vendedor_username = vendedor[0].get('username', '')
                pv_vendedor = vendedor[0].get('pos_vendas', '')
            else:
                vendedor_username = ""
                pv_vendedor = ""

            cadastrar_venda(usuario_id=usuario_id, venda_data=venda_data)
            # Monta lista de envolvidos para notificação
            envolvidos = []
            if vendedor_username:
                envolvidos.append(vendedor_username)
            if pv_vendedor:
                envolvidos.append(pv_vendedor)
            envolvidos.append("admin")
            registrar_notificacao(
                tipo="venda",
                mensagem=f"Venda {numero_da_venda} cadastrada/atualizada.",
                venda=venda_data,
                envolvidos=envolvidos
            )
            return jsonify({"success": True, "numero_da_venda": numero_da_venda})
        except Exception as e:
            import traceback
            print("ERRO AO CADASTRAR VENDA:", e)
            traceback.print_exc()
            return jsonify({"success": False, "erro": str(e), "numero_da_venda": numero_da_venda})

    return render_template('cadastrar_vendas.html', info_vendas=info_vendas)
