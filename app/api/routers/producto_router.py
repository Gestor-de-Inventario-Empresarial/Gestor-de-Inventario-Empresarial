from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta
from app.domain.entities.producto import (
    ProductoCreate,
    ProductoRetiroCreate,
    ProductoUpdate,
)
from app.repositories.producto_repository import producto_repository
from app.services.producto_service import ProductoService

from fastapi import APIRouter, Depends
from app.api.routers.suscripcion_router import verificar_suscripcion_activa

router = APIRouter(
    prefix="/api/v1/productos",
    tags=["Productos"],
    dependencies=[Depends(verificar_suscripcion_activa)],
)

service = ProductoService(repo=producto_repository)


def obtener_id_sucursal_sesion(
    x_sucursal_id: int = Header(
        default=1,
        alias="X-Sucursal-Id",
        description="ID de la sucursal activa en sesión (simulado mientras se integra autenticación)",
    )
) -> int:
    return x_sucursal_id


def _manejar_error_producto(error: ErrorNegocio):
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


# POST /api/v1/productos  (HU-06)
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar producto en una sucursal",
    description=(
        "Registra un producto con código, nombre, categoría, precio y cantidad asociándolo a la "
        "sucursal de la sesión activa. Valida que la sucursal esté activa, que el precio sea mayor "
        "a cero, la cantidad no sea negativa (RN-04) y que el código sea único en esa sucursal (RN-05)."
    ),
    responses={
        201: {
            "description": "Producto registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Producto registrado exitosamente",
                        "data": {
                            "id_producto": 1,
                            "id_sucursal": 1,
                            "codigo": "PRD-0001",
                            "nombre": "Cuaderno argollado 100 hojas",
                            "categoria": "Papelería",
                            "precio": 8500,
                            "cantidad": 120,
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Precio, cantidad o campos obligatorios inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El precio debe ser mayor a cero y la cantidad no puede ser negativa",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        403: {
            "description": "Sucursal inactiva",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La sucursal se encuentra inactiva",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Sucursal de la sesión no encontrada",
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
            "description": "Código de producto duplicado en la sucursal",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El código de producto ya existe en esta sucursal",
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
                        "message": "No fue posible procesar la solicitud de producto",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def registrar_producto(
    datos: ProductoCreate,
    id_sucursal: int = Depends(obtener_id_sucursal_sesion),
):
    """Registra un producto en la sucursal de la sesión activa."""
    producto = service.crear(id_sucursal=id_sucursal, datos=datos)
    return respuesta(True, producto, "Producto registrado exitosamente")


# GET /api/v1/productos  (HU-07)
@router.get(
    "",
    summary="Consultar existencias de una sucursal",
    description=(
        "Consulta en modo de solo lectura los productos de la sucursal de la sesión activa, "
        "permitiendo filtrar por nombre o código mediante el parámetro 'busqueda'."
    ),
    responses={
        200: {
            "description": "Consulta de existencias exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Consulta de existencias exitosa",
                        "data": [
                            {
                                "id_producto": 1,
                                "codigo": "PRD-0001",
                                "nombre": "Cuaderno argollado 100 hojas",
                                "cantidad": 120,
                                "precio": 8500,
                            }
                        ],
                        "success": True,
                    }
                }
            },
        },
        404: {
            "description": "Sin productos que coincidan con el criterio",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No se encontraron productos con el criterio indicado",
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
                        "message": "No fue posible procesar la solicitud de existencias",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def consultar_existencias(
    busqueda: Optional[str] = Query(
        default=None,
        description="Nombre o código del producto a buscar dentro de la sucursal",
        examples=["PRD-0001"],
    ),
    id_sucursal: int = Depends(obtener_id_sucursal_sesion),
):
    """Consulta existencias de productos en la sucursal de la sesión."""
    productos = service.consultar_existencias(id_sucursal=id_sucursal, busqueda=busqueda)
    return respuesta(True, productos, "Consulta de existencias exitosa")


# PUT /api/v1/productos/{id_producto}  (HU-06)
@router.put(
    "/{id_producto}",
    summary="Actualizar precio o cantidad de un producto",
    description=(
        "Actualiza el precio y/o la cantidad de un producto perteneciente a la sucursal activa. "
        "El código y la sucursal propietaria no se modifican."
    ),
    responses={
        200: {
            "description": "Producto actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Producto actualizado exitosamente",
                        "data": {
                            "id_producto": 1,
                            "precio": 9000,
                            "cantidad": 150,
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Precio o cantidad inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El precio debe ser mayor a cero y la cantidad no puede ser negativa",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        403: {
            "description": "Sucursal inactiva",
            "content": {
                "application/json": {
                    "example": {
                        "message": "La sucursal se encuentra inactiva",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Producto no encontrado o pertenece a otra sucursal",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Producto no encontrado",
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
                        "message": "No fue posible procesar la solicitud de producto",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def actualizar_producto(
    id_producto: int,
    datos: ProductoUpdate,
    id_sucursal: int = Depends(obtener_id_sucursal_sesion),
):
    """Actualiza precio o cantidad de un producto de la sucursal activa."""
    producto = service.actualizar(
        id_producto=id_producto, id_sucursal=id_sucursal, datos=datos
    )
    return respuesta(True, producto, "Producto actualizado exitosamente")


# POST /api/v1/productos/{id_producto}/retiros  (HU-07)
@router.post(
    "/{id_producto}/retiros",
    summary="Retirar producto del inventario con motivo",
    description=(
        "Retira un producto del inventario de la sucursal activa registrando el motivo "
        "('averia', 'vencimiento' o 'ajuste'). Bloquea el retiro si el producto tiene "
        "traslados pendientes o en curso."
    ),
    responses={
        200: {
            "description": "Producto retirado del inventario exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Producto retirado del inventario exitosamente",
                        "data": {
                            "id_producto": 1,
                            "motivo": "averia",
                            "fecha_retiro": "2026-11-18",
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Motivo ausente o no válido",
            "content": {
                "application/json": {
                    "example": {
                        "message": "El motivo debe ser 'averia', 'vencimiento' o 'ajuste'",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        403: {
            "description": "El producto pertenece a otra sucursal",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No tiene permisos para modificar el inventario de otra sucursal",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "Producto no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Producto no encontrado",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Retiro bloqueado por traslados en curso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No es posible retirar el producto: tiene traslados en curso",
                        "data": {
                            "id_producto": 1,
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
                        "message": "No fue posible procesar la solicitud de existencias",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def retirar_producto(
    id_producto: int,
    datos: ProductoRetiroCreate,
    id_sucursal: int = Depends(obtener_id_sucursal_sesion),
):
    """Retira un producto del inventario registrando el motivo."""
    try:
        retiro = service.retirar_existencias(
            id_producto=id_producto, id_sucursal=id_sucursal, datos=datos
        )
    except ErrorNegocio as e:
        return _manejar_error_producto(e)

    return respuesta(True, retiro, "Producto retirado del inventario exitosamente")