from datetime import date
from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.producto import (
    Producto,
    ProductoCreate,
    ProductoRetiroCreate,
    ProductoUpdate,
)
from app.repositories.producto_repository import ProductoRepository

MENSAJE_FALLA = "No fue posible procesar la solicitud de producto"
MENSAJE_FALLA_EXISTENCIAS = "No fue posible procesar la solicitud de existencias"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_PRODUCTO_NO_ENCONTRADO = "Producto no encontrado"
MENSAJE_SIN_RESULTADOS = "No se encontraron productos con el criterio indicado"
MENSAJE_PERMISO_OTRA_SUCURSAL = "No tiene permisos para modificar el inventario de otra sucursal"


class ProductoService:
    """Coordina el registro, actualización, consulta y retiro de existencias por sucursal."""

    def __init__(self, repo: ProductoRepository):
        self.repo = repo

    def _verificar_sucursal_activa(self, id_sucursal: int, mensaje_error_bd: str = MENSAJE_FALLA):
        try:
            estado = self.repo.obtener_estado_sucursal(id_sucursal)
        except Exception as e:
            raise ErrorNegocio(mensaje_error_bd, 503) from e

        if estado is None:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)

        Producto.validar_sucursal_activa(estado)

    # ── HU-06: registrar producto en una sucursal ─────────────
    def crear(self, id_sucursal: int, datos: ProductoCreate) -> dict:
        self._verificar_sucursal_activa(id_sucursal)
        Producto.validar_precio_y_cantidad(datos.precio, datos.cantidad)

        try:
            codigo_registrado = self.repo.existe_codigo_en_sucursal(
                id_sucursal, datos.codigo
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        Producto.validar_codigo_por_sucursal(codigo_registrado)

        producto = Producto(
            id=None,
            id_sucursal=id_sucursal,
            codigo=datos.codigo,
            nombre=datos.nombre,
            categoria=datos.categoria,
            precio=datos.precio,
            cantidad=datos.cantidad,
        )

        try:
            guardado = self.repo.crear(producto)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return guardado.to_response()

    # ── HU-06: actualizar precio o cantidad de un producto ────
    def actualizar(
        self, id_producto: int, id_sucursal: int, datos: ProductoUpdate
    ) -> dict:
        self._verificar_sucursal_activa(id_sucursal)

        try:
            producto = self.repo.buscar_por_id_y_sucursal(id_producto, id_sucursal)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        if producto is None:
            raise ErrorNegocio(MENSAJE_PRODUCTO_NO_ENCONTRADO, 404)

        producto.actualizar_stock_y_precio(datos.precio, datos.cantidad)

        try:
            actualizado = self.repo.actualizar(producto)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return actualizado.to_actualizacion_response()

    # ── HU-07: consultar existencias por sucursal ─────────────
    def consultar_existencias(
        self, id_sucursal: int, busqueda: Optional[str] = None
    ) -> list[dict]:
        try:
            productos = self.repo.buscar_por_sucursal_y_criterio(id_sucursal, busqueda)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_EXISTENCIAS, 503) from e

        if not productos:
            raise ErrorNegocio(MENSAJE_SIN_RESULTADOS, 404)

        return [p.to_existencia_response() for p in productos]

    # ── HU-07: retirar existencias con motivo ─────────────────
    def retirar_existencias(
        self, id_producto: int, id_sucursal: int, datos: ProductoRetiroCreate
    ) -> dict:
        motivo_valido = Producto.validar_motivo_retiro(datos.motivo or "")

        try:
            producto = self.repo.buscar_por_id(id_producto)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_EXISTENCIAS, 503) from e

        if producto is None:
            raise ErrorNegocio(MENSAJE_PRODUCTO_NO_ENCONTRADO, 404)

        if producto.id_sucursal != id_sucursal:
            raise ErrorNegocio(MENSAJE_PERMISO_OTRA_SUCURSAL, 403)

        try:
            traslados_pendientes = self.repo.consultar_traslados_pendientes(id_producto)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_EXISTENCIAS, 503) from e

        Producto.validar_sin_traslados_pendientes(id_producto, traslados_pendientes)

        fecha_retiro = date.today().isoformat()
        try:
            return self.repo.retirar(producto, motivo_valido, fecha_retiro)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_EXISTENCIAS, 503) from e