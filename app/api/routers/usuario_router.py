from fastapi import APIRouter

from app.core.responses import respuesta
from app.domain.entities.usuario import LoginRequest
from app.repositories.usuario_repository import usuario_repository
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

service = UsuarioService(repo=usuario_repository)


@router.post(
    "/login",
    summary="Iniciar sesión",
    description="Autentica las credenciales del usuario comparando la contraseña cifrada, verifica que cuenta, sucursal y empresa estén activas y entrega el token de acceso.",
)
def login(datos: LoginRequest):
    resultado = service.iniciar_sesion(datos)
    return respuesta(True, resultado, "Inicio de sesión exitoso")