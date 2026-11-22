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
MENSAJE_CORREO_INVALIDO = "El correo no tiene un formato válido"
MENSAJE_CREDENCIALES_INCORRECTAS = "Credenciales incorrectas"
MENSAJE_ACCESO_INACTIVO = (
    "El acceso no está habilitado: la cuenta, la sucursal o la empresa se encuentra inactiva"
)

PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CLAVE_SECRETA_TOKEN = "gestor-inventario-jwt-secret-key"


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
        estado: str = "activa",
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