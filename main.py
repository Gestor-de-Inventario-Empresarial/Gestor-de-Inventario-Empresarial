import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "Gestor de Inventario Empresarial"))


@app.get("/")
def raiz():
    return {"success": True, "data": None, "message": "Servicio en línea"}