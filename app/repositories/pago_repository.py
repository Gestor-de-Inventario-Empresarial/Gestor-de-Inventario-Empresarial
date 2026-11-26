from datetime import date
from typing import Optional

from app.domain.entities.pago import TransaccionPago
from app.repositories.empresa_repository import empresa_repository
from app.repositories.suscripcion_repository import suscripcion_repository


class PagoRepository:
    def __init__(self):
        self._planes: dict[int, dict] = {
            1: {"id_plan": 1, "nombre": "Plan Mensual Estándar", "monto": 150000},
            2: {"id_plan": 2, "nombre": "Plan Mensual Empresarial", "monto": 280000},
        }
        self._transacciones: list[TransaccionPago] = []
        self._revisiones_manuales: list[dict] = []
        self._siguiente_id: int = 1

    # Punto de enlace con MOD-01 (Empresas.consultarEmpresa)
    def consultar_empresa(self, id_empresa: int) -> Optional[dict]:
        empresa = next(
            (e for e in empresa_repository._datos if e.id == id_empresa),
            None,
        )
        if empresa is None:
            return None
        return {
            "id_empresa": empresa.id,
            "nombre": empresa.nombre,
            "estado": empresa.estado,
        }

    def obtener_plan(self, id_plan: int) -> Optional[dict]:
        return self._planes.get(id_plan)

    def obtener_siguiente_secuencial(self) -> int:
        return self._siguiente_id

    def registrar_transaccion(self, transaccion: TransaccionPago) -> TransaccionPago:
        transaccion.id = self._siguiente_id
        self._siguiente_id += 1
        self._transacciones.append(transaccion)
        return transaccion

    def actualizar_transaccion(self, transaccion: TransaccionPago) -> TransaccionPago:
        for i, existente in enumerate(self._transacciones):
            if existente.id == transaccion.id:
                self._transacciones[i] = transaccion
                break
        return transaccion

    def registrar_constancia_revision(self, transaccion: TransaccionPago):
        self._revisiones_manuales.append(
            {
                "id_transaccion": transaccion.id,
                "id_empresa": transaccion.id_empresa,
                "referencia": transaccion.referencia,
                "monto": transaccion.monto,
                "estado": transaccion.estado,
            }
        )

    # Renueva la suscripción en MOD-06 (válida para todas las sucursales de la empresa)
    def confirmar_pago_y_renovar_suscripcion(
        self, transaccion: TransaccionPago, fecha_pago: date
    ):
        suscripcion_repository.registrar_fecha_pago(transaccion.id_empresa, fecha_pago)
        self.actualizar_transaccion(transaccion)

    # Cliente de pasarela externa Wompi (solo recibe referencia, monto y token_pago)
    def procesar_cobro_wompi(
        self, referencia: str, monto: int, token_pago: str
    ) -> dict:
        token_norm = token_pago.strip().lower()
        if token_norm == "tok_error_pasarela":
            raise TimeoutError("Tiempo de espera agotado con Wompi")
        if token_norm == "tok_rechazado":
            return {"status": "DECLINED", "motivo": "Fondos insuficientes o tarjeta rechazada"}
        if token_norm == "tok_pendiente":
            return {"status": "PENDING"}
        return {"status": "APPROVED"}


pago_repository = PagoRepository()