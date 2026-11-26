from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.domain.entities.pago import PagoCreate
from app.repositories.pago_repository import pago_repository
from app.services.pago_service import PagoService

# No usa verificar_suscripcion_activa: debe seguir disponible con suscripción vencida
router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos y Suscripciones"])

service = PagoService(repo=pago_repository)


def obtener_sesion_pago(
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
    "",
    summary="Pagar suscripción con Wompi",
    description="Procesa el cobro de un plan mensual mediante el token de pago de Wompi sin recibir ni almacenar datos de tarjeta, renovando la vigencia de la empresa por 30 días.",
)
def pagar_suscripcion(
    datos: PagoCreate,
    sesion: tuple[int, str] = Depends(obtener_sesion_pago),
):
    id_empresa_sesion, rol_sesion = sesion
    codigo_http, exito, data, mensaje = service.procesar_pago(
        id_empresa_sesion=id_empresa_sesion,
        rol_sesion=rol_sesion,
        datos=datos,
    )
    return JSONResponse(
        status_code=codigo_http,
        content={
            "message": mensaje,
            "data": data,
            "success": exito,
        },
    )