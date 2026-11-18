from app.core.exceptions import ErrorNegocio
from app.domain.entities.producto import (
    Producto,
    ProductoCreate,
    ProductoUpdate,
)
from app.repositories.producto_repository import ProductoRepository

MENSAJE_FALLA = "No fue posible procesar la solicitud de producto"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_PRODUCTO_NO_ENCONTRADO = "Producto no encontrado"


class ProductoService:
    """Coordina el registro y actualización de productos por sucursal."""

    def __init__(self, repo: ProductoRepository):
        self.repo = repo

    def _verificar_sucursal_activa(self, id_sucursal: int):
        try:
            estado = self.repo.obtener_estado_sucursal(id_sucursal)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

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