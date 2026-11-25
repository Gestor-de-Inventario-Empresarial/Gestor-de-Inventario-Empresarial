from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.suscripcion import Suscripcion
from app.repositories.suscripcion_repository import SuscripcionRepository

MENSAJE_FALLA_SUSCRIPCION = "No fue posible consultar el estado de la suscripción"
MENSAJE_EMPRESA_NO_ENCONTRADA = "Empresa no encontrada"


class SuscripcionService:
    def __init__(self, repo: SuscripcionRepository):
        self.repo = repo

    def consultar_estado(self, id_empresa: int, token: Optional[str]) -> tuple[dict, str]:
        Suscripcion.validar_sesion_autenticada(token)

        try:
            empresa = self.repo.consultar_empresa(id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_SUSCRIPCION, 503) from e

        if empresa is None:
            raise ErrorNegocio(MENSAJE_EMPRESA_NO_ENCONTRADA, 404)

        try:
            fecha_ultimo_pago = self.repo.obtener_fecha_ultimo_pago(id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_SUSCRIPCION, 503) from e

        vigencia = Suscripcion.calcular_vigencia(fecha_ultimo_pago)
        mensaje = (
            "Consulta de suscripción exitosa"
            if vigencia["estado"] == "activa"
            else "La suscripción se encuentra vencida"
        )
        return vigencia, mensaje

    # Interfaz interna Suscripciones.consultarEstado para Inventario, Traslados y Usuarios
    def obtener_estado_simple(self, id_empresa: int) -> str:
        fecha_ultimo_pago = self.repo.obtener_fecha_ultimo_pago(id_empresa)
        vigencia = Suscripcion.calcular_vigencia(fecha_ultimo_pago)
        return "activa" if vigencia["estado"] == "activa" else "vencida"

    def verificar_acceso_modulo(
        self,
        id_sucursal: Optional[int] = None,
        id_empresa: Optional[int] = None,
    ):
        try:
            empresa_objetivo = id_empresa
            if empresa_objetivo is None and id_sucursal is not None:
                empresa_objetivo = self.repo.obtener_empresa_por_sucursal(id_sucursal)
            if empresa_objetivo is None:
                empresa_objetivo = 1

            fecha_ultimo_pago = self.repo.obtener_fecha_ultimo_pago(empresa_objetivo)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_SUSCRIPCION, 503) from e

        vigencia = Suscripcion.calcular_vigencia(fecha_ultimo_pago)
        Suscripcion.validar_acceso_activo(vigencia)