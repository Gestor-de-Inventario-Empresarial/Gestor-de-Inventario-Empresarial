from datetime import date
from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.traslado import Traslado, TrasladoCreate
from app.repositories.traslado_repository import TrasladoRepository

MENSAJE_FALLA_DISPONIBILIDAD = "No fue posible consultar la disponibilidad del producto"
MENSAJE_FALLA_TRASLADO = "No fue posible radicar la solicitud de traslado"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_PRODUCTO_NO_EN_ORIGEN = "El producto no existe en la sucursal de origen"


class TrasladoService:
    def __init__(self, repo: TrasladoRepository):
        self.repo = repo

    # ── HU-08 ─────────────────────────────────────────────────
    def buscar_disponibilidad(
        self,
        id_sucursal_solicitante: int,
        token: Optional[str],
        producto: Optional[str],
    ) -> dict:
        Traslado.validar_sesion_autenticada(token)
        criterio_producto = Traslado.validar_parametro_producto(producto)

        try:
            sucursal_solicitante = self.repo.obtener_sucursal(id_sucursal_solicitante)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_DISPONIBILIDAD, 503) from e

        Traslado.validar_sucursal_solicitante_activa(sucursal_solicitante)

        try:
            sucursales_empresa = self.repo.listar_sucursales_empresa(
                sucursal_solicitante["id_empresa"]
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_DISPONIBILIDAD, 503) from e

        Traslado.validar_empresa_multisucursal(sucursales_empresa)

        try:
            nombre_ref, codigo_ref, stock_sucursales = (
                self.repo.consultar_stock_en_sucursales(
                    sucursales_empresa, criterio_producto
                )
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_DISPONIBILIDAD, 503) from e

        disponibles = Traslado.filtrar_y_ordenar_disponibilidad(
            id_sucursal_solicitante=id_sucursal_solicitante,
            candidatas_con_stock=stock_sucursales,
            nombre_producto_referencia=nombre_ref,
        )

        resultado = {
            "producto": nombre_ref,
            "sucursales_disponibles": disponibles,
        }
        if codigo_ref is not None:
            resultado["codigo"] = codigo_ref

        return resultado

    # ── HU-09 ─────────────────────────────────────────────────
    def radicar(
        self,
        id_sucursal_solicitante: int,
        rol_usuario: str,
        datos: TrasladoCreate,
    ) -> dict:
        Traslado.validar_permiso_operativo(rol_usuario)

        if datos.id_sucursal_origen == id_sucursal_solicitante:
            raise ErrorNegocio(
                "La sucursal de origen debe ser distinta a la solicitante", 400
            )

        try:
            sucursal_solicitante = self.repo.obtener_sucursal(id_sucursal_solicitante)
            sucursal_origen = self.repo.obtener_sucursal(datos.id_sucursal_origen)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_TRASLADO, 503) from e

        if sucursal_solicitante is None or sucursal_origen is None:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)

        Traslado.validar_sucursales_traslado(
            id_sucursal_origen=datos.id_sucursal_origen,
            id_sucursal_solicitante=id_sucursal_solicitante,
            empresa_origen=sucursal_origen["id_empresa"],
            empresa_solicitante=sucursal_solicitante["id_empresa"],
            estado_origen=sucursal_origen["estado"],
            estado_solicitante=sucursal_solicitante["estado"],
        )

        try:
            stock_origen = self.repo.consultar_stock_producto(
                datos.id_producto, datos.id_sucursal_origen
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_TRASLADO, 503) from e

        if stock_origen is None:
            raise ErrorNegocio(MENSAJE_PRODUCTO_NO_EN_ORIGEN, 404)

        Traslado.validar_disponibilidad(
            cantidad_solicitada=datos.cantidad,
            cantidad_disponible=stock_origen["cantidad"],
        )

        traslado = Traslado(
            id=None,
            id_sucursal_origen=datos.id_sucursal_origen,
            id_sucursal_destino=id_sucursal_solicitante,
            id_producto=datos.id_producto,
            cantidad=datos.cantidad,
            estado="pendiente",
            fecha_solicitud=date.today().isoformat(),
        )

        try:
            guardado = self.repo.crear(traslado)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_TRASLADO, 503) from e

        return guardado.to_response()