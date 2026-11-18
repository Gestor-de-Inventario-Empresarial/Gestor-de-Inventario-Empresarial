from typing import Optional

from app.domain.entities.empresa import Empresa


class EmpresaRepository:
    """Único lugar que toca los datos. Hoy: almacenamiento en memoria. Sin reglas de negocio."""

    def __init__(self):
        self._datos: list[Empresa] = []
        self._siguiente_id: int = 1
        # Referencia en memoria para simular cascada mientras se integra MOD-01 Sucursales
        self._sucursales: list[dict] = []

    def existe_nit(self, nit: str) -> bool:
        return any(e.nit == nit for e in self._datos)

    def crear(self, empresa: Empresa) -> Empresa:
        empresa.id = self._siguiente_id
        self._siguiente_id += 1
        self._datos.append(empresa)
        return empresa

    def buscar_por_id(self, id_empresa: int) -> Optional[Empresa]:
        return next((e for e in self._datos if e.id == id_empresa), None)

    def buscar_por_nit(self, nit: str) -> Optional[Empresa]:
        return next((e for e in self._datos if e.nit == nit), None)

    def buscar_por_nombre(self, nombre: str) -> Optional[Empresa]:
        buscado = nombre.strip().lower()
        return next((e for e in self._datos if e.nombre.lower() == buscado), None)

    def actualizar(self, empresa: Empresa) -> Empresa:
        for i, existente in enumerate(self._datos):
            if existente.id == empresa.id:
                self._datos[i] = empresa
                break
        return empresa

    def consultar_traslados_pendientes(self, id_empresa: int) -> list[dict]:
        """
        Punto de integración con Traslados.consultarPendientes (MOD-03).
        Mientras MOD-03 se implementa, retorna lista vacía por defecto.
        """
        return []

    def actualizar_estado_cascada(self, id_empresa: int, nuevo_estado: str) -> int:
        """
        Actualiza el estado de la empresa y, en cascada, el de todas sus sucursales.
        Retorna la cantidad de sucursales afectadas.
        """
        sucursales_empresa = [s for s in self._sucursales if s.get("id_empresa") == id_empresa]
        for sucursal in sucursales_empresa:
            sucursal["estado"] = nuevo_estado

        for existente in self._datos:
            if existente.id == id_empresa:
                existente.estado = nuevo_estado
                break

        return len(sucursales_empresa)


# Instancia única compartida por todo el programa
empresa_repository = EmpresaRepository()