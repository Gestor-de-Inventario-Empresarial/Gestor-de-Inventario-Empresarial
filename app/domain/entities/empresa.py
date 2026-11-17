import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_OBLIGATORIOS = "Los campos nit, nombre, ubicacion y fecha_creacion son obligatorios"


# Schema de ENTRADA: lo que envía el cliente en el POST.
# Si un campo no llega, se trata como vacío y se rechaza con el mensaje de la HU.
class EmpresaCreate(BaseModel):
    nit: str = Field("", validate_default=True)
    nombre: str = Field("", validate_default=True)
    ubicacion: str = Field("", validate_default=True)
    fecha_creacion: str = Field("", validate_default=True)

    @field_validator("nit", "nombre", "ubicacion", "fecha_creacion")
    @classmethod
    def no_vacio(cls, v):
        if not v.strip():
            raise ValueError(MENSAJE_OBLIGATORIOS)
        return v.strip()

    @field_validator("fecha_creacion")
    @classmethod
    def formato_fecha(cls, v):
        mensaje = "Formato de fecha no válido. Debe ser YYYY-MM-DD"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError(mensaje)
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(mensaje)
        return v


# Entidad del dominio: guarda los datos y las reglas de negocio
class Empresa:
    def __init__(self, id: Optional[int], nit: str, nombre: str, ubicacion: str,
                 fecha_creacion: date, estado: str = "activo"):
        self.id = id
        self.nit = nit
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.fecha_creacion = fecha_creacion
        self.estado = estado

    # RN-01: la empresa debe tener mínimo 2 años de creada
    def validar_antiguedad(self, hoy: Optional[date] = None):
        hoy = hoy or date.today()
        try:
            limite = hoy.replace(year=hoy.year - 2)
        except ValueError:  # 29 de febrero
            limite = hoy.replace(year=hoy.year - 2, day=28)
        if self.fecha_creacion > limite:
            raise ErrorNegocio(
                "La empresa no cumple la antigüedad mínima de 2 años para registrarse", 400
            )

    # RN-02: el NIT no puede estar registrado. El servicio consulta al
    # repositorio y le pasa el resultado; el dominio solo decide.
    @staticmethod
    def validar_nit_unico(nit_ya_registrado: bool):
        if nit_ya_registrado:
            raise ErrorNegocio("El NIT ya se encuentra registrado en el sistema", 409)

    def to_response(self) -> dict:
        return {
            "id_empresa": self.id,
            "nit": self.nit,
            "nombre": self.nombre,
            "ubicacion": self.ubicacion,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "estado": self.estado,
        }