from typing import Optional

from app.domain.entities.producto import Producto
from app.repositories.sucursal_repository import sucursal_repository


class ProductoRepository:
    """Almacenamiento en memoria para productos por sucursal sin reglas de negocio."""

    def __init__(self):
        self._datos: list[Producto] = []
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


# Instancia única compartida por todo el programa
producto_repository = ProductoRepository()