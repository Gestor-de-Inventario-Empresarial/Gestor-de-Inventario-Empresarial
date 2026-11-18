from typing import Optional

from fastapi import APIRouter, status

from app.core.responses import respuesta
from app.domain.entities.empresa import EmpresaCreate, EmpresaUpdate
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


# GET /api/v1/empresas?nit=...  o  ?nombre=...  (HU-02)
@router.get("")
def consultar_empresa(nit: Optional[str] = None, nombre: Optional[str] = None):
    """Consulta una empresa por NIT o por nombre."""
    empresa = service.buscar(nit=nit, nombre=nombre)
    return respuesta(True, empresa, "Consulta de empresa exitosa")


# PUT /api/v1/empresas/{id_empresa}  (HU-02)
@router.put("/{id_empresa}")
def actualizar_empresa(id_empresa: int, datos: EmpresaUpdate):
    """Actualiza teléfono, correo y ubicación. El NIT y la fecha de creación no se modifican."""
    empresa = service.actualizar(id_empresa, datos)
    return respuesta(True, empresa, "Datos de la empresa actualizados exitosamente")