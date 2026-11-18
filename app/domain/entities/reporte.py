import math
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.exceptions import ErrorNegocio

MENSAJE_FORMATO_FECHA = "Formato de fecha no válido. Debe ser YYYY-MM-DD"
MENSAJE_RANGO_INVALIDO = "La fecha de inicio no puede ser posterior a la fecha de fin"
MENSAJE_PARTE_INVALIDA = "El parámetro 'parte' debe ser un entero mayor o igual a 1"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_SIN_REGISTROS = "No existen registros para los filtros indicados"

DIAS_POR_PARTE = 365


class Reporte:
    """Entidad de dominio para validación de rangos, particionamiento anual y consolidación de reportes."""

    @staticmethod
    def parsear_fecha(fecha_str: str) -> date:
        if not isinstance(fecha_str, str) or len(fecha_str.strip()) != 10:
            raise ErrorNegocio(MENSAJE_FORMATO_FECHA, 400)
        try:
            return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
        except ValueError as e:
            raise ErrorNegocio(MENSAJE_FORMATO_FECHA, 400) from e

    @classmethod
    def validar_y_calcular_particion(
        cls, fecha_inicio: str, fecha_fin: str, parte: int
    ) -> tuple[date, date, int, date, date]:
        dt_inicio = cls.parsear_fecha(fecha_inicio)
        dt_fin = cls.parsear_fecha(fecha_fin)

        if dt_inicio > dt_fin:
            raise ErrorNegocio(MENSAJE_RANGO_INVALIDO, 400)

        if parte < 1:
            raise ErrorNegocio(MENSAJE_PARTE_INVALIDA, 400)

        total_dias = (dt_fin - dt_inicio).days + 1
        total_partes = 1 if total_dias <= DIAS_POR_PARTE else math.ceil(total_dias / DIAS_POR_PARTE)

        if parte > total_partes:
            raise ErrorNegocio(
                f"La parte solicitada ({parte}) excede el total de partes disponibles ({total_partes})",
                400,
            )

        sub_inicio = dt_inicio + timedelta(days=(parte - 1) * DIAS_POR_PARTE)
        sub_fin = min(dt_fin, sub_inicio + timedelta(days=DIAS_POR_PARTE - 1))

        return dt_inicio, dt_fin, total_partes, sub_inicio, sub_fin

    @staticmethod
    def validar_sucursal_empresa(sucursal: Optional[dict], id_empresa: int) -> dict:
        if sucursal is None or sucursal.get("id_empresa") != id_empresa:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)
        return sucursal

    @staticmethod
    def _lanzar_sin_registros(fecha_inicio: str, fecha_fin: str, parte: int, total_partes: int):
        error = ErrorNegocio(MENSAJE_SIN_REGISTROS, 404)
        error.data = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "parte": parte,
            "total_partes": total_partes,
        }
        raise error

    @classmethod
    def consolidar_inventario(
        cls,
        sucursales: list[dict],
        movimientos: list[dict],
        fecha_inicio: str,
        fecha_fin: str,
        sub_inicio: date,
        sub_fin: date,
        parte: int,
        total_partes: int,
    ) -> dict:
        sucursales_con_movimientos = []

        for suc in sucursales:
            id_suc = suc["id_sucursal"]
            movs_sucursal = []
            codigos_unicos = set()

            for mov in movimientos:
                if mov["id_sucursal"] != id_suc:
                    continue
                fecha_mov = cls.parsear_fecha(mov["fecha"])
                if sub_inicio <= fecha_mov <= sub_fin:
                    codigos_unicos.add(mov["codigo"])
                    movs_sucursal.append(
                        {
                            "fecha": mov["fecha"],
                            "codigo": mov["codigo"],
                            "tipo": mov["tipo"],
                            "cantidad": mov["cantidad"],
                        }
                    )

            if movs_sucursal:
                movs_sucursal.sort(key=lambda m: m["fecha"])
                sucursales_con_movimientos.append(
                    {
                        "id_sucursal": id_suc,
                        "nombre": suc["nombre"],
                        "total_productos": len(codigos_unicos),
                        "movimientos": movs_sucursal,
                    }
                )

        if not sucursales_con_movimientos:
            cls._lanzar_sin_registros(fecha_inicio, fecha_fin, parte, total_partes)

        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "parte": parte,
            "total_partes": total_partes,
            "sucursales": sucursales_con_movimientos,
        }

    @classmethod
    def consolidar_traslados(
        cls,
        ids_sucursales_validas: set[int],
        traslados: list[dict],
        fecha_inicio: str,
        fecha_fin: str,
        sub_inicio: date,
        sub_fin: date,
        parte: int,
        total_partes: int,
        solo_rechazados: bool = False,
    ) -> dict:
        registros_filtrados = []

        for tr in traslados:
            es_rechazado = tr["estado"].lower() == "rechazado"
            if solo_rechazados != es_rechazado:
                continue

            if (
                tr["id_sucursal_origen"] not in ids_sucursales_validas
                and tr["id_sucursal_destino"] not in ids_sucursales_validas
            ):
                continue

            fecha_tr = cls.parsear_fecha(tr["fecha"])
            if not (sub_inicio <= fecha_tr <= sub_fin):
                continue

            item = {
                "id_traslado": tr["id_traslado"],
                "sucursal_origen": tr["sucursal_origen"],
                "sucursal_destino": tr["sucursal_destino"],
                "producto": tr["producto"],
                "cantidad": tr["cantidad"],
                "estado": tr["estado"],
                "fecha": tr["fecha"],
            }
            if solo_rechazados:
                item["motivo_rechazo"] = tr.get("motivo_rechazo", "Sin motivo registrado")

            registros_filtrados.append(item)

        if not registros_filtrados:
            cls._lanzar_sin_registros(fecha_inicio, fecha_fin, parte, total_partes)

        registros_filtrados.sort(key=lambda t: t["fecha"])
        clave_lista = "traslados_rechazados" if solo_rechazados else "traslados"

        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "parte": parte,
            "total_partes": total_partes,
            clave_lista: registros_filtrados,
        }