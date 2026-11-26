from datetime import date
from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.traslado import (
    MENSAJE_STOCK_INSUFICIENTE_ACEPTAR,
    Traslado,
    TrasladoCreate,
    TrasladoRechazo,
)
from app.repositories.traslado_repository import TrasladoRepository

MENSAJE_FALLA_DISPONIBILIDAD = "No fue posible consultar la disponibilidad del producto"
MENSAJE_FALLA_TRASLADO = "No fue posible radicar la solicitud de traslado"
MENSAJE_FALLA_COMPLETAR = "No fue posible completar el traslado"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_PRODUCTO_NO_EN_ORIGEN = "El producto no existe en la sucursal de origen"
MENSAJE_TRASLADO_NO_ENCONTRADO = "Traslado no encontrado"


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

    # ── HU-10: consultar traslados de la sucursal ─────────────
    def listar_traslados(
        self,
        id_sucursal: int,
        estado: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> list[dict]:
        try:
            return self.repo.listar_por_sucursal(
                id_sucursal=id_sucursal, estado=estado, tipo=tipo
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

    # ── HU-10: aceptar traslado (operación atómica con reversión)
    def aceptar(self, id_traslado: int, id_sucursal_sesion: int) -> dict:
        try:
            traslado = self.repo.buscar_por_id(id_traslado)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        if traslado is None:
            raise ErrorNegocio(MENSAJE_TRASLADO_NO_ENCONTRADO, 404)

        traslado.validar_gestionable_por_origen(id_sucursal_sesion)

        try:
            sucursal_origen = self.repo.obtener_sucursal(traslado.id_sucursal_origen)
            sucursal_destino = self.repo.obtener_sucursal(traslado.id_sucursal_destino)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        if sucursal_origen is None or sucursal_destino is None:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)

        Traslado.validar_sucursales_activas_ejecucion(
            estado_origen=sucursal_origen["estado"],
            estado_destino=sucursal_destino["estado"],
        )

        try:
            stock_origen = self.repo.consultar_stock_producto(
                traslado.id_producto, traslado.id_sucursal_origen
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        disponible_actual = stock_origen["cantidad"] if stock_origen else 0
        Traslado.validar_disponibilidad(
            cantidad_solicitada=traslado.cantidad,
            cantidad_disponible=disponible_actual,
            mensaje_insuficiente=MENSAJE_STOCK_INSUFICIENTE_ACEPTAR,
        )

        stock_descontado = False
        try:
            nuevo_stock_origen = self.repo.descontar_stock_origen(
                traslado.id_producto, traslado.id_sucursal_origen, traslado.cantidad
            )
            stock_descontado = True

            nuevo_stock_destino = self.repo.incrementar_stock_destino(
                traslado.id_producto, traslado.id_sucursal_destino, traslado.cantidad
            )

            traslado.confirmar_ejecucion()
            self.repo.actualizar(traslado)
        except Exception as e:
            if stock_descontado:
                self.repo.revertir_descuento_origen(
                    traslado.id_producto, traslado.id_sucursal_origen, traslado.cantidad
                )
            traslado.estado = "pendiente"
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        return {
            "id_traslado": traslado.id,
            "estado": traslado.estado,
            "stock_origen": nuevo_stock_origen,
            "stock_destino": nuevo_stock_destino,
        }

    # ── HU-10: rechazar traslado con motivo ───────────────────
    def rechazar(
        self, id_traslado: int, id_sucursal_sesion: int, datos: TrasladoRechazo
    ) -> dict:
        try:
            traslado = self.repo.buscar_por_id(id_traslado)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        if traslado is None:
            raise ErrorNegocio(MENSAJE_TRASLADO_NO_ENCONTRADO, 404)

        traslado.validar_gestionable_por_origen(id_sucursal_sesion)
        traslado.rechazar(datos.motivo or "")

        try:
            self.repo.actualizar(traslado)
        except Exception as e:
            traslado.estado = "pendiente"
            traslado.motivo_rechazo = None
            raise ErrorNegocio(MENSAJE_FALLA_COMPLETAR, 503) from e

        return {
            "id_traslado": traslado.id,
            "estado": traslado.estado,
            "motivo": traslado.motivo_rechazo,
        }