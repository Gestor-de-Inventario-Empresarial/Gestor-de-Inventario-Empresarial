from datetime import date, timedelta
import importlib
import pytest
from fastapi.testclient import TestClient

from main import app


def _reiniciar_objeto_repo(repo):
    for attr in dir(repo):
        if attr.startswith("__"):
            continue
        valor = getattr(repo, attr)
        if attr == "_ultimos_pagos" and isinstance(valor, dict):
            valor.clear()
            valor[1] = date.today() - timedelta(days=15)
        elif attr == "_siguiente_id" and isinstance(valor, int):
            setattr(repo, attr, 1)
        elif attr in ("_planes", "_roles_validos"):
            continue
        elif isinstance(valor, list):
            valor.clear()
        elif isinstance(valor, dict):
            valor.clear()


@pytest.fixture(autouse=True)
def limpiar_estado_repositorios():
    modulos_repo = [
        ("app.repositories.empresa_repository", "empresa_repository"),
        ("app.repositories.sucursal_repository", "sucursal_repository"),
        ("app.repositories.producto_repository", "producto_repository"),
        ("app.repositories.traslado_repository", "traslado_repository"),
        ("app.repositories.usuario_repository", "usuario_repository"),
        ("app.repositories.suscripcion_repository", "suscripcion_repository"),
        ("app.repositories.pago_repository", "pago_repository"),
    ]
    for ruta_modulo, nombre_instancia in modulos_repo:
        try:
            modulo = importlib.import_module(ruta_modulo)
            instancia = getattr(modulo, nombre_instancia, None)
            if instancia is not None:
                _reiniciar_objeto_repo(instancia)
        except ImportError:
            continue
    yield


@pytest.fixture
def client():
    return TestClient(app)