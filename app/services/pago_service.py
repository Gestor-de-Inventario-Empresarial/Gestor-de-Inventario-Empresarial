from datetime import date

from app.core.exceptions import ErrorNegocio
from app.domain.entities.pago import (
    MENSAJE_PAGO_APROBADO,
    MENSAJE_PAGO_PENDIENTE,
    MENSAJE_PAGO_RECHAZADO,
    MENSAJE_PAGO_REVISION,
    MENSAJE_PLAN_NO_ENCONTRADO,
    PagoCreate,
    TransaccionPago,
)
from app.repositories.pago_repository import PagoRepository

MENSAJE_EMPRESA_NO_ENCONTRADA = "Empresa no encontrada"
MENSAJE_FALLA_PASARELA = "No fue posible comunicarse con la pasarela de pagos"
MENSAJE_FALLA_REGISTRO_INICIAL = "No fue posible iniciar la transacción de pago"


class PagoService:
    def __init__(self, repo: PagoRepository):
        self.repo = repo

    def procesar_pago(
        self,
        id_empresa_sesion: int,
        rol_sesion: str,
        datos: PagoCreate,
    ) -> tuple[int, bool, dict, str]:
        TransaccionPago.validar_permiso_administrador(rol_sesion)

        try:
            empresa = self.repo.consultar_empresa(id_empresa_sesion)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_REGISTRO_INICIAL, 503) from e

        if empresa is None:
            raise ErrorNegocio(MENSAJE_EMPRESA_NO_ENCONTRADA, 404)

        plan = self.repo.obtener_plan(datos.id_plan or 0)
        if plan is None:
            raise ErrorNegocio(MENSAJE_PLAN_NO_ENCONTRADO, 404)

        try:
            secuencial = self.repo.obtener_siguiente_secuencial()
            referencia = TransaccionPago.generar_referencia(
                id_empresa=id_empresa_sesion,
                secuencial=secuencial,
            )
            transaccion = TransaccionPago(
                id=None,
                id_empresa=id_empresa_sesion,
                id_plan=plan["id_plan"],
                referencia=referencia,
                monto=plan["monto"],
                estado="pendiente",
            )
            transaccion = self.repo.registrar_transaccion(transaccion)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_REGISTRO_INICIAL, 503) from e

        try:
            respuesta_wompi = self.repo.procesar_cobro_wompi(
                referencia=transaccion.referencia,
                monto=transaccion.monto,
                token_pago=datos.token_pago or "",
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_PASARELA, 503) from e

        estado_wompi = respuesta_wompi.get("status", "").upper()

        if estado_wompi == "DECLINED":
            transaccion.marcar_rechazada(
                respuesta_wompi.get("motivo", MENSAJE_PAGO_RECHAZADO)
            )
            try:
                self.repo.actualizar_transaccion(transaccion)
            except Exception:
                pass
            return (
                402,
                False,
                transaccion.to_estado_response(),
                MENSAJE_PAGO_RECHAZADO,
            )

        if estado_wompi == "PENDING":
            transaccion.marcar_pendiente()
            try:
                self.repo.actualizar_transaccion(transaccion)
            except Exception:
                pass
            return (
                202,
                True,
                transaccion.to_estado_response(),
                MENSAJE_PAGO_PENDIENTE,
            )

        # Estado APPROVED: renovar vigencia (RN-10) y asegurar persistencia con reintentos (RN-11)
        hoy = date.today()
        vigencia = TransaccionPago.calcular_nueva_vigencia(hoy)
        fecha_vencimiento = vigencia["fecha_vencimiento"]

        def _persistir_aprobacion() -> str:
            transaccion.estado = "aprobada"
            transaccion.fecha_vencimiento = fecha_vencimiento
            self.repo.confirmar_pago_y_renovar_suscripcion(transaccion, hoy)
            return fecha_vencimiento

        guardado_exitoso = transaccion.manejar_inconsistencia(_persistir_aprobacion)

        if not guardado_exitoso:
            self.repo.registrar_constancia_revision(transaccion)
            return (
                500,
                False,
                transaccion.to_estado_response(),
                MENSAJE_PAGO_REVISION,
            )

        return (
            201,
            True,
            transaccion.to_aprobada_response(),
            MENSAJE_PAGO_APROBADO,
        )