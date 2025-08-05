import pytest
import mongomock
from datetime import datetime

# Importe a função correta (ajuste o import conforme sua estrutura)
from app.models import nova_venda

@pytest.fixture
def fake_vendas_collection(monkeypatch):
    # Cria uma coleção de vendas fake (em memória)
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.vendas_collection", mock_db.vendas)
    return mock_db.vendas

def test_nova_venda_insercao(fake_vendas_collection):
    dados_venda = {
        "usuario_id": "123",
        "numero_da_venda": "001",
        "nome": "Cliente Teste",
        "nome_do_contato": "Contato Teste",
        "endereco": {"rua": "Rua A", "num": "10"},
        "cep": "12345678",
        "cnpj_cpf": "123.456.789-00",
        "razao_social": "Empresa Teste Ltda",
        "inscricao_estadual_identidade": "ISENTO",
        "produto": "Produto Teste",
        "valor_tabela": 1500.0,
        "condicoes": "à vista",
        "valor_parcelas": "0",
        "data_prestacao_inicial": "2025-07-07",
        "tipo_envio_boleto": "email",
        "tipo_remessa": "normal",
        "email": "cliente@teste.com",
        "fones": ["11999990000"],
        "fone_vendedor": "11988887777",
        "email_vendedor": "vendedor@teste.com",
        "vendedor": "Vendedor Teste",
        "obs": "Observação qualquer",
        "status": "Aprovado",
        "posvendas": "Joana",
        "data_criacao": datetime.now(),
        "data_real": datetime.now(),
        "valor_real": 1500.0,
        "tipo_cliente": "Verde",
        "logs": [{"evento": "criação", "data": "2025-07-07"}],
        "desconto_autorizado": True,
        "caminho_arquivos": "/caminho/arquivo.pdf",
        "obs_vendas": "Obs interna",
        "valor_entrada": 100.0,
        "valor_venda_avista": 1400.0,
        "condicoes_venda": "Boleto",
        "desconto_live": False,
        "percentual_desconto_live": 0.0
    }

    # Chama a função, passando os argumentos na ordem correta
    resultado = nova_venda(
        dados_venda["usuario_id"],
        dados_venda["numero_da_venda"],
        dados_venda["nome"],
        dados_venda["nome_do_contato"],
        dados_venda["endereco"],
        dados_venda["cep"],
        dados_venda["cnpj_cpf"],
        dados_venda["razao_social"],
        dados_venda["inscricao_estadual_identidade"],
        dados_venda["produto"],
        dados_venda["valor_tabela"],
        dados_venda["condicoes"],
        dados_venda["valor_parcelas"],
        dados_venda["data_prestacao_inicial"],
        dados_venda["tipo_envio_boleto"],
        dados_venda["tipo_remessa"],
        dados_venda["email"],
        dados_venda["fones"],
        dados_venda["fone_vendedor"],
        dados_venda["email_vendedor"],
        dados_venda["vendedor"],
        dados_venda["obs"],
        dados_venda["status"],
        dados_venda["posvendas"],
        dados_venda["data_criacao"],
        dados_venda["data_real"],
        dados_venda["valor_real"],
        dados_venda["tipo_cliente"],
        dados_venda["logs"],
        dados_venda["desconto_autorizado"],
        dados_venda["caminho_arquivos"],
        dados_venda["obs_vendas"],
        dados_venda["valor_entrada"],
        dados_venda["valor_venda_avista"],
        dados_venda["condicoes_venda"],
        dados_venda["desconto_live"],
        dados_venda["percentual_desconto_live"],
    )

    # Verifica se o retorno tem um inserted_id
    assert resultado.inserted_id is not None

    # Busca a venda criada no banco fake
    venda_db = fake_vendas_collection.find_one({"numero_da_venda": "001"})
    assert venda_db is not None
    assert venda_db["nome"] == "Cliente Teste"
    assert venda_db["produto"] == "Produto Teste"
    assert venda_db["valor_tabela"] == 1500.0
    assert venda_db["logs"] == [{"evento": "criação", "data": "2025-07-07"}]
    assert venda_db["valor_entrada"] == 100.0
    assert venda_db["desconto_live"] == False
    assert venda_db["percentual_desconto_live"] == 0.0
    assert venda_db["condicoes_venda"] == "Boleto"
    assert venda_db["caminho_arquivos"] == "/caminho/arquivo.pdf"

def test_nova_venda_logs_opcional(fake_vendas_collection):
    # Testa logs=None, deve virar lista vazia
    resultado = nova_venda(
        "1", "1002", "Nome", "Contato", {}, "00000-000", "000", "RS", "IE", "P",
        200.0, "a prazo", "50", "2025-07-07", "email", "normal", "cli@ex.com", ["11000"], "119", "vend@ex.com", "Vend",
        "Obs", "Novo", "Maria", datetime.now(), datetime.now(), 199.0,
        tipo_cliente=None, logs=None, desconto_autorizado=None, caminho_arquivos="",
        obs_vendas="", valor_entrada=None, valor_venda_avista=None, condicoes_venda=None, desconto_live=None, percentual_desconto_live=None
    )
    venda_db = fake_vendas_collection.find_one({"numero_da_venda": "1002"})
    assert venda_db is not None
    assert venda_db["logs"] == []

