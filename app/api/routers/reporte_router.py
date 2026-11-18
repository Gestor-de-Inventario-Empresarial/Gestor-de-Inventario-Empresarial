from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta
from app.repositories.reporte_repository import reporte_repository
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/api/v1/reportes", tags=["Reportes"])

service = ReporteService(repo=reporte_repository)


def obtener_id_empresa_sesion(
    x_empresa_id: int = Header(
        default=1,
        alias="X-Empresa-Id",
        description="ID de la empresa activa en sesión (simulado mientras se integra autenticación)",
    )
) -> int:
    return x_empresa_id


def _manejar_error_reporte(error: ErrorNegocio):
    if getattr(error, "data", None) is not None:
        return JSONResponse(
            status_code=error.codigo_http,
            content={
                "message": str(error),
                "data": error.data,
                "success": False,
            },
        )
    raise error


# GET /api/v1/reportes/inventario  (HU-14)
@router.get(
    "/inventario",
    summary="Generar reporte de inventario",
    description=(
        "Genera en modo de solo lectura el reporte consolidado de movimientos y existencias de "
        "inventario por sucursal en un rango de fechas (YYYY-MM-DD). Si el rango supera un año, "
        "divide la respuesta en partes mediante el parámetro 'parte'."
    ),
    responses={
        200: {
            "description": "Reporte de inventario generado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Reporte de inventario generado exitosamente",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                            "sucursales": [
                                {
                                    "id_sucursal": 1,
                                    "nombre": "Sucursal Centro",
                                    "total_productos": 2,
                                    "movimientos": [
                                        {
                                            "fecha": "2026-03-10",
                                            "codigo": "PRD-0001",
                                            "tipo": "entrada",
                                            "cantidad": 100,
                                        }
                                    ],
                                }
                            ],
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Rango o formato de fechas inválido",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La fecha de inicio no puede ser posterior a la fecha de fin",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal no encontrada o sin registros en el rango",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No existen registros para los filtros indicados",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                        },
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos o en otros módulos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible generar el reporte",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def reporte_inventario(
    fecha_inicio: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD", examples=["2026-01-01"]),
    fecha_fin: str = Query(..., description="Fecha final en formato YYYY-MM-DD", examples=["2026-06-30"]),
    id_sucursal: Optional[int] = Query(default=None, description="ID opcional de sucursal a filtrar"),
    parte: int = Query(default=1, description="Número de parte cuando el rango supera 1 año"),
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Genera el reporte de inventario consolidado por sucursal."""
    try:
        datos = service.generar_reporte_inventario(
            id_empresa=id_empresa,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_sucursal=id_sucursal,
            parte=parte,
        )
    except ErrorNegocio as e:
        return _manejar_error_reporte(e)

    return respuesta(True, datos, "Reporte de inventario generado exitosamente")


# GET /api/v1/reportes/traslados  (HU-14)
@router.get(
    "/traslados",
    summary="Generar reporte de traslados entre sucursales",
    description=(
        "Genera en modo de solo lectura el historial de traslados entre sucursales de la empresa "
        "filtrando por rango de fechas y sucursal opcional."
    ),
    responses={
        200: {
            "description": "Reporte de traslados generado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Reporte de traslados generado exitosamente",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                            "traslados": [
                                {
                                    "id_traslado": 12,
                                    "sucursal_origen": "Sucursal Norte",
                                    "sucursal_destino": "Sucursal Centro",
                                    "producto": "Cuaderno argollado 100 hojas",
                                    "cantidad": 30,
                                    "estado": "completado",
                                    "fecha": "2026-03-15",
                                }
                            ],
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Rango o formato de fechas inválido",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La fecha de inicio no puede ser posterior a la fecha de fin",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal no encontrada o sin registros en el rango",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No existen registros para los filtros indicados",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                        },
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos o en otros módulos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible generar el reporte",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def reporte_traslados(
    fecha_inicio: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD", examples=["2026-01-01"]),
    fecha_fin: str = Query(..., description="Fecha final en formato YYYY-MM-DD", examples=["2026-06-30"]),
    id_sucursal: Optional[int] = Query(default=None, description="ID opcional de sucursal a filtrar"),
    parte: int = Query(default=1, description="Número de parte cuando el rango supera 1 año"),
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Genera el reporte de traslados entre sucursales."""
    try:
        datos = service.generar_reporte_traslados(
            id_empresa=id_empresa,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_sucursal=id_sucursal,
            parte=parte,
        )
    except ErrorNegocio as e:
        return _manejar_error_reporte(e)

    return respuesta(True, datos, "Reporte de traslados generado exitosamente")


# GET /api/v1/reportes/traslados-rechazados  (HU-14)
@router.get(
    "/traslados-rechazados",
    summary="Generar reporte de solicitudes de traslado rechazadas",
    description=(
        "Genera en modo de solo lectura el historial de solicitudes de traslado rechazadas, "
        "incluyendo el motivo del rechazo registrado en cada caso."
    ),
    responses={
        200: {
            "description": "Reporte de traslados rechazados generado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Reporte de traslados rechazados generado exitosamente",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                            "traslados_rechazados": [
                                {
                                    "id_traslado": 15,
                                    "sucursal_origen": "Sucursal Centro",
                                    "sucursal_destino": "Sucursal Norte",
                                    "producto": "Resma papel carta 75g",
                                    "cantidad": 20,
                                    "estado": "rechazado",
                                    "motivo_rechazo": "Stock insuficiente en sucursal origen",
                                    "fecha": "2026-04-02",
                                }
                            ],
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Rango o formato de fechas inválido",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La fecha de inicio no puede ser posterior a la fecha de fin",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal no encontrada o sin registros en el rango",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No existen registros para los filtros indicados",
                        "data": {
                            "fecha_inicio": "2026-01-01",
                            "fecha_fin": "2026-06-30",
                            "parte": 1,
                            "total_partes": 1,
                        },
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla en la base de datos o en otros módulos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No fue posible generar el reporte",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def reporte_traslados_rechazados(
    fecha_inicio: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD", examples=["2026-01-01"]),
    fecha_fin: str = Query(..., description="Fecha final en formato YYYY-MM-DD", examples=["2026-06-30"]),
    id_sucursal: Optional[int] = Query(default=None, description="ID opcional de sucursal a filtrar"),
    parte: int = Query(default=1, description="Número de parte cuando el rango supera 1 año"),
    id_empresa: int = Depends(obtener_id_empresa_sesion),
):
    """Genera el reporte de solicitudes de traslado rechazadas con su motivo."""
    try:
        datos = service.generar_reporte_traslados_rechazados(
            id_empresa=id_empresa,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_sucursal=id_sucursal,
            parte=parte,
        )
    except ErrorNegocio as e:
        return _manejar_error_reporte(e)

    return respuesta(True, datos, "Reporte de traslados rechazados generado exitosamente")