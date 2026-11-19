from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_CAMPOS_OBLIGATORIOS = "Los campos codigo, nombre y categoria son obligatorios"
MENSAJE_PRECIO_CANTIDAD = "El precio debe ser mayor a cero y la cantidad no puede ser negativa"
MENSAJE_CODIGO_DUPLICADO = "El código de producto ya existe en esta sucursal"
MENSAJE_INMUTABLES = "El código y la sucursal propietaria no pueden modificarse"
MENSAJE_SUCURSAL_INACTIVA = "La sucursal se encuentra inactiva"


# ── HU-06: schema de ENTRADA para registrar producto ──────────
class ProductoCreate(BaseModel):
    codigo: str = Field("", validate_default=True, examples=["PRD-0001"])
    nombre: str = Field("", validate_default=True, examples=["Cuaderno argollado 100 hojas"])
    categoria: str = Field("", validate_default=True, examples=["Papelería"])
    precio: int | float = Field(..., examples=[8500])
    cantidad: int = Field(..., examples=[120])

    @field_validator("codigo", "nombre", "categoria", mode="before")
    @classmethod
    def validar_textos_obligatorios(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(MENSAJE_CAMPOS_OBLIGATORIOS)
        return v.strip()

    @model_validator(mode="after")
    def validar_valores_numericos(self):
        if self.precio <= 0 or self.cantidad < 0:
            raise ValueError(MENSAJE_PRECIO_CANTIDAD)
        return self


# ── HU-06: schema de ENTRADA para actualizar precio o cantidad ─
class ProductoUpdate(BaseModel):
    precio: Optional[int | float] = Field(None, examples=[9000])
    cantidad: Optional[int] = Field(None, examples=[150])

    @model_validator(mode="before")
    @classmethod
    def rechazar_campos_inmutables(cls, valores):
        if isinstance(valores, dict) and ("codigo" in valores or "id_sucursal" in valores):
            raise ValueError(MENSAJE_INMUTABLES)
        return valores

    @model_validator(mode="after")
    def validar_datos_actualizacion(self):
        if self.precio is None and self.cantidad is None:
            raise ValueError("Debe enviar al menos un dato a modificar: precio o cantidad")
        if self.precio is not None and self.precio <= 0:
            raise ValueError(MENSAJE_PRECIO_CANTIDAD)
        if self.cantidad is not None and self.cantidad < 0:
            raise ValueError(MENSAJE_PRECIO_CANTIDAD)
        return self


# ── Entidad del dominio: datos y reglas de negocio (RN-04, RN-05) ─
class Producto:
    def __init__(
        self,
        id: Optional[int],
        id_sucursal: int,
        codigo: str,
        nombre: str,
        categoria: str,
        precio: int | float,
        cantidad: int,
    ):
        self.id = id
        self.id_sucursal = id_sucursal
        self.codigo = codigo
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio
        self.cantidad = cantidad

    # RN-04: precio mayor a cero y cantidad no negativa
    @staticmethod
    def validar_precio_y_cantidad(precio: int | float, cantidad: int):
        if precio <= 0 or cantidad < 0:
            raise ErrorNegocio(MENSAJE_PRECIO_CANTIDAD, 400)

    # RN-05: código único dentro de la misma sucursal
    @staticmethod
    def validar_codigo_por_sucursal(codigo_ya_registrado: bool):
        if codigo_ya_registrado:
            raise ErrorNegocio(MENSAJE_CODIGO_DUPLICADO, 409)

    # Validación de sucursal activa (INT-06)
    @staticmethod
    def validar_sucursal_activa(estado_sucursal: str):
        if estado_sucursal.strip().lower() != "activa":
            raise ErrorNegocio(MENSAJE_SUCURSAL_INACTIVA, 403)

    def actualizar_stock_y_precio(
        self, precio: Optional[int | float], cantidad: Optional[int]
    ):
        nuevo_precio = precio if precio is not None else self.precio
        nueva_cantidad = cantidad if cantidad is not None else self.cantidad
        self.validar_precio_y_cantidad(nuevo_precio, nueva_cantidad)
        self.precio = nuevo_precio
        self.cantidad = nueva_cantidad

    def to_response(self) -> dict:
        return {
            "id_producto": self.id,
            "id_sucursal": self.id_sucursal,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "precio": self.precio,
            "cantidad": self.cantidad,
        }

    def to_actualizacion_response(self) -> dict:
        return {
            "id_producto": self.id,
            "precio": self.precio,
            "cantidad": self.cantidad,
        }