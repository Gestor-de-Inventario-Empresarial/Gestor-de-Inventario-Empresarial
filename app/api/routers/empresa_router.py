from fastapi import APIRouter, status

from app.core.responses import respuesta
from app.domain.entities.empresa import EmpresaCreate
from app.repositories.empresa_repository import empresa_repository
from app.services.empresa_service import EmpresaService

router = APIRouter(prefix="/api/v1/empresas", tags=["Empresas"])

service = EmpresaService(repo=empresa_repository)


# POST /api/v1/empresas  (HU-01)
@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_empresa(datos: EmpresaCreate):
    """Registra una empresa cliente. Los errores los convierte el manejador global."""
    empresa = service.crear(datos)
    return respuesta(True, empresa, "Empresa registrada exitosamente")