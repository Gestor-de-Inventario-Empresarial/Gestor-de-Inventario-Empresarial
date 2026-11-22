from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status

from app.core.responses import respuesta
from app.domain.entities.usuario import (
    LoginRequest,
    UsuarioCreate,
    UsuarioEstadoUpdate,
    UsuarioUpdate,
)
from app.repositories.usuario_repository import usuario_repository
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/v1", tags=["Usuarios"])

service = UsuarioService(repo=usuario_repository)


def obtener_sesion_administrador(
    x_empresa_id: int = Header(
        default=1,
        alias="X-Empresa-Id",
        description="ID de la empresa del usuario en sesión",
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


@router.get(
    "/usuarios",
    summary="Consultar usuarios de la empresa",
    description="Lista los usuarios activos e inactivos de la empresa en sesión, con filtros opcionales por sucursal y estado.",
)
def consultar_usuarios(
    id_sucursal: Optional[int] = Query(
        default=None,
        description="Filtrar usuarios por ID de sucursal",
    ),
    estado: Optional[str] = Query(
        default=None,
        description="Filtrar usuarios por estado ('activo' o 'inactivo')",
    ),
    sesion: tuple[int, str] = Depends(obtener_sesion_administrador),
):
    id_empresa_sesion, rol_sesion = sesion
    usuarios = service.listar_usuarios(
        id_empresa_sesion=id_empresa_sesion,
        rol_sesion=rol_sesion,
        id_sucursal=id_sucursal,
        estado=estado,
    )
    return respuesta(True, usuarios, "Consulta de usuarios exitosa")


@router.put(
    "/usuarios/{id_usuario}",
    summary="Actualizar rol o sucursal de un usuario",
    description="Permite al Administrador modificar el rol y/o la sucursal asignada de un usuario evitando quitar el rol al único Administrador activo.",
)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioUpdate,
    sesion: tuple[int, str] = Depends(obtener_sesion_administrador),
):
    id_empresa_sesion, rol_sesion = sesion
    actualizado = service.actualizar_rol_o_sucursal(
        id_usuario=id_usuario,
        id_empresa_sesion=id_empresa_sesion,
        rol_sesion=rol_sesion,
        datos=datos,
    )
    return respuesta(True, actualizado, "Usuario actualizado exitosamente")


@router.patch(
    "/usuarios/{id_usuario}/estado",
    summary="Activar o desactivar un usuario",
    description="Cambia el estado de un usuario entre 'activo' e 'inactivo', bloqueando la desactivación del único Administrador activo de la empresa.",
)
def cambiar_estado_usuario(
    id_usuario: int,
    datos: UsuarioEstadoUpdate,
    sesion: tuple[int, str] = Depends(obtener_sesion_administrador),
):
    id_empresa_sesion, rol_sesion = sesion
    actualizado = service.cambiar_estado(
        id_usuario=id_usuario,
        id_empresa_sesion=id_empresa_sesion,
        rol_sesion=rol_sesion,
        datos=datos,
    )
    return respuesta(True, actualizado, "Estado del usuario actualizado exitosamente")