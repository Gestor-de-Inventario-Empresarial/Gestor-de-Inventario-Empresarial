from datetime import date, timedelta
from typing import Optional

from app.repositories.empresa_repository import empresa_repository
from app.repositories.sucursal_repository import sucursal_repository


class SuscripcionRepository:
    def __init__(self):
        # Registro en memoria de la fecha del último pago exitoso por empresa
        self._ultimos_pagos: dict[int, date] = {
            1: date.today() - timedelta(days=15),
        }

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

    def obtener_empresa_por_sucursal(self, id_sucursal: int) -> Optional[int]:
        sucursal = next(
            (s for s in sucursal_repository._datos if s.id == id_sucursal),
            None,
        )
        return sucursal.id_empresa if sucursal else None

    def obtener_fecha_ultimo_pago(self, id_empresa: int) -> Optional[date]:
        return self._ultimos_pagos.get(id_empresa)

    def registrar_fecha_pago(self, id_empresa: int, fecha_pago: date):
        self._ultimos_pagos[id_empresa] = fecha_pago


suscripcion_repository = SuscripcionRepository()