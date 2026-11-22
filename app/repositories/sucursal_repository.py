from typing import Optional

from app.domain.entities.sucursal import Sucursal


class SucursalRepository:
    """Único lugar que toca los datos de sucursales. Almacenamiento en memoria sin reglas de negocio."""

    def __init__(self):
        self._datos: list[Sucursal] = []
        self._siguiente_id: int = 1

    def existe_codigo_en_empresa(self, id_empresa: int, codigo: str) -> bool:
        buscado = codigo.strip().lower()
        return any(
            s.id_empresa == id_empresa and s.codigo.lower() == buscado
            for s in self._datos
        )

    def crear(self, sucursal: Sucursal) -> Sucursal:
        sucursal.id = self._siguiente_id
        self._siguiente_id += 1
        self._datos.append(sucursal)
        return sucursal

    def listar_por_empresa(self, id_empresa: int, estado: Optional[str] = None) -> list[Sucursal]:
        resultado = [s for s in self._datos if s.id_empresa == id_empresa]
        if estado:
            estado_buscado = estado.strip().lower()
            resultado = [s for s in resultado if s.estado.lower() == estado_buscado]
        return resultado

    def buscar_por_id_y_empresa(self, id_sucursal: int, id_empresa: int) -> Optional[Sucursal]:
        return next(
            (s for s in self._datos if s.id == id_sucursal and s.id_empresa == id_empresa),
            None,
        )

    def actualizar(self, sucursal: Sucursal) -> Sucursal:
        for i, existente in enumerate(self._datos):
            if existente.id == sucursal.id:
                self._datos[i] = sucursal
                break
        return sucursal

    # HU-05: punto de enlace con MOD-03 (Traslados.consultarPendientes)
    def consultar_traslados_pendientes(self, id_sucursal: int) -> list[dict]:
        
        return []


# Instancia única compartida por todo el programa
sucursal_repository = SucursalRepository()