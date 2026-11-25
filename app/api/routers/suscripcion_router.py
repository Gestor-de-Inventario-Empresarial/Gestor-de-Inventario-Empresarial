from typing import Optional

from fastapi import APIRouter, Depends, Header

from app.core.responses import respuesta
from app.repositories.suscripcion_repository import suscripcion_repository
from app.services.suscripcion_service import SuscripcionService

router = APIRouter(prefix="/api/v1/suscripciones", tags=["Suscripciones"])

service = SuscripcionService(repo=suscripcion_repository)


def obtener_sesion_suscripcion(
    authorization: Optional[str] = Header(
        default=None,
        alias="Authorization",
        description="Token de sesión del usuario autenticado",
    ),
    x_empresa_id: int = Header(
        default=1,
        alias="X-Empresa-Id",
        description="ID de la empresa en sesión",
    ),
) -> tuple[int, Optional[str]]:
    return x_empresa_id, authorization


# Dependencia reutilizable para bloquear Inventario y Traslados si la suscripción venció
def verificar_suscripcion_activa(
    x_sucursal_id: int = Header(default=1, alias="X-Sucursal-Id"),
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
):
    service.verificar_acceso_modulo(
        id_sucursal=x_sucursal_id,
        id_empresa=x_empresa_id,
    )


@router.get(
    "/estado",
    summary="Consultar estado de suscripción",
    description="Calcula la vigencia mensual (30 días desde el último pago exitoso) e informa los días restantes o vencidos de la empresa.",
)
def consultar_estado_suscripcion(
    sesion: tuple[int, Optional[str]] = Depends(obtener_sesion_suscripcion),
):
    id_empresa, token = sesion
    datos, mensaje = service.consultar_estado(id_empresa=id_empresa, token=token)
    return respuesta(True, datos, mensaje)