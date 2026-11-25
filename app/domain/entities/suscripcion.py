from datetime import date, timedelta
from typing import Optional

from app.core.exceptions import ErrorNegocio

MENSAJE_NO_AUTENTICADO = "Debe iniciar sesión para consultar la suscripción"
MENSAJE_SUSCRIPCION_VENCIDA_BLOQUEO = (
    "Suscripción vencida: regularice su pago para acceder a este módulo"
)

DIAS_VIGENCIA_MENSUAL = 30


class Suscripcion:
    def __init__(
        self,
        id_empresa: int,
        fecha_ultimo_pago: Optional[date] = None,
    ):
        self.id_empresa = id_empresa
        self.fecha_ultimo_pago = fecha_ultimo_pago

    @staticmethod
    def validar_sesion_autenticada(token: Optional[str]):
        if token is None or not token.strip():
            raise ErrorNegocio(MENSAJE_NO_AUTENTICADO, 401)

    # RN-10: vigencia de 30 días desde el último pago exitoso (sin periodo de gracia)
    @staticmethod
    def calcular_vigencia(
        fecha_ultimo_pago: Optional[date],
        fecha_referencia: Optional[date] = None,
    ) -> dict:
        if fecha_ultimo_pago is None:
            return {
                "estado": "sin_pago",
                "fecha_ultimo_pago": None,
                "fecha_vencimiento": None,
                "dias_vencida": 0,
            }

        hoy = fecha_referencia or date.today()
        dias_transcurridos = (hoy - fecha_ultimo_pago).days
        fecha_vencimiento = fecha_ultimo_pago + timedelta(days=DIAS_VIGENCIA_MENSUAL)

        if dias_transcurridos <= DIAS_VIGENCIA_MENSUAL:
            dias_restantes = max(0, DIAS_VIGENCIA_MENSUAL - dias_transcurridos)
            return {
                "estado": "activa",
                "fecha_ultimo_pago": fecha_ultimo_pago.isoformat(),
                "fecha_vencimiento": fecha_vencimiento.isoformat(),
                "dias_restantes": dias_restantes,
            }

        dias_vencida = dias_transcurridos - DIAS_VIGENCIA_MENSUAL
        return {
            "estado": "vencida",
            "fecha_ultimo_pago": fecha_ultimo_pago.isoformat(),
            "fecha_vencimiento": fecha_vencimiento.isoformat(),
            "dias_vencida": dias_vencida,
        }

    @staticmethod
    def validar_acceso_activo(vigencia: dict):
        if vigencia.get("estado") != "activa":
            error = ErrorNegocio(MENSAJE_SUSCRIPCION_VENCIDA_BLOQUEO, 403)
            error.data = {
                "estado": "vencida",
                "dias_vencida": vigencia.get("dias_vencida", 0),
            }
            raise error