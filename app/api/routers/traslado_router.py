from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta
from app.domain.entities.traslado import TrasladoCreate
from app.repositories.traslado_repository import traslado_repository
from app.services.traslado_service import TrasladoService

router = APIRouter(prefix="/api/v1/traslados", tags=["Traslados"])

service = TrasladoService(repo=traslado_repository)


def obtener_sesion_consulta(
    authorization: Optional[str] = Header(
        default=None,
        alias="Authorization",
        description="Token de sesión del usuario autenticado",
    ),
    x_sucursal_id: int = Header(
        default=1,
        alias="X-Sucursal-Id",
        description="ID de la sucursal solicitante en sesión",
    ),
) -> tuple[int, Optional[str]]:
    return x_sucursal_id, authorization


def obtener_sesion_radicacion(
    x_sucursal_id: int = Header(
        default=1,
        alias="X-Sucursal-Id",
        description="ID de la sucursal solicitante en sesión",
    ),
    x_rol: str = Header(
        default="Usuario",
        alias="X-Rol",
        description="Rol del usuario en sesión ('Administrador' o 'Usuario')",
    ),
) -> tuple[int, str]:
    return x_sucursal_id, x_rol


def _manejar_error_traslado(error: ErrorNegocio):
    if getattr(error, "data", None) is not None:
        return JSONResponse(
            status_code=error.codigo_http,
            content={
                "message": str(error),
                "data": error.data,
                "success": False,
            },
        )
    raise error


@router.get(
    "/disponibilidad",
    summary="Buscar stock en otras sucursales",
    description="Consulta otras sucursales activas de la empresa con existencias disponibles del producto, ordenadas de mayor a menor.",
)
def buscar_disponibilidad(
    producto: Optional[str] = Query(
        default=None,
        description="Nombre o código del producto a buscar",
    ),
    sesion: tuple[int, Optional[str]] = Depends(obtener_sesion_consulta),
):
    id_sucursal_solicitante, token = sesion
    try:
        datos = service.buscar_disponibilidad(
            id_sucursal_solicitante=id_sucursal_solicitante,
            token=token,
            producto=producto,
        )
    except ErrorNegocio as e:
        return _manejar_error_traslado(e)

    return respuesta(True, datos, "Consulta de disponibilidad exitosa")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Radicar solicitud de traslado",
    description="Radica una solicitud de traslado en estado pendiente validando sucursales activas y stock disponible en origen sin alterar inventarios.",
)
def radicar_traslado(
    datos: TrasladoCreate,
    sesion: tuple[int, str] = Depends(obtener_sesion_radicacion),
):
    id_sucursal_solicitante, rol_usuario = sesion
    try:
        traslado = service.radicar(
            id_sucursal_solicitante=id_sucursal_solicitante,
            rol_usuario=rol_usuario,
            datos=datos,
        )
    except ErrorNegocio as e:
        return _manejar_error_traslado(e)

    return respuesta(True, traslado, "Solicitud de traslado radicada exitosamente")