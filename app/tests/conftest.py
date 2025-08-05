import pytest
from app import create_app  # Ou o nome da função que cria seu app Flask

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app
