from typing import Optional

from app.domain.entities.producto import Producto
from app.repositories.sucursal_repository import sucursal_repository


class ProductoRepository:
    """Almacenamiento en memoria para productos por sucursal y trazabilidad de retiros."""

    def __init__(self):
        self._datos: list[Producto] = []
        self._retiros: list[dict] = []
        self._siguiente_id: int = 1

    # Punto de enlace con MOD-01 (INT-06: Sucursales.validarEstado)
    def obtener_estado_sucursal(self, id_sucursal: int) -> Optional[str]:
        sucursal = next(
            (s for s in sucursal_repository._datos if s.id == id_sucursal),
            None,
        )
        return sucursal.estado if sucursal else None

    def existe_codigo_en_sucursal(self, id_sucursal: int, codigo: str) -> bool:
        buscado = codigo.strip().lower()
        return any(
            p.id_sucursal == id_sucursal and p.codigo.lower() == buscado
            for p in self._datos
        )

    def crear(self, producto: Producto) -> Producto:
        producto.id = self._siguiente_id
        self._siguiente_id += 1
        self._datos.append(producto)
        return producto

    def buscar_por_id(self, id_producto: int) -> Optional[Producto]:
        return next((p for p in self._datos if p.id == id_producto), None)

    def buscar_por_id_y_sucursal(
        self, id_producto: int, id_sucursal: int
    ) -> Optional[Producto]:
        return next(
            (
                p
                for p in self._datos
                if p.id == id_producto and p.id_sucursal == id_sucursal
            ),
            None,
        )

    def actualizar(self, producto: Producto) -> Producto:
        for i, existente in enumerate(self._datos):
            if existente.id == producto.id:
                self._datos[i] = producto
                break
        return producto

    # HU-07: consulta de existencias por sucursal y criterio (nombre o código)
    def buscar_por_sucursal_y_criterio(
        self, id_sucursal: int, busqueda: Optional[str] = None
    ) -> list[Producto]:
        productos_sucursal = [p for p in self._datos if p.id_sucursal == id_sucursal]
        if busqueda is None or not busqueda.strip():
            return productos_sucursal

        criterio = busqueda.strip().lower()
        return [
            p
            for p in productos_sucursal
            if criterio in p.codigo.lower() or criterio in p.nombre.lower()
        ]

    # HU-07: punto de enlace con MOD-03 (INT-08: Traslados.consultarPendientes)
    def consultar_traslados_pendientes(self, id_producto: int) -> list[dict]:
        return []

    # HU-07: elimina el producto del inventario activo y registra trazabilidad del retiro
    def retirar(self, producto: Producto, motivo: str, fecha_retiro: str) -> dict:
        self._datos = [p for p in self._datos if p.id != producto.id]
        registro = {
            "id_producto": producto.id,
            "id_sucursal": producto.id_sucursal,
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "cantidad": producto.cantidad,
            "motivo": motivo,
            "fecha_retiro": fecha_retiro,
        }
        self._retiros.append(registro)
        return {
            "id_producto": producto.id,
            "motivo": motivo,
            "fecha_retiro": fecha_retiro,
        }


# Instancia única compartida por todo el programa
producto_repository = ProductoRepository()