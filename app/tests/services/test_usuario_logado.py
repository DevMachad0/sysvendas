import pytest
from app.services import usuario_logado

def test_usuario_logado(monkeypatch):
  
  monkeypatch.setattr('app.services.usuario_logado', lambda: False)

  retorno = usuario_logado()

  assert retorno == False