import importlib
import pkgutil

from app.api import routers


def cargar_routers(app):
    """Registra solo todos los archivos de app/api/routers que tengan una variable 'router'."""
    for modulo in pkgutil.iter_modules(routers.__path__):
        archivo = importlib.import_module(f"app.api.routers.{modulo.name}")
        if hasattr(archivo, "router"):
            app.include_router(archivo.router)