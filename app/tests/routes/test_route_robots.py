import os
import tempfile
import shutil
import pytest
import time

@pytest.fixture
def url_robots():
    return '/robots.txt'


def test_robots_txt_ok(monkeypatch, client, url_robots):
    fake_dir = tempfile.mkdtemp()
    robots_path = os.path.join(fake_dir, 'robots.txt')
    with open(robots_path, 'w', encoding='utf-8') as f:
        f.write("User-agent: *\nDisallow: /admin/\n")
    monkeypatch.setattr('app.routes.robots.__file__', os.path.join(fake_dir, "fake_module.py"))
    resp = client.get(url_robots)
    assert resp.status_code == 200
    assert b"User-agent:" in resp.data
    assert b"Disallow: /admin/" in resp.data
    # Garante que o arquivo foi liberado antes de remover
    for _ in range(5):
        try:
            shutil.rmtree(fake_dir)
        except PermissionError:
            time.sleep(0.2)


def test_robots_txt_not_found(monkeypatch, client, url_robots):
    # Cria um diretório sem robots.txt
    fake_dir = tempfile.mkdtemp()
    monkeypatch.setattr('app.routes.robots.__file__', os.path.join(fake_dir, "fake_module.py"))
    resp = client.get(url_robots)
    # Flask retorna 404 se arquivo não existe
    assert resp.status_code == 404
    shutil.rmtree(fake_dir)

def test_robots_txt_metodo_nao_permitido(client, url_robots):
    resp = client.post(url_robots)
    assert resp.status_code == 405  # Method Not Allowed
