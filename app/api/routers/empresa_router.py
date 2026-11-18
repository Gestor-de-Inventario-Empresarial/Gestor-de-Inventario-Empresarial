from typing import Optional

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.responses import respuesta
from app.domain.entities.empresa import (
    EmpresaCreate,
    EmpresaEstadoUpdate,
    EmpresaUpdate,
    ErrorTrasladosPendientes,
)
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


# PATCH /api/v1/empresas/{id_empresa}/estado  (HU-03)
@router.patch(
    "/{id_empresa}/estado",
    summary="Activar o inactivar una empresa en cascada",
    description=(
        "Cambia el estado operativo de la empresa ('activo' o 'inactivo') y propaga el cambio "
        "en cascada a todas sus sucursales. Antes de inactivar, valida mediante RN-03 que ninguna "
        "sucursal tenga traslados pendientes o en curso."
    ),
    responses={
        200: {
            "description": "Estado actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Estado de la empresa actualizado exitosamente",
                        "data": {
                            "id_empresa": 1,
                            "estado": "inactivo",
                            "sucursales_afectadas": 3,
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Valor de estado no válido",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El estado debe ser 'activo' o 'inactivo'",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Empresa no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Empresa no encontrada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Conflicto por traslados en curso (RN-03) o porque la empresa ya tiene ese estado",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No es posible inactivar la empresa: existen traslados en curso",
                        "data": {
                            "id_empresa": 1,
                            "traslados_pendientes": [
                                {
                                    "id_traslado": 12,
                                    "sucursal_origen": "Sucursal Centro",
                                    "sucursal_destino": "Sucursal Norte",
                                }
                            ],
                        },
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos o en el módulo de Traslados",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible cambiar el estado de la empresa",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def cambiar_estado_empresa(id_empresa: int, datos: EmpresaEstadoUpdate):
    """Activa o inactiva una empresa y actualiza en cascada el estado de sus sucursales."""
    try:
        resultado = service.cambiar_estado(id_empresa, datos)
        return respuesta(True, resultado, "Estado de la empresa actualizado exitosamente")
    except ErrorTrasladosPendientes as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=respuesta(False, e.datos, e.mensaje),
        )