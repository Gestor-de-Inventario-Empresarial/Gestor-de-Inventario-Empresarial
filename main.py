import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.handlers import registrar_manejadores
from app.core.loader import cargar_routers
from app.core.responses import respuesta

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "Gestor de Inventario Empresarial"))

registrar_manejadores(app)
cargar_routers(app)


@app.get("/")
def raiz():
    return respuesta(True, None, "Servicio en línea")