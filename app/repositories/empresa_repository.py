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


# Instancia única compartida por todo el programa
empresa_repository = EmpresaRepository()