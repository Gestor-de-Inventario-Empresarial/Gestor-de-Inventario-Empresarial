from datetime import date

from app.core.exceptions import ErrorNegocio
from app.domain.entities.empresa import Empresa, EmpresaCreate
from app.repositories.empresa_repository import EmpresaRepository

MENSAJE_FALLA = "No fue posible registrar la empresa"


class EmpresaService:
    """Coordina el flujo: aplica las reglas del dominio y llama al repositorio."""

    def __init__(self, repo: EmpresaRepository):
        self.repo = repo

    def crear(self, datos: EmpresaCreate) -> dict:
        empresa = Empresa(
            id=None,
            nit=datos.nit,
            nombre=datos.nombre,
            ubicacion=datos.ubicacion,
            fecha_creacion=date.fromisoformat(datos.fecha_creacion),
        )

        empresa.validar_antiguedad()  # RN-01

        try:
            nit_registrado = self.repo.existe_nit(empresa.nit)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e
        Empresa.validar_nit_unico(nit_registrado)  # RN-02

        try:
            guardada = self.repo.crear(empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e
        return guardada.to_response()