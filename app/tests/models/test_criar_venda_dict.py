from datetime import datetime

from app.models import criar_venda_dict

def test_criar_venda_dict_campos_obrigatorios():
    agora = datetime(2025, 7, 7, 15, 0, 0)
    venda = criar_venda_dict(
        usuario_id="u1",
        numero_da_venda="123",
        nome="Cliente A",
        nome_do_contato="Contato A",
        endereco={"rua": "Rua 1"},
        cep="00000-000",
        cnpj_cpf="000.000.000-00",
        razao_social="Empresa X",
        inscricao_estadual_identidade="ISENTO",
        produto="Produto X",
        valor_tabela=100.0,
        condicoes="à vista",
        valor_parcelas="100",
        data_prestacao_inicial="2025-07-10",
        tipo_envio_boleto="email",
        tipo_remessa="normal",
        email="cliente@x.com",
        fones=["11999999999"],
        fone_vendedor="11988888888",
        email_vendedor="vendedor@x.com",
        vendedor="Vendedor Y",
        obs="Observação",
        status="Novo",
        posvendas="Ana",
        data_criacao=agora,
        valor_real=90.0
    )
    # Checa campos obrigatórios
    assert venda["usuario_id"] == "u1"
    assert venda["numero_da_venda"] == "123"
    assert venda["nome"] == "Cliente A"
    assert venda["valor_tabela"] == 100.0
    assert venda["status"] == "Novo"
    assert venda["data_criacao"] == agora
    assert venda["valor_real"] == 90.0
    assert venda["logs"] == []  # logs default vira lista vazia
    assert isinstance(venda["data_real"], datetime)
    assert venda["data_real"] != agora  # Provavelmente, pois será datetime.now()

def test_criar_venda_dict_campos_opcionais():
    agora = datetime(2025, 7, 7, 15, 0, 0)
    venda = criar_venda_dict(
        usuario_id="u1",
        numero_da_venda="123",
        nome="Cliente A",
        nome_do_contato="Contato A",
        endereco={"rua": "Rua 1"},
        cep="00000-000",
        cnpj_cpf="000.000.000-00",
        razao_social="Empresa X",
        inscricao_estadual_identidade="ISENTO",
        produto="Produto X",
        valor_tabela=100.0,
        condicoes="à vista",
        valor_parcelas="100",
        data_prestacao_inicial="2025-07-10",
        tipo_envio_boleto="email",
        tipo_remessa="normal",
        email="cliente@x.com",
        fones=["11999999999"],
        fone_vendedor="11988888888",
        email_vendedor="vendedor@x.com",
        vendedor="Vendedor Y",
        obs="Observação",
        status="Novo",
        posvendas="Ana",
        data_criacao=agora,
        valor_real=90.0,
        tipo_cliente="VIP",
        logs=[{"evento": "criada"}],
        desconto_autorizado=True,
        caminho_arquivos="/tmp/file.pdf",
        obs_vendas="Só interna",
        valor_entrada=50.0,
        valor_venda_avista=80.0,
        condicoes_venda="Boleto",
        desconto_live=False,
        percentual_desconto_live=5.0
    )
    assert venda["tipo_cliente"] == "VIP"
    assert venda["logs"] == [{"evento": "criada"}]
    assert venda["desconto_autorizado"] is True
    assert venda["caminho_arquivos"] == "/tmp/file.pdf"
    assert venda["obs_vendas"] == "Só interna"
    assert venda["valor_entrada"] == 50.0
    assert venda["valor_venda_avista"] == 80.0
    assert venda["condicoes_venda"] == "Boleto"
    assert venda["desconto_live"] is False
    assert venda["percentual_desconto_live"] == 5.0

def test_criar_venda_dict_logs_padrao_lista_vazia():
    agora = datetime(2025, 7, 7, 15, 0, 0)
    venda = criar_venda_dict(
        usuario_id="u1",
        numero_da_venda="123",
        nome="Cliente A",
        nome_do_contato="Contato A",
        endereco={"rua": "Rua 1"},
        cep="00000-000",
        cnpj_cpf="000.000.000-00",
        razao_social="Empresa X",
        inscricao_estadual_identidade="ISENTO",
        produto="Produto X",
        valor_tabela=100.0,
        condicoes="à vista",
        valor_parcelas="100",
        data_prestacao_inicial="2025-07-10",
        tipo_envio_boleto="email",
        tipo_remessa="normal",
        email="cliente@x.com",
        fones=["11999999999"],
        fone_vendedor="11988888888",
        email_vendedor="vendedor@x.com",
        vendedor="Vendedor Y",
        obs="Observação",
        status="Novo",
        posvendas="Ana",
        data_criacao=agora,
        valor_real=90.0
    )
    assert venda["logs"] == []
