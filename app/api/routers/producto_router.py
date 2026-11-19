from fastapi import APIRouter, Depends, Header, status

from app.core.responses import respuesta
from app.domain.entities.producto import ProductoCreate, ProductoUpdate
from app.repositories.producto_repository import producto_repository
from app.services.producto_service import ProductoService

router = APIRouter(prefix="/api/v1/productos", tags=["Inventario"])

service = ProductoService(repo=producto_repository)


def obtener_id_sucursal_sesion(
    x_sucursal_id: int = Header(
        default=1,
        alias="X-Sucursal-Id",
        description="ID de la sucursal activa en sesión (simulado mientras se integra autenticación)",
    )
) -> int:
    return x_sucursal_id


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