import hashlib
import hmac
from typing import Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta
from app.domain.entities.pago import PagoCreate, WebhookWompiRequest
from app.repositories.pago_repository import pago_repository
from app.services.pago_service import PagoService

CLAVE_SECRETA_WEBHOOK_WOMPI = "wompi-events-secret"
MENSAJE_FIRMA_INVALIDA = "Firma del evento no válida"

router = APIRouter(prefix="/api/v1", tags=["Pagos y Suscripciones"])

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


# Seguridad en capa API: verificación criptográfica HMAC-SHA256 de la firma del evento
def verificar_firma_wompi(
    datos: WebhookWompiRequest,
    x_wompi_signature: Optional[str] = Header(
        default=None,
        alias="X-Wompi-Signature",
        description="Firma HMAC-SHA256 generada por Wompi sobre 'referencia:status'",
    ),
) -> WebhookWompiRequest:
    if not x_wompi_signature or not x_wompi_signature.strip():
        raise ErrorNegocio(MENSAJE_FIRMA_INVALIDA, 401)

    mensaje = f"{datos.referencia}:{datos.estado_crudo}".encode("utf-8")
    firma_esperada = hmac.new(
        CLAVE_SECRETA_WEBHOOK_WOMPI.encode("utf-8"),
        mensaje,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(x_wompi_signature.strip().lower(), firma_esperada):
        raise ErrorNegocio(MENSAJE_FIRMA_INVALIDA, 401)

    return datos


@router.post(
    "/pagos",
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


@router.post(
    "/webhooks/wompi",
    summary="Recibir confirmación del webhook de Wompi",
    description="Endpoint asíncrono consumido por Wompi. Verifica la firma HMAC-SHA256 del evento, garantiza idempotencia y actualiza la transacción y la suscripción.",
)
def recibir_webhook_wompi(
    datos: WebhookWompiRequest = Depends(verificar_firma_wompi),
):
    resultado, mensaje = service.procesar_webhook_wompi(datos)
    return respuesta(True, resultado, mensaje)