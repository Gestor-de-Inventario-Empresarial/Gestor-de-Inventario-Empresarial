from typing import Optional

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta
from app.domain.entities.sucursal import (
    SucursalCreate,
    SucursalEstadoUpdate,
    SucursalUpdate,
)
from app.repositories.sucursal_repository import sucursal_repository
from app.services.sucursal_service import SucursalService

router = APIRouter(prefix="/api/v1/sucursales", tags=["Sucursales"])

service = SucursalService(repo=sucursal_repository)


def obtener_id_empresa_sesion(
    x_empresa_id: int = Header(
        default=1,
        alias="X-Empresa-Id",
        description="ID de la empresa activa en sesión (simulado mientras se integra autenticación)",
    )
) -> int:
    return x_empresa_id


# POST /api/v1/sucursales  (HU-04)
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una sucursal",
    description=(
        "Registra una nueva sucursal en estado 'activa' asociándola automáticamente a la empresa "
        "de la sesión activa. Valida que la dirección no esté vacía y que el código sea único "
        "dentro de esa empresa."
    ),
    responses={
        201: {
            "description": "Sucursal registrada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Sucursal registrada exitosamente",
                        "data": {
                            "id_sucursal": 1,
                            "id_empresa": 1,
                            "nombre": "Sucursal Centro",
                            "direccion": "Calle 35 # 15-20, Bucaramanga",
                            "codigo": "SUC-001",
                            "estado": "activa",
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Datos obligatorios faltantes o inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La dirección es obligatoria",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Código de sucursal duplicado en la empresa",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El código de sucursal ya existe para esta empresa",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible procesar la solicitud de sucursal",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def registrar_sucursal(
    datos: SucursalCreate,
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Registra una sucursal para la empresa de la sesión activa."""
    sucursal = service.crear(id_empresa=id_empresa, datos=datos)
    return respuesta(True, sucursal, "Sucursal registrada exitosamente")


# GET /api/v1/sucursales  (HU-04)
@router.get(
    "",
    summary="Consultar sucursales de la empresa",
    description="Lista las sucursales pertenecientes a la empresa de la sesión activa, con filtro opcional por estado.",
    responses={
        200: {
            "description": "Consulta de sucursales exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Consulta de sucursales exitosa",
                        "data": [
                            {
                                "id_sucursal": 1,
                                "nombre": "Sucursal Centro",
                                "codigo": "SUC-001",
                                "estado": "activa",
                            },
                            {
                                "id_sucursal": 2,
                                "nombre": "Sucursal Norte",
                                "codigo": "SUC-002",
                                "estado": "activa",
                            },
                        ],
                        "success": True,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible procesar la solicitud de sucursal",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def consultar_sucursales(
    estado: Optional[str] = None,
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Consulta las sucursales de la empresa autenticada."""
    sucursales = service.listar(id_empresa=id_empresa, estado=estado)
    return respuesta(True, sucursales, "Consulta de sucursales exitosa")


# PUT /api/v1/sucursales/{id_sucursal}  (HU-04)
@router.put(
    "/{id_sucursal}",
    summary="Actualizar nombre y dirección de una sucursal",
    description=(
        "Actualiza el nombre y/o la dirección de una sucursal perteneciente a la empresa activa. "
        "El código y la empresa propietaria son inmutables."
    ),
    responses={
        200: {
            "description": "Sucursal actualizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Sucursal actualizada exitosamente",
                        "data": {
                            "id_sucursal": 1,
                            "id_empresa": 1,
                            "nombre": "Sucursal Centro Principal",
                            "direccion": "Carrera 27 # 36-14, Bucaramanga",
                            "codigo": "SUC-001",
                            "estado": "activa",
                        },
                        "success": True,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal no encontrada o pertenece a otra empresa",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Sucursal no encontrada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible procesar la solicitud de sucursal",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalUpdate,
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Actualiza el nombre y dirección de una sucursal de la empresa activa."""
    sucursal = service.actualizar(id_sucursal=id_sucursal, id_empresa=id_empresa, datos=datos)
    return respuesta(True, sucursal, "Sucursal actualizada exitosamente")


# PATCH /api/v1/sucursales/{id_sucursal}/estado  (HU-05)
@router.patch(
    "/{id_sucursal}/estado",
    summary="Activar o inactivar una sucursal",
    description=(
        "Cambia el estado de una sucursal ('activa' o 'inactiva') de forma independiente al resto "
        "de la empresa. Antes de inactivar, verifica en el módulo de Traslados que la sucursal "
        "no tenga traslados en curso."
    ),
    responses={
        200: {
            "description": "Estado de la sucursal actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Estado de la sucursal actualizado exitosamente",
                        "data": {
                            "id_sucursal": 2,
                            "estado": "inactiva",
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
                        "message": "El estado debe ser 'activa' o 'inactiva'",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Sucursal no encontrada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Conflicto: la sucursal ya tiene ese estado o existen traslados en curso",
            "content": {
                "application/json": {
                    "examples": {
                        "traslados_en_curso": {
                            "summary": "Bloqueo por traslados pendientes",
                            "value": {
                                "message": "No es posible inactivar la sucursal: existen traslados en curso",
                                "data": {
                                    "id_sucursal": 2,
                                    "traslados_pendientes": [
                                        {
                                            "id_traslado": 12,
                                            "sucursal_origen": "Sucursal Centro",
                                            "sucursal_destino": "Sucursal Norte",
                                        }
                                    ],
                                },
                                "success": False,
                            },
                        },
                        "mismo_estado": {
                            "summary": "La sucursal ya tiene el estado solicitado",
                            "value": {
                                "message": "La sucursal ya se encuentra en el estado solicitado",
                                "data": None,
                                "success": False,
                            },
                        },
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos o en el módulo de Traslados",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible cambiar el estado de la sucursal",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def cambiar_estado_sucursal(
    id_sucursal: int,
    datos: SucursalEstadoUpdate,
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Activa o inactiva una sucursal de la empresa activa."""
    try:
        resultado = service.cambiar_estado(
            id_sucursal=id_sucursal,
            id_empresa=id_empresa,
            datos=datos,
        )
    except ErrorNegocio as e:
        if getattr(e, "data", None) is not None:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "message": str(e),
                    "data": e.data,
                    "success": False,
                },
            )
        raise

    return respuesta(True, resultado, "Estado de la sucursal actualizado exitosamente")