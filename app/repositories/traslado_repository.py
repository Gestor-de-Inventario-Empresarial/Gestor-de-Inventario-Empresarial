from typing import Optional

from app.domain.entities.producto import Producto
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

    def buscar_por_id(self, id_traslado: int) -> Optional[Traslado]:
        return next((t for t in self._datos if t.id == id_traslado), None)

    def listar_por_sucursal(
        self,
        id_sucursal: int,
        estado: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> list[dict]:
        resultados = []
        tipo_norm = tipo.strip().lower() if tipo else None
        estado_norm = estado.strip().lower() if estado else None

        for t in self._datos:
            if tipo_norm == "recibidos" and t.id_sucursal_origen != id_sucursal:
                continue
            if tipo_norm == "enviados" and t.id_sucursal_destino != id_sucursal:
                continue
            if tipo_norm is None and (
                t.id_sucursal_origen != id_sucursal
                and t.id_sucursal_destino != id_sucursal
            ):
                continue

            if estado_norm and t.estado.lower() != estado_norm:
                continue

            origen = self.obtener_sucursal(t.id_sucursal_origen)
            destino = self.obtener_sucursal(t.id_sucursal_destino)
            prod = next(
                (p for p in producto_repository._datos if p.id == t.id_producto),
                None,
            )

            resultados.append(
                {
                    "id_traslado": t.id,
                    "sucursal_origen": origen["nombre"] if origen else f"Sucursal {t.id_sucursal_origen}",
                    "sucursal_destino": destino["nombre"] if destino else f"Sucursal {t.id_sucursal_destino}",
                    "producto": prod.nombre if prod else f"Producto {t.id_producto}",
                    "cantidad": t.cantidad,
                    "estado": t.estado,
                    "fecha_solicitud": t.fecha_solicitud,
                }
            )

        return resultados

    def descontar_stock_origen(
        self, id_producto: int, id_sucursal_origen: int, cantidad: int
    ) -> int:
        producto = producto_repository.buscar_por_id_y_sucursal(
            id_producto, id_sucursal_origen
        )
        if producto is None:
            raise RuntimeError("Producto no encontrado en origen")
        producto.cantidad -= cantidad
        producto_repository.actualizar(producto)
        return producto.cantidad

    def revertir_descuento_origen(
        self, id_producto: int, id_sucursal_origen: int, cantidad: int
    ):
        producto = producto_repository.buscar_por_id_y_sucursal(
            id_producto, id_sucursal_origen
        )
        if producto is not None:
            producto.cantidad += cantidad
            producto_repository.actualizar(producto)

    def incrementar_stock_destino(
        self, id_producto_origen: int, id_sucursal_destino: int, cantidad: int
    ) -> int:
        prod_origen = next(
            (p for p in producto_repository._datos if p.id == id_producto_origen),
            None,
        )
        if prod_origen is None:
            raise RuntimeError("Referencia de producto no encontrada")

        prod_destino = next(
            (
                p
                for p in producto_repository._datos
                if p.id_sucursal == id_sucursal_destino
                and p.codigo.lower() == prod_origen.codigo.lower()
            ),
            None,
        )

        if prod_destino is not None:
            prod_destino.cantidad += cantidad
            producto_repository.actualizar(prod_destino)
            return prod_destino.cantidad

        nuevo_destino = Producto(
            id=None,
            id_sucursal=id_sucursal_destino,
            codigo=prod_origen.codigo,
            nombre=prod_origen.nombre,
            categoria=prod_origen.categoria,
            precio=prod_origen.precio,
            cantidad=cantidad,
        )
        creado = producto_repository.crear(nuevo_destino)
        return creado.cantidad

    def actualizar(self, traslado: Traslado) -> Traslado:
        for i, existente in enumerate(self._datos):
            if existente.id == traslado.id:
                self._datos[i] = traslado
                break
        return traslado


traslado_repository = TrasladoRepository()