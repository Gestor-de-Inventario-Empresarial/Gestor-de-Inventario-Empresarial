from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.traslado import Traslado
from app.repositories.traslado_repository import TrasladoRepository

MENSAJE_FALLA_DISPONIBILIDAD = "No fue posible consultar la disponibilidad del producto"


class TrasladoService:
    def __init__(self, repo: TrasladoRepository):
        self.repo = repo

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