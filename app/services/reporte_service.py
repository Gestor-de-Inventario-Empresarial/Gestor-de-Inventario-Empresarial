from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.reporte import Reporte
from app.repositories.reporte_repository import ReporteRepository

MENSAJE_FALLA = "No fue posible generar el reporte"


class ReporteService:
    """Coordina la generación de reportes en modo de solo lectura."""

    def __init__(self, repo: ReporteRepository):
        self.repo = repo

    def _resolver_sucursales_objetivo(
        self, id_empresa: int, id_sucursal: Optional[int]
    ) -> list[dict]:
        if id_sucursal is not None:
            try:
                sucursal = self.repo.buscar_sucursal_por_id(id_sucursal)
            except Exception as e:
                raise ErrorNegocio(MENSAJE_FALLA, 503) from e

            sucursal_valida = Reporte.validar_sucursal_empresa(sucursal, id_empresa)
            return [sucursal_valida]

        try:
            return self.repo.consultar_sucursales_empresa(id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

    # ── HU-14: Reporte de inventario ──────────────────────────
    def generar_reporte_inventario(
        self,
        id_empresa: int,
        fecha_inicio: str,
        fecha_fin: str,
        id_sucursal: Optional[int] = None,
        parte: int = 1,
    ) -> dict:
        _, _, total_partes, sub_inicio, sub_fin = Reporte.validar_y_calcular_particion(
            fecha_inicio, fecha_fin, parte
        )
        sucursales = self._resolver_sucursales_objetivo(id_empresa, id_sucursal)

        try:
            movimientos = self.repo.consultar_historico_inventario()
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return Reporte.consolidar_inventario(
            sucursales=sucursales,
            movimientos=movimientos,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            sub_inicio=sub_inicio,
            sub_fin=sub_fin,
            parte=parte,
            total_partes=total_partes,
        )

    # ── HU-14: Reporte de traslados ───────────────────────────
    def generar_reporte_traslados(
        self,
        id_empresa: int,
        fecha_inicio: str,
        fecha_fin: str,
        id_sucursal: Optional[int] = None,
        parte: int = 1,
    ) -> dict:
        _, _, total_partes, sub_inicio, sub_fin = Reporte.validar_y_calcular_particion(
            fecha_inicio, fecha_fin, parte
        )
        sucursales = self._resolver_sucursales_objetivo(id_empresa, id_sucursal)
        ids_validos = {s["id_sucursal"] for s in sucursales}

        try:
            traslados = self.repo.consultar_historial_traslados()
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return Reporte.consolidar_traslados(
            ids_sucursales_validas=ids_validos,
            traslados=traslados,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            sub_inicio=sub_inicio,
            sub_fin=sub_fin,
            parte=parte,
            total_partes=total_partes,
            solo_rechazados=False,
        )

    # ── HU-14: Reporte de solicitudes rechazadas ──────────────
    def generar_reporte_traslados_rechazados(
        self,
        id_empresa: int,
        fecha_inicio: str,
        fecha_fin: str,
        id_sucursal: Optional[int] = None,
        parte: int = 1,
    ) -> dict:
        _, _, total_partes, sub_inicio, sub_fin = Reporte.validar_y_calcular_particion(
            fecha_inicio, fecha_fin, parte
        )
        sucursales = self._resolver_sucursales_objetivo(id_empresa, id_sucursal)
        ids_validos = {s["id_sucursal"] for s in sucursales}

        try:
            traslados = self.repo.consultar_historial_traslados()
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return Reporte.consolidar_traslados(
            ids_sucursales_validas=ids_validos,
            traslados=traslados,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            sub_inicio=sub_inicio,
            sub_fin=sub_fin,
            parte=parte,
            total_partes=total_partes,
            solo_rechazados=True,
        )