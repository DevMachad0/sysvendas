from flask import Blueprint, jsonify, request, session
from app.services import verifica_condicoes, verifica_tipo_cliente, verifica_status_vendas, verifica_produto, normalizar_valor, eh_numero, reenviar_venda, registrar_notificacao
from app.models import vendas_collection, usuarios_collection
from bson import ObjectId
from datetime import datetime

salvar_edicao_venda_bp = Blueprint('salvar_edicao_venda', __name__)

@salvar_edicao_venda_bp.route('/salvar_edicao_venda', methods=['POST'])
def salvar_edicao_venda():
    """
    Endpoint para salvar a edição de uma venda.

    - Recebe os dados da venda editada via POST.
    - Atualiza apenas os campos editáveis definidos em 'campos_editaveis'.
    - Atualiza campos do endereço separadamente.
    - Faz tratamento especial para produtos personalizados.
    - Atualiza (ou adiciona) o campo 'desconto_autorizado'.
    - Atualiza o log de alterações da venda.
    - Atualiza a venda no banco e atualiza o objeto na sessão.
    - Dispara notificação para todos os envolvidos na venda (vendedor, pós-vendas, admin, faturamento).
    - Notificação detalhada pelo status atual da venda.
    """
    data = request.json or request.form
    numero_da_venda = data.get('numero_da_venda')
    venda = vendas_collection.find_one({"numero_da_venda": numero_da_venda})
    if not venda:
        return jsonify({"success": False, "erro": "Venda não encontrada"}), 404

    # --- CORREÇÃO: Recupera o tipo de usuário da sessão para uso nas permissões ---
    user = session.get('user')
    user.get('tipo') if user else None

    if data.get('status') in ['refazer', 'Refazer', 'aguardando', 'Aguardando', 'cancelada', 'Cancelada'] and user['tipo'].strip().lower() == 'faturamento':
        return jsonify({"success": False, "erro": "Sem permissão"}), 403
    
    if data.get('status') in ['aprovada', 'Aprovada', 'faturado', 'Faturado', 'cancelada', 'Cancelada'] and user['tipo'].strip().lower() == 'vendedor':
        return jsonify({"success": False, "erro": "Sem permissão"}), 403

    if data.get('status') in ['cancelada', 'Cancelada'] and data.get('obs_vendas') == '':
        return jsonify({"success": False, "erro": "Adicione o motivo do cancelamento."}), 403
    
    verificando_condicoes = verifica_condicoes(data.get('condicoes'))
    if not verificando_condicoes:
        return jsonify({"success": False, "erro": f"A condição {data.get('condicoes')} não está cadastrada."}), 400
    
    verificando_tipo_clientes = verifica_tipo_cliente(data.get('tipo_cliente'))
    if not verificando_tipo_clientes:
        return jsonify({"success": False, "erro": f"O tipo de cliente {data.get('tipo_cliente')} não existe."}), 400
    
    status_venda = data.get("status", "")
    verificando_status_venda = verifica_status_vendas(status_venda)
    if not verificando_status_venda:
        return jsonify({"success": False, "erro": f"O Status da Venda {status_venda} não existe."}), 400

    campos_editaveis = [
        "nome", "nome_do_contato", "cep", "email", "fones", "cnpj_cpf", "razao_social", "inscricao_estadual_identidade",
        "produto", "valor_parcelas", "condicoes", "data_prestacao_inicial", "tipo_remessa", "tipo_cliente", "obs", "status",
        "caminho_arquivos", "obs_vendas", "quantidade_acessos"  # <-- adicionado aqui
    ]
    # Atualiza campos do endereço
    endereco = venda.get('endereco', {})
    for campo in ["rua", "bairro", "numero", "cidade", "estado"]:
        endereco[campo] = data.get(f"endereco_{campo}", endereco.get(campo, ''))
    update = {"endereco": endereco}

    # Lógica para produto personalizado na edição
    produto = data.get("produto", "")
    produtos_personalizados = data.get("produtos_personalizados", "")
    if (produto == "" or (produto and produto.startswith("Personalizado"))) and produtos_personalizados:
        produtos_lista = [p.strip() for p in produtos_personalizados.split(",") if p.strip()]
        produto_final = "Personalizado: " + ", ".join(produtos_lista)
        update["produto"] = produto_final
    else:
        update["produto"] = produto
    
    verificando_produto = verifica_produto(update["produto"])
    if not verificando_produto:
        return jsonify({"success": False, "erro": f"O produto {update["produto"]} não está cadastrado."}), 400

    # Atualiza os demais campos editáveis
    for campo in campos_editaveis:
        if campo != "produto":  # já tratado acima
            update[campo] = data.get(campo, venda.get(campo, ''))

    # Tenta extrair quantidade de acessos como int
    raw_qtd_acessos = data.get("quantidade_acessos", venda.get("quantidade_acessos", 2))

    try:
        qtd = int(raw_qtd_acessos)
        if qtd < 1:
            return jsonify({"success": False, "erro": "A quantidade de acessos não pode ser menor que 1."}), 400
    except Exception:
        return jsonify({"success": False, "erro": "A quantidade de acessos deve ser um inteiro válido."}), 400

    
    update["quantidade_acessos"] = qtd

    # --- GARANTE atualização dos campos financeiros ---
    if "valor_real" in data:
        update["valor_real"] = normalizar_valor(data.get("valor_real", "0") if data.get("valor_real", "0") else "0")
    # Validação para impedir valor_real igual a 0 ou vazio
    if not update.get("valor_real") or str(update.get("valor_real")).replace(",", ".") in ["0", "0.0", "0,0"]:
        return jsonify({"success": False, "erro": "O Valor Real da Venda não pode ser zero ou vazio."}), 400

    if "condicoes_venda" in data:
        update["condicoes_venda"] = data.get("condicoes_venda", "")
    if "valor_entrada" in data:
        update["valor_entrada"] = normalizar_valor(data.get("valor_entrada", "0") if data.get("valor_entrada", "0") else "0")
    if "valor_venda_avista" in data:
        update["valor_venda_avista"] = normalizar_valor(data.get("valor_venda_avista", "0") if data.get("valor_venda_avista", "0") else "0")

    # --- NOVO: Sempre salva valor_tabela do formulário ---
    update["valor_tabela"] = normalizar_valor(data.get("valor_tabela", "0") if data.get("valor_tabela", "0") else "0")

    # --- NOVO: Lógica para limpar/preencher campos conforme condição ---
    condicao = update.get("condicoes") or data.get("condicoes") or venda.get("condicoes", "")
    condicoes_venda = update.get("condicoes_venda") or data.get("condicoes_venda") or venda.get("condicoes_venda", "")
    if condicao == "A/C | 1+1" and condicoes_venda == "avista":
        # Preenche valor_venda_avista e força valor_parcelas = "0" (string), limpa valor_entrada
        valor_venda_avista = normalizar_valor(data.get("valor_venda_avista", "0") if data.get("valor_venda_avista", "0") else "0")
        update["valor_venda_avista"] = valor_venda_avista
        update["valor_parcelas"] = "0"
        update["valor_entrada"] = "0"
    elif condicao == "A/C | 1+1" and condicoes_venda == "entrada_parcela":
        update["valor_venda_avista"] = "0"
        # valor_entrada e valor_parcelas já vêm do data normalmente
    else:
        update["valor_venda_avista"] = "0"
    
    verificando_valores = eh_numero(
                                update["valor_real"],
                                update["valor_tabela"],
                                update["valor_entrada"],
                                update["valor_venda_avista"],
                                update["valor_parcelas"]
                             )
    if not verificando_valores:
        return jsonify({"success": False, "erro": f"Algum valor não é um número. Verifique os valores da venda."}), 400 

    # --- ATUALIZA O LOG DA VENDA ---
    logs = venda.get("logs", [])
    logs.append({
        "data_hora": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "quem": user.get("username") or user.get("nome_vendedor") or "",
        "modificacao": "Edição da venda"
    })
    update["logs"] = logs

    # --- TRATAMENTO CORRETO DO DESCONTO AUTORIZADO ---
    desconto_autorizado = data.get("desconto_autorizado", "")
    if isinstance(desconto_autorizado, str):
        desconto_autorizado = desconto_autorizado.lower() in ("true", "on", "1")
    elif isinstance(desconto_autorizado, bool):
        pass  # já está booleano
    else:
        desconto_autorizado = False
    update["desconto_autorizado"] = desconto_autorizado

    # --- NOVO: TRATAMENTO DO DESCONTO DA LIVE ---
    desconto_live = data.get("desconto_live", "")
    if isinstance(desconto_live, str):
        desconto_live = desconto_live.lower() in ("true", "on", "1")
    elif isinstance(desconto_live, bool):
        pass
    else:
        desconto_live = False
    update["desconto_live"] = desconto_live

    # Salva o motivo do desconto (campo texto)
    motivo_desconto_live = data.get("motivo_desconto_live", "")
    update["motivo_desconto_live"] = motivo_desconto_live

    # Remove campo antigo de percentual_desconto_live se existir
    update.pop("percentual_desconto_live", None)

    # Atualiza no banco de dados
    vendas_collection.update_one({"numero_da_venda": numero_da_venda}, {"$set": update})

    # Serializa venda para sessão (converte ObjectId e outros tipos não serializáveis)
    venda.update(update)
    venda_serializada = {}
    for k, v in venda.items():
        if isinstance(v, ObjectId):
            venda_serializada[k] = str(v)
        elif isinstance(v, dict):
            venda_serializada[k] = {ik: (str(iv) if isinstance(iv, ObjectId) else iv) for ik, iv in v.items()}
        else:
            venda_serializada[k] = v
    if 'logs' in venda_serializada and isinstance(venda_serializada['logs'], list):
        for log in venda_serializada['logs']:
            for lk, lv in log.items():
                if isinstance(lv, ObjectId):
                    log[lk] = str(lv)

    session['venda_edicao'] = venda_serializada

    # ----------- NOTIFICAÇÃO -----------
    envolvidos = []
    # Adiciona o vendedor responsável pela venda
    vendedor_nome = venda.get('vendedor', '')
    vendedor = usuarios_collection.find_one({'nome_completo': vendedor_nome}, {'username': 1})
    if vendedor and vendedor.get('username'):
        envolvidos.append(vendedor['username'])
    # Pós-vendas (um ou mais usernames)
    posvendas_raw = venda.get('posvendas', '') or data.get('posvendas', '')
    posvendas_usernames = [pv.strip() for pv in posvendas_raw.split(",") if pv.strip()]
    envolvidos.extend(posvendas_usernames)
    # Admin
    envolvidos.append("admin")
    # --- NOVO: Se status == "Faturado", notifica todos admins, todos faturamento, todos pos_vendas, e só o vendedor responsável ---
    status_final = (update.get("status") or venda.get("status", "") or "").strip()
    if status_final.lower() == "faturado":
        # Adiciona todos faturamento
        faturamentos = usuarios_collection.find({"tipo": "faturamento"}, {"username": 1})
        envolvidos.extend([f["username"] for f in faturamentos if f.get("username")])
        # Adiciona todos pos_vendas
        pos_vendas_users = usuarios_collection.find({"tipo": "pos_vendas"}, {"username": 1})
        envolvidos.extend([pv["username"] for pv in pos_vendas_users if pv.get("username")])
        # Adiciona todos admins
        admins = usuarios_collection.find({"tipo": "admin"}, {"username": 1})
        envolvidos.extend([adm["username"] for adm in admins if adm.get("username")])
        # Remove duplicados mantendo ordem
        envolvidos = list(dict.fromkeys(envolvidos))
    elif status_final.lower() == "aprovada":
        # Notifica todos faturamento
        faturamentos = usuarios_collection.find({"tipo": "faturamento"}, {"username": 1})
        envolvidos.extend([f["username"] for f in faturamentos if f.get("username")])
        # Remove duplicados mantendo ordem
        envolvidos = list(dict.fromkeys(envolvidos))
    else:
        # Remove duplicados mantendo ordem
        envolvidos = list(dict.fromkeys(envolvidos))

    # Mensagem detalhada conforme status
    status_msg = {
        "aguardando": "em preparação",
        "aprovada": "aprovada",
        "refazer": "marcada para refazer",
        "cancelada": "cancelada",
        "faturada": "faturada",
        "faturado": "faturado"
    }
    status_key = status_final.lower()
    status_legivel = status_msg.get(status_key, status_final)
    registrar_notificacao(
        tipo="venda",
        mensagem=f"Venda {numero_da_venda} editada. Status: {status_legivel.capitalize()}",
        venda=venda,
        envolvidos=envolvidos
    )
    # ----------- FIM NOTIFICAÇÃO -----------

    # ----------------- ENVIO DE EMAIL ------------------
    if data.get('status') in ['aguardando', 'Aguardando'] and user['tipo'].strip().lower() == 'vendedor':
        reenviar_venda(data=data)
        return jsonify({"success": "Email de pedido de venda reenviado."}), 200
    # ------------ FIM DE ENVIO DE EMAIL ---------------


    return jsonify({"success": True})
