from typing import Optional

from app.domain.entities.empresa import Empresa


class EmpresaRepository:
    """Único lugar que toca los datos. Hoy: una lista en memoria. Sin reglas de negocio."""

    def __init__(self):
        self._datos: list[Empresa] = []
        self._siguiente_id: int = 1

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


# Instancia única compartida por todo el programa
empresa_repository = EmpresaRepository()    