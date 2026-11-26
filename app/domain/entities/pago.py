import re
from datetime import date
from typing import Callable, Optional

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions import ErrorNegocio
from app.domain.entities.suscripcion import Suscripcion

MENSAJE_CAMPOS_OBLIGATORIOS = "El plan y el token de pago son obligatorios"
MENSAJE_SIN_PERMISO_PAGAR = "No tiene permisos para realizar pagos"
MENSAJE_SIN_PERMISO_HISTORIAL = "No tiene permisos para consultar el historial de pagos"
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

MENSAJE_ESTADO_HISTORIAL_INVALIDO = "El estado indicado no es válido"
MENSAJE_FORMATO_FECHA_INVALIDO = "Las fechas deben tener formato YYYY-MM-DD"
MENSAJE_RANGO_FECHAS_INVALIDO = (
    "La fecha de inicio no puede ser posterior a la fecha de fin"
)
MENSAJE_PAGINACION_INVALIDA = "Los parámetros de paginación deben ser enteros positivos"
MENSAJE_HISTORIAL_EXITOSO = "Consulta de historial de pagos exitosa"
MENSAJE_HISTORIAL_VACIO = "No existen transacciones para los filtros indicados"

MAX_REINTENTOS_REGISTRO = 3
MAX_TAMANO_PAGINA = 100
PATRON_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ESTADOS_HISTORIAL_VALIDOS = (
    "pendiente",
    "aprobada",
    "rechazada",
    "pendiente_revision",
)
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
    def validar_permiso_administrador(
        rol_sesion: str, mensaje: str = MENSAJE_SIN_PERMISO_PAGAR
    ):
        if not isinstance(rol_sesion, str) or rol_sesion.strip().lower() != "administrador":
            raise ErrorNegocio(mensaje, 403)

    @staticmethod
    def validar_filtros_historial(
        estado: Optional[str],
        fecha_inicio: Optional[str],
        fecha_fin: Optional[str],
        pagina: int,
        tamano: int,
    ) -> tuple[Optional[str], Optional[date], Optional[date]]:
        if pagina < 1 or tamano < 1 or tamano > MAX_TAMANO_PAGINA:
            raise ErrorNegocio(MENSAJE_PAGINACION_INVALIDA, 400)

        estado_normalizado: Optional[str] = None
        if estado is not None:
            estado_limpio = estado.strip().lower()
            if estado_limpio not in ESTADOS_HISTORIAL_VALIDOS:
                raise ErrorNegocio(MENSAJE_ESTADO_HISTORIAL_INVALIDO, 400)
            estado_normalizado = estado_limpio

        inicio_dt: Optional[date] = None
        if fecha_inicio is not None:
            fecha_ini_str = fecha_inicio.strip()
            if not PATRON_FECHA_ISO.match(fecha_ini_str):
                raise ErrorNegocio(MENSAJE_FORMATO_FECHA_INVALIDO, 400)
            try:
                inicio_dt = date.fromisoformat(fecha_ini_str)
            except ValueError as e:
                raise ErrorNegocio(MENSAJE_FORMATO_FECHA_INVALIDO, 400) from e

        fin_dt: Optional[date] = None
        if fecha_fin is not None:
            fecha_fin_str = fecha_fin.strip()
            if not PATRON_FECHA_ISO.match(fecha_fin_str):
                raise ErrorNegocio(MENSAJE_FORMATO_FECHA_INVALIDO, 400)
            try:
                fin_dt = date.fromisoformat(fecha_fin_str)
            except ValueError as e:
                raise ErrorNegocio(MENSAJE_FORMATO_FECHA_INVALIDO, 400) from e

        if inicio_dt is not None and fin_dt is not None and inicio_dt > fin_dt:
            raise ErrorNegocio(MENSAJE_RANGO_FECHAS_INVALIDO, 400)

        return estado_normalizado, inicio_dt, fin_dt

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

    def to_historial_response(self) -> dict:
        return {
            "id_transaccion": self.id,
            "referencia": self.referencia,
            "id_plan": self.id_plan,
            "monto": self.monto,
            "estado": self.estado,
            "fecha": self.fecha_creacion.isoformat(),
        }