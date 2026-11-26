from datetime import date
from typing import Callable, Optional

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions import ErrorNegocio
from app.domain.entities.suscripcion import Suscripcion

MENSAJE_CAMPOS_OBLIGATORIOS = "El plan y el token de pago son obligatorios"
MENSAJE_SIN_PERMISO_PAGAR = "No tiene permisos para realizar pagos"
MENSAJE_PLAN_NO_ENCONTRADO = "Plan de suscripción no encontrado"
MENSAJE_PAGO_APROBADO = "Pago aprobado y suscripción renovada exitosamente"
MENSAJE_PAGO_RECHAZADO = "El pago fue rechazado por la pasarela"
MENSAJE_PAGO_PENDIENTE = "El pago está pendiente de confirmación por la pasarela"
MENSAJE_PAGO_REVISION = (
    "El pago fue recibido y está en revisión; se activará el servicio una vez verificado"
)

MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA = "El evento no tiene la estructura esperada"
MENSAJE_EVENTO_PROCESADO = "Evento de pago procesado exitosamente"
MENSAJE_EVENTO_REPETIDO = "El evento ya fue procesado anteriormente"

MAX_REINTENTOS_REGISTRO = 3
ESTADOS_FINALES_TRANSACCION = ("aprobada", "rechazada", "anulada")
MAPEO_ESTADOS_WOMPI = {
    "APPROVED": "aprobada",
    "APROBADO": "aprobada",
    "DECLINED": "rechazada",
    "RECHAZADO": "rechazada",
    "VOIDED": "anulada",
    "ANULADO": "anulada",
}


class PagoCreate(BaseModel):
    id_plan: Optional[int] = Field(default=None)
    token_pago: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def validar_campos_pago(cls, valores):
        if not isinstance(valores, dict):
            raise ValueError(MENSAJE_CAMPOS_OBLIGATORIOS)

        id_plan = valores.get("id_plan")
        token_pago = valores.get("token_pago")

        if (
            id_plan is None
            or isinstance(id_plan, bool)
            or not isinstance(id_plan, int)
            or token_pago is None
            or not isinstance(token_pago, str)
            or not token_pago.strip()
        ):
            raise ValueError(MENSAJE_CAMPOS_OBLIGATORIOS)

        valores["token_pago"] = token_pago.strip()
        return valores


class WebhookWompiRequest(BaseModel):
    event: str
    referencia: str
    estado_evento: str
    estado_crudo: str

    @model_validator(mode="before")
    @classmethod
    def validar_estructura_evento(cls, valores):
        if not isinstance(valores, dict):
            raise ValueError(MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA)

        evento = valores.get("event")
        data = valores.get("data")
        if (
            not isinstance(evento, str)
            or not evento.strip()
            or not isinstance(data, dict)
        ):
            raise ValueError(MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA)

        transaccion = data.get("transaction")
        if not isinstance(transaccion, dict):
            raise ValueError(MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA)

        referencia = transaccion.get("reference")
        status = transaccion.get("status")
        if (
            not isinstance(referencia, str)
            or not referencia.strip()
            or not isinstance(status, str)
            or not status.strip()
        ):
            raise ValueError(MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA)

        status_upper = status.strip().upper()
        if status_upper not in MAPEO_ESTADOS_WOMPI:
            raise ValueError(MENSAJE_ESTRUCTURA_WEBHOOK_INVALIDA)

        return {
            "event": evento.strip(),
            "referencia": referencia.strip(),
            "estado_evento": MAPEO_ESTADOS_WOMPI[status_upper],
            "estado_crudo": status.strip(),
        }


class TransaccionPago:
    def __init__(
        self,
        id: Optional[int],
        id_empresa: int,
        id_plan: int,
        referencia: str,
        monto: int,
        estado: str = "pendiente",
        fecha_creacion: Optional[date] = None,
        fecha_vencimiento: Optional[str] = None,
        motivo_rechazo: Optional[str] = None,
    ):
        self.id = id
        self.id_empresa = id_empresa
        self.id_plan = id_plan
        self.referencia = referencia
        self.monto = monto
        self.estado = estado
        self.fecha_creacion = fecha_creacion or date.today()
        self.fecha_vencimiento = fecha_vencimiento
        self.motivo_rechazo = motivo_rechazo

    @staticmethod
    def validar_permiso_administrador(rol_sesion: str):
        if not isinstance(rol_sesion, str) or rol_sesion.strip().lower() != "administrador":
            raise ErrorNegocio(MENSAJE_SIN_PERMISO_PAGAR, 403)

    @staticmethod
    def generar_referencia(
        id_empresa: int, secuencial: int, fecha: Optional[date] = None
    ) -> str:
        fecha_ref = (fecha or date.today()).strftime("%Y%m%d")
        return f"SUB-{id_empresa}-{fecha_ref}-{secuencial:04d}"

    def es_estado_final(self) -> bool:
        return self.estado.strip().lower() in ESTADOS_FINALES_TRANSACCION

    def marcar_rechazada(self, motivo: str = "Transacción declinada por la pasarela"):
        self.estado = "rechazada"
        self.motivo_rechazo = motivo

    def marcar_anulada(self, motivo: str = "Transacción anulada por la pasarela"):
        self.estado = "anulada"
        self.motivo_rechazo = motivo

    def marcar_pendiente(self):
        self.estado = "pendiente"

    # RN-11: reintento de registro interno tras cobro aprobado y constancia para revisión manual
    def manejar_inconsistencia(
        self,
        persistir_aprobacion: Callable[[], str],
        max_reintentos: int = MAX_REINTENTOS_REGISTRO,
    ) -> bool:
        for _ in range(max_reintentos):
            try:
                fecha_vencimiento = persistir_aprobacion()
                self.estado = "aprobada"
                self.fecha_vencimiento = fecha_vencimiento
                return True
            except Exception:
                continue

        self.estado = "pendiente_revision"
        return False

    @staticmethod
    def calcular_nueva_vigencia(fecha_pago: Optional[date] = None) -> dict:
        return Suscripcion.calcular_vigencia(fecha_pago or date.today())

    def to_aprobada_response(self) -> dict:
        return {
            "id_transaccion": self.id,
            "referencia": self.referencia,
            "id_plan": self.id_plan,
            "monto": self.monto,
            "estado": self.estado,
            "fecha_vencimiento": self.fecha_vencimiento,
        }

    def to_estado_response(self) -> dict:
        return {
            "id_transaccion": self.id,
            "referencia": self.referencia,
            "estado": self.estado,
        }

    def to_webhook_response(self) -> dict:
        return {
            "referencia": self.referencia,
            "estado": self.estado,
        }