"""Tests para CELEBRO."""
import os
import pytest
import tempfile
import shutil
from celebro import Celebro


@pytest.fixture
def celebro_tmp():
    """Crea un Celebro con datos temporales."""
    tmpdir = tempfile.mkdtemp()
    cb = Celebro(db_path=tmpdir)
    yield cb
    shutil.rmtree(tmpdir)


class TestGuardar:
    def test_guardar_retorna_uuid(self, celebro_tmp):
        mid = celebro_tmp.guardar("Test de memoria", "test")
        assert len(mid) == 36  # formato UUID
        assert "-" in mid

    def test_guardar_incrementa_contador(self, celebro_tmp):
        assert celebro_tmp.contar() == 0
        celebro_tmp.guardar("Primera")
        assert celebro_tmp.contar() == 1
        celebro_tmp.guardar("Segunda")
        assert celebro_tmp.contar() == 2


class TestBuscar:
    def test_buscar_encontrar_similar(self, celebro_tmp):
        celebro_tmp.guardar("El servidor web está en 192.168.1.10", "infra")
        celebro_tmp.guardar("La base de datos corre en PostgreSQL", "infra")
        
        results = celebro_tmp.buscar("¿dónde está el servidor?", top_k=2)
        assert len(results) > 0
        assert "servidor" in results[0]["texto"].lower()
        assert results[0]["score"] > 0.5

    def test_buscar_no_encontrar(self, celebro_tmp):
        celebro_tmp.guardar("Solo sé que nada sé")
        results = celebro_tmp.buscar("cosmología cuántica", top_k=1)
        # Puede devolver algo con score bajo, pero no debe fallar
        assert isinstance(results, list)


class TestListar:
    def test_listar_todas(self, celebro_tmp):
        celebro_tmp.guardar("A", "cat1")
        celebro_tmp.guardar("B", "cat2")
        todos = celebro_tmp.listar()
        assert len(todos) == 2

    def test_listar_por_categoria(self, celebro_tmp):
        celebro_tmp.guardar("Web server", "infra")
        celebro_tmp.guardar("App code", "dev")
        infra = celebro_tmp.listar(categoria="infra")
        assert len(infra) == 1
        assert infra[0]["categoria"] == "infra"


class TestBorrar:
    def test_borrar_existente(self, celebro_tmp):
        mid = celebro_tmp.guardar("Temporal")
        assert celebro_tmp.contar() == 1
        celebro_tmp.borrar(mid)
        assert celebro_tmp.contar() == 0
