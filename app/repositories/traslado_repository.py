from typing import Optional

from app.domain.entities.traslado import Traslado
from app.repositories.producto_repository import producto_repository
from app.repositories.sucursal_repository import sucursal_repository


class TrasladoRepository:
    def __init__(self):
        self._datos: list[Traslado] = []
        self._siguiente_id: int = 1

    def obtener_sucursal(self, id_sucursal: int) -> Optional[dict]:
        sucursal = next(
            (s for s in sucursal_repository._datos if s.id == id_sucursal),
            None,
        )
        if sucursal is None:
            return None
        return {
            "id_sucursal": sucursal.id,
            "id_empresa": sucursal.id_empresa,
            "nombre": sucursal.nombre,
            "estado": sucursal.estado,
        }

    def listar_sucursales_empresa(self, id_empresa: int) -> list[dict]:
        sucursales = sucursal_repository.listar_por_empresa(id_empresa)
        return [
            {
                "id_sucursal": s.id,
                "id_empresa": s.id_empresa,
                "nombre": s.nombre,
                "estado": s.estado,
            }
            for s in sucursales
        ]

    def consultar_stock_en_sucursales(
        self, sucursales_empresa: list[dict], criterio_producto: str
    ) -> tuple[str, Optional[str], list[dict]]:
        mapa_sucursales = {s["id_sucursal"]: s for s in sucursales_empresa}
        criterio = criterio_producto.strip().lower()

        coincidencias = [
            p
            for p in producto_repository._datos
            if p.id_sucursal in mapa_sucursales
            and (p.codigo.lower() == criterio or criterio in p.nombre.lower())
        ]

        if not coincidencias:
            return criterio_producto.strip(), None, []

        referencia = coincidencias[0]
        resultados = []
        for prod in coincidencias:
            suc = mapa_sucursales[prod.id_sucursal]
            resultados.append(
                {
                    "id_sucursal": suc["id_sucursal"],
                    "nombre_sucursal": suc["nombre"],
                    "estado_sucursal": suc["estado"],
                    "codigo": prod.codigo,
                    "nombre_producto": prod.nombre,
                    "cantidad": prod.cantidad,
                }
            )

        return referencia.nombre, referencia.codigo, resultados

    def consultar_stock_producto(
        self, id_producto: int, id_sucursal_origen: int
    ) -> Optional[dict]:
        producto = producto_repository.buscar_por_id_y_sucursal(
            id_producto, id_sucursal_origen
        )
        if producto is None:
            return None
        return {
            "id_producto": producto.id,
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "cantidad": producto.cantidad,
        }

    def crear(self, traslado: Traslado) -> Traslado:
        traslado.id = self._siguiente_id
        self._siguiente_id += 1
        self._datos.append(traslado)
        return traslado


traslado_repository = TrasladoRepository()