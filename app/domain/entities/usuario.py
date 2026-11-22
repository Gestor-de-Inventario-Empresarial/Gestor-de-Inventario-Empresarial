import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_CAMPOS_OBLIGATORIOS = "El correo y la contraseña son obligatorios"
MENSAJE_NOMBRE_OBLIGATORIO = "El nombre del usuario es obligatorio"
MENSAJE_CORREO_OBLIGATORIO = "El correo electrónico es obligatorio"
MENSAJE_CORREO_INVALIDO = "El correo no tiene un formato válido"
MENSAJE_CONTRASENA_CORTA = "La contraseña debe tener al menos 8 caracteres"
MENSAJE_ROL_INVALIDO = "El rol debe ser 'Administrador' o 'Usuario'"
MENSAJE_CORREO_DUPLICADO = "El correo ya se encuentra registrado"
MENSAJE_SIN_PERMISO_CREAR = "No tiene permisos para crear usuarios"
MENSAJE_SUCURSAL_INACTIVA_USUARIO = (
    "No se pueden crear usuarios en una sucursal inactiva"
)

MENSAJE_CREDENCIALES_INCORRECTAS = "Credenciales incorrectas"
MENSAJE_ACCESO_INACTIVO = (
    "El acceso no está habilitado: la cuenta, la sucursal o la empresa se encuentra inactiva"
)

PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CLAVE_SECRETA_TOKEN = "gestor-inventario-jwt-secret-key"
ROLES_VALIDOS = {"administrador": "Administrador", "usuario": "Usuario"}


class LoginRequest(BaseModel):
    correo: Optional[str] = Field(default=None)
    contrasena: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def validar_campos_login(cls, valores):
        if not isinstance(valores, dict):
            raise ValueError(MENSAJE_CAMPOS_OBLIGATORIOS)

        correo = valores.get("correo")
        contrasena = valores.get("contrasena")

        if (
            correo is None
            or contrasena is None
            or not isinstance(correo, str)
            or not isinstance(contrasena, str)
            or not correo.strip()
            or not contrasena.strip()
        ):
            raise ValueError(MENSAJE_CAMPOS_OBLIGATORIOS)

        correo_limpio = correo.strip().lower()
        if not PATRON_CORREO.match(correo_limpio):
            raise ValueError(MENSAJE_CORREO_INVALIDO)

        valores["correo"] = correo_limpio
        return valores


class UsuarioCreate(BaseModel):
    nombre: Optional[str] = Field(default=None)
    correo: Optional[str] = Field(default=None)
    contrasena: Optional[str] = Field(default=None)
    rol: Optional[str] = Field(default=None)
    id_sucursal: int = Field(...)

    @model_validator(mode="before")
    @classmethod
    def validar_datos_usuario(cls, valores):
        if not isinstance(valores, dict):
            raise ValueError(MENSAJE_NOMBRE_OBLIGATORIO)

        nombre = valores.get("nombre")
        if nombre is None or not isinstance(nombre, str) or not nombre.strip():
            raise ValueError(MENSAJE_NOMBRE_OBLIGATORIO)

        correo = valores.get("correo")
        if correo is None or not isinstance(correo, str) or not correo.strip():
            raise ValueError(MENSAJE_CORREO_OBLIGATORIO)

        correo_limpio = correo.strip().lower()
        if not PATRON_CORREO.match(correo_limpio):
            raise ValueError(MENSAJE_CORREO_INVALIDO)

        contrasena = valores.get("contrasena")
        if (
            contrasena is None
            or not isinstance(contrasena, str)
            or len(contrasena) < 8
        ):
            raise ValueError(MENSAJE_CONTRASENA_CORTA)

        rol = valores.get("rol")
        if rol is None or not isinstance(rol, str) or rol.strip().lower() not in ROLES_VALIDOS:
            raise ValueError(MENSAJE_ROL_INVALIDO)

        valores["nombre"] = nombre.strip()
        valores["correo"] = correo_limpio
        valores["rol"] = ROLES_VALIDOS[rol.strip().lower()]
        return valores


class Usuario:
    def __init__(
        self,
        id: Optional[int],
        id_empresa: int,
        id_sucursal: int,
        nombre: str,
        correo: str,
        password_hash: str,
        rol: str = "Usuario",
        estado: str = "activo",
    ):
        self.id = id
        self.id_empresa = id_empresa
        self.id_sucursal = id_sucursal
        self.nombre = nombre
        self.correo = correo.strip().lower()
        self.password_hash = password_hash
        self.rol = rol
        self.estado = estado

    @staticmethod
    def generar_hash_contrasena(contrasena: str) -> str:
        salt = secrets.token_hex(16)
        derivado = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return f"{salt}${derivado}"

    # RN-08: comparación cifrada contra hash guardado (nunca en texto plano)
    @staticmethod
    def validar_credencial_cifrada(contrasena_plana: str, password_hash: str) -> bool:
        if not contrasena_plana or not password_hash or "$" not in password_hash:
            return False
        salt, hash_esperado = password_hash.split("$", 1)
        derivado = hashlib.pbkdf2_hmac(
            "sha256", contrasena_plana.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return hmac.compare_digest(derivado, hash_esperado)

    # ── Reglas HU-12 en Domain ────────────────────────────────
    @staticmethod
    def validar_permiso_administrador(rol_sesion: str):
        if not isinstance(rol_sesion, str) or rol_sesion.strip().lower() != "administrador":
            raise ErrorNegocio(MENSAJE_SIN_PERMISO_CREAR, 403)

    @staticmethod
    def validar_correo_unico(correo_ya_existe: bool):
        if correo_ya_existe:
            raise ErrorNegocio(MENSAJE_CORREO_DUPLICADO, 409)

    @staticmethod
    def validar_rol_valido(rol: str) -> str:
        if not isinstance(rol, str) or rol.strip().lower() not in ROLES_VALIDOS:
            raise ErrorNegocio(MENSAJE_ROL_INVALIDO, 400)
        return ROLES_VALIDOS[rol.strip().lower()]

    @staticmethod
    def validar_longitud_contrasena(contrasena: str):
        if not isinstance(contrasena, str) or len(contrasena) < 8:
            raise ErrorNegocio(MENSAJE_CONTRASENA_CORTA, 400)

    @staticmethod
    def validar_sucursal_activa_para_usuario(estado_sucursal: str):
        if estado_sucursal.strip().lower() != "activa":
            raise ErrorNegocio(MENSAJE_SUCURSAL_INACTIVA_USUARIO, 409)

    # ── Reglas HU-11 en Domain ────────────────────────────────
    @staticmethod
    def validar_estados_activos(
        estado_usuario: str, estado_sucursal: str, estado_empresa: str
    ):
        usuario_activo = estado_usuario.strip().lower() in ("activa", "activo")
        sucursal_activa = estado_sucursal.strip().lower() == "activa"
        empresa_activa = estado_empresa.strip().lower() == "activa"

        if not (usuario_activo and sucursal_activa and empresa_activa):
            raise ErrorNegocio(MENSAJE_ACCESO_INACTIVO, 403)

    @staticmethod
    def generar_token_acceso(id_usuario: int, rol: str, id_sucursal: int) -> str:
        def _b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        header = _b64url(
            json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
        )
        payload = _b64url(
            json.dumps(
                {
                    "sub": id_usuario,
                    "rol": rol,
                    "id_sucursal": id_sucursal,
                    "exp": int(time.time()) + 28_800,
                },
                separators=(",", ":"),
            ).encode("utf-8")
        )
        mensaje = f"{header}.{payload}".encode("utf-8")
        firma = _b64url(
            hmac.new(
                CLAVE_SECRETA_TOKEN.encode("utf-8"), mensaje, hashlib.sha256
            ).digest()
        )
        return f"{header}.{payload}.{firma}"

    def to_auth_response(self) -> dict:
        return {
            "id_usuario": self.id,
            "nombre": self.nombre,
            "rol": self.rol,
            "id_sucursal": self.id_sucursal,
        }

    def to_response(self) -> dict:
        return {
            "id_usuario": self.id,
            "nombre": self.nombre,
            "correo": self.correo,
            "rol": self.rol,
            "id_sucursal": self.id_sucursal,
            "estado": self.estado,
        }