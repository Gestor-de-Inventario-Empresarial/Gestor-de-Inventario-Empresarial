from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_NOMBRE_OBLIGATORIO = "El nombre de la sucursal es obligatorio"
MENSAJE_DIRECCION_OBLIGATORIA = "La dirección es obligatoria"
MENSAJE_CODIGO_OBLIGATORIO = "El código de la sucursal es obligatorio"
MENSAJE_CODIGO_DUPLICADO = "El código de sucursal ya existe para esta empresa"
MENSAJE_INMUTABLES = "El código y la empresa propietaria no pueden modificarse"


# ── HU-04: schema de ENTRADA del registro de sucursal ─────────
class SucursalCreate(BaseModel):
    nombre: str = Field("", validate_default=True, examples=["Sucursal Centro"])
    direccion: str = Field("", validate_default=True, examples=["Calle 35 # 15-20, Bucaramanga"])
    codigo: str = Field("", validate_default=True, examples=["SUC-001"])

    @field_validator("direccion", mode="before")
    @classmethod
    def validar_direccion(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(MENSAJE_DIRECCION_OBLIGATORIA)
        return v.strip()

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(MENSAJE_NOMBRE_OBLIGATORIO)
        return v.strip()

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(MENSAJE_CODIGO_OBLIGATORIO)
        return v.strip()


# ── HU-04: schema de ENTRADA de actualización de sucursal ─────
class SucursalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, examples=["Sucursal Centro Principal"])
    direccion: Optional[str] = Field(None, examples=["Carrera 27 # 36-14, Bucaramanga"])

    @model_validator(mode="before")
    @classmethod
    def rechazar_campos_inmutables(cls, valores):
        if isinstance(valores, dict) and ("codigo" in valores or "id_empresa" in valores):
            raise ValueError(MENSAJE_INMUTABLES)
        return valores

    @field_validator("direccion", mode="before")
    @classmethod
    def validar_direccion(cls, v):
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError(MENSAJE_DIRECCION_OBLIGATORIA)
            return v.strip()
        return v

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v):
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError(MENSAJE_NOMBRE_OBLIGATORIO)
            return v.strip()
        return v

    @model_validator(mode="after")
    def debe_traer_algo(self):
        if self.nombre is None and self.direccion is None:
            raise ValueError("Debe enviar al menos un dato a modificar: nombre o direccion")
        return self


# ── Entidad del dominio: guarda los datos y reglas de negocio ──
class Sucursal:
    def __init__(
        self,
        id: Optional[int],
        id_empresa: int,
        nombre: str,
        direccion: str,
        codigo: str,
        estado: str = "activa",
    ):
        self.id = id
        self.id_empresa = id_empresa
        self.nombre = nombre
        self.direccion = direccion
        self.codigo = codigo
        self.estado = estado

    # RN (HU-04): el código debe ser único dentro de la misma empresa
    @staticmethod
    def validar_codigo_unico(codigo_ya_registrado: bool):
        if codigo_ya_registrado:
            raise ErrorNegocio(MENSAJE_CODIGO_DUPLICADO, 409)

    # HU-04: actualizar nombre y dirección sin modificar código ni empresa
    def actualizar_datos(self, nombre: Optional[str], direccion: Optional[str]):
        if nombre is not None:
            self.nombre = nombre
        if direccion is not None:
            self.direccion = direccion

    # Respuesta detallada de HU-04 (registro y actualización)
    def to_response(self) -> dict:
        return {
            "id_sucursal": self.id,
            "id_empresa": self.id_empresa,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "codigo": self.codigo,
            "estado": self.estado,
        }

    # Respuesta resumida de HU-04 (listado)
    def to_resumen(self) -> dict:
        return {
            "id_sucursal": self.id,
            "nombre": self.nombre,
            "codigo": self.codigo,
            "estado": self.estado,
        }