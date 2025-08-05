import pytest
import mongomock
import bcrypt

# Aqui você importa a função que você quer testar
from app.models import criar_usuario

@pytest.fixture
def fake_usuarios_collection(monkeypatch):
    # Cria um banco em memória fake
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.models.usuarios_collection", mock_db.usuarios)
    return mock_db.usuarios

def test_criar_usuario_insercao(fake_usuarios_collection):
    # Dados de entrada simulados
    usuario = {
        "nome_completo": "João Silva",
        "username": "joaosilva",
        "email": "joao@email.com",
        "senha": "senha123",
        "fone": "11988887777",
        "tipo": "admin",
        "status": "ativo",
        "foto": None,
        "pos_vendas": None,
        "meta_mes": 10000.0,
        "permissa_acesso": "aceito"
    }

    # Chama a função
    resultado = criar_usuario(
        usuario["nome_completo"],
        usuario["username"],
        usuario["email"],
        usuario["senha"],
        usuario["fone"],
        usuario["tipo"],
        usuario["status"],
        usuario["foto"],
        usuario["pos_vendas"],
        usuario["meta_mes"],
        usuario["permissa_acesso"]
    )
    
    # Verifica se retornou um id (Mongo retorna um InsertOneResult com inserted_id)
    assert resultado.inserted_id is not None

    # Busca o usuário criado no banco fake
    usuario_db = fake_usuarios_collection.find_one({"username": "joaosilva"})
    assert usuario_db is not None
    assert usuario_db["nome_completo"] == "João Silva"
    assert usuario_db["email"] == "joao@email.com"
    assert usuario_db["status"] == "ativo"
    assert usuario_db["meta_mes"] == 10000.0
    assert usuario_db["tentativas_login"] == 0

    # Senha deve ser hash, não igual à original
    assert usuario_db["senha"] != "senha123"
    # Verifica se o hash confere com a senha informada
    assert bcrypt.checkpw("senha123".encode('utf-8'), usuario_db["senha"])

    # Checa se os campos opcionais estão corretos
    assert usuario_db["foto"] is None
    assert usuario_db["pos_vendas"] is None

