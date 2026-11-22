from fastapi import APIRouter, Depends, Header, status

from app.core.responses import respuesta
from app.domain.entities.usuario import LoginRequest, UsuarioCreate
from app.repositories.usuario_repository import usuario_repository
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/v1", tags=["Usuarios"])

service = UsuarioService(repo=usuario_repository)


def obtener_sesion_administrador(
    x_empresa_id: int = Header(
        default=1,
        alias="X-Empresa-Id",
        description="ID de la empresa del Administrador en sesión",
    ),
    x_rol: str = Header(
        default="Administrador",
        alias="X-Rol",
        description="Rol del usuario autenticado ('Administrador' o 'Usuario')",
    ),
) -> tuple[int, str]:
    return x_empresa_id, x_rol


@router.post(
    "/auth/login",
    summary="Iniciar sesión",
    description="Autentica las credenciales del usuario comparando la contraseña cifrada, verifica que cuenta, sucursal y empresa estén activas y entrega el token de acceso.",
)
def login(datos: LoginRequest):
    resultado = service.iniciar_sesion(datos)
    return respuesta(True, resultado, "Inicio de sesión exitoso")


@router.post(
    "/usuarios",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario en una sucursal",
    description="Crea una cuenta de usuario asociada a una sucursal activa de la empresa del Administrador, cifrando la contraseña antes de guardarla.",
)
def crear_usuario(
    datos: UsuarioCreate,
    sesion: tuple[int, str] = Depends(obtener_sesion_administrador),
):
    id_empresa_sesion, rol_sesion = sesion
    usuario = service.crear_usuario(
        id_empresa_sesion=id_empresa_sesion,
        rol_sesion=rol_sesion,
        datos=datos,
    )
    return respuesta(True, usuario, "Usuario creado exitosamente")