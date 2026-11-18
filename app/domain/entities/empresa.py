import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_OBLIGATORIOS = "Los campos nit, nombre, ubicacion y fecha_creacion son obligatorios"
MENSAJE_INMUTABLES = "El NIT y la fecha de creación no pueden modificarse"


# ── HU-01: schema de ENTRADA del registro ─────────────────────
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
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Formato de fecha no válido. Debe ser YYYY-MM-DD")
        return v


# ── HU-02: schema de ENTRADA de la actualización de contacto ──
# Todos los campos son opcionales: solo se modifican los que lleguen.
class EmpresaUpdate(BaseModel):
    telefono: Optional[str] = None
    correo: Optional[str] = None
    ubicacion: Optional[str] = None

    # El NIT y la fecha de creación nunca se modifican
    @model_validator(mode="before")
    @classmethod
    def rechazar_campos_inmutables(cls, valores):
        if isinstance(valores, dict) and ("nit" in valores or "fecha_creacion" in valores):
            raise ValueError(MENSAJE_INMUTABLES)
        return valores

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v):
        if v is not None:
            v = v.strip()
            if not re.fullmatch(r"[0-9]+", v):
                raise ValueError("El teléfono solo debe contener números")
        return v

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v):
        if v is not None:
            v = v.strip()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
                raise ValueError("El correo no tiene un formato válido")
        return v

    @field_validator("ubicacion")
    @classmethod
    def validar_ubicacion(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("La ubicación no puede estar vacía")
            v = v.strip()
        return v

    @model_validator(mode="after")
    def debe_traer_algo(self):
        if self.telefono is None and self.correo is None and self.ubicacion is None:
            raise ValueError("Debe enviar al menos un dato a modificar: telefono, correo o ubicacion")
        return self


# ── Entidad del dominio: guarda los datos y las reglas de negocio ──
class Empresa:
    def __init__(self, id: Optional[int], nit: str, nombre: str, ubicacion: str,
                 fecha_creacion: date, estado: str = "activo",
                 telefono: Optional[str] = None, correo: Optional[str] = None):
        self.id = id
        self.nit = nit
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.fecha_creacion = fecha_creacion
        self.estado = estado
        self.telefono = telefono
        self.correo = correo

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

    # HU-02: solo se cambian los datos de contacto que lleguen.
    # El NIT y la fecha de creación no se tocan.
    def actualizar_contacto(self, telefono: Optional[str], correo: Optional[str],
                            ubicacion: Optional[str]):
        if telefono is not None:
            self.telefono = telefono
        if correo is not None:
            self.correo = correo
        if ubicacion is not None:
            self.ubicacion = ubicacion

    # Respuesta de HU-01 (registro)
    def to_response(self) -> dict:
        return {
            "id_empresa": self.id,
            "nit": self.nit,
            "nombre": self.nombre,
            "ubicacion": self.ubicacion,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "estado": self.estado,
        }

    # Respuesta de HU-02 (consulta)
    def to_detalle(self) -> dict:
        return {
            "id_empresa": self.id,
            "nit": self.nit,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
            "ubicacion": self.ubicacion,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "estado": self.estado,
        }

    # Respuesta de HU-02 (actualización)
    def to_contacto(self) -> dict:
        return {
            "id_empresa": self.id,
            "telefono": self.telefono,
            "correo": self.correo,
            "ubicacion": self.ubicacion,
        }