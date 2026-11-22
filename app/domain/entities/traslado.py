from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ErrorNegocio

MENSAJE_NO_AUTENTICADO = "Debe iniciar sesión para realizar la consulta"
MENSAJE_PRODUCTO_OBLIGATORIO = "El parámetro producto es obligatorio"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"
MENSAJE_SUCURSAL_INACTIVA = "La sucursal se encuentra inactiva"
MENSAJE_UNA_SOLA_SUCURSAL = (
    "El módulo de traslados no está habilitado: la empresa solo tiene una sucursal"
)
MENSAJE_SIN_EXISTENCIAS = (
    "No hay existencias del producto en las demás sucursales de la empresa"
)

MENSAJE_CANTIDAD_INVALIDA = "La cantidad debe ser un número entero mayor a cero"
MENSAJE_MISMA_SUCURSAL = "La sucursal de origen debe ser distinta a la solicitante"
MENSAJE_EMPRESA_DISTINTA = "La sucursal de origen debe pertenecer a la misma empresa"
MENSAJE_ORIGEN_INACTIVA = "La sucursal de origen se encuentra inactiva"
MENSAJE_SOLICITANTE_INACTIVA = "La sucursal solicitante se encuentra inactiva"
MENSAJE_STOCK_INSUFICIENTE = (
    "La cantidad solicitada supera el stock disponible en la sucursal de origen"
)
MENSAJE_SIN_PERMISO = "No tiene permisos para radicar traslados"

ROLES_OPERATIVOS_VALIDOS = ("administrador", "usuario")


class TrasladoCreate(BaseModel):
    id_sucursal_origen: int = Field(...)
    id_producto: int = Field(...)
    cantidad: int = Field(...)

    @field_validator("cantidad")
    @classmethod
    def validar_cantidad_positiva(cls, v: int) -> int:
        if isinstance(v, bool) or v <= 0:
            raise ValueError(MENSAJE_CANTIDAD_INVALIDA)
        return v


class Traslado:
    def __init__(
        self,
        id: Optional[int],
        id_sucursal_origen: int,
        id_sucursal_destino: int,
        id_producto: int,
        cantidad: int,
        estado: str = "pendiente",
        fecha_solicitud: str = "",
        motivo_rechazo: Optional[str] = None,
    ):
        self.id = id
        self.id_sucursal_origen = id_sucursal_origen
        self.id_sucursal_destino = id_sucursal_destino
        self.id_producto = id_producto
        self.cantidad = cantidad
        self.estado = estado
        self.fecha_solicitud = fecha_solicitud
        self.motivo_rechazo = motivo_rechazo

    # ── Reglas HU-08 ──────────────────────────────────────────
    @staticmethod
    def validar_sesion_autenticada(token: Optional[str]):
        if token is None or not token.strip():
            raise ErrorNegocio(MENSAJE_NO_AUTENTICADO, 401)

    @staticmethod
    def validar_parametro_producto(producto: Optional[str]) -> str:
        if producto is None or not producto.strip():
            raise ErrorNegocio(MENSAJE_PRODUCTO_OBLIGATORIO, 400)
        return producto.strip()

    @staticmethod
    def validar_sucursal_solicitante_activa(sucursal_solicitante: Optional[dict]):
        if sucursal_solicitante is None:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)
        if sucursal_solicitante["estado"].strip().lower() != "activa":
            raise ErrorNegocio(MENSAJE_SUCURSAL_INACTIVA, 403)

    @staticmethod
    def validar_empresa_multisucursal(sucursales_empresa: list[dict]):
        if len(sucursales_empresa) <= 1:
            raise ErrorNegocio(MENSAJE_UNA_SOLA_SUCURSAL, 409)

    @staticmethod
    def filtrar_y_ordenar_disponibilidad(
        id_sucursal_solicitante: int,
        candidatas_con_stock: list[dict],
        nombre_producto_referencia: str,
    ) -> list[dict]:
        disponibles = [
            {
                "id_sucursal": item["id_sucursal"],
                "nombre": item["nombre_sucursal"],
                "cantidad_disponible": item["cantidad"],
            }
            for item in candidatas_con_stock
            if item["id_sucursal"] != id_sucursal_solicitante
            and item["estado_sucursal"].strip().lower() == "activa"
            and item["cantidad"] > 0
        ]

        disponibles.sort(key=lambda x: x["cantidad_disponible"], reverse=True)

        if not disponibles:
            error = ErrorNegocio(MENSAJE_SIN_EXISTENCIAS, 404)
            error.data = {
                "producto": nombre_producto_referencia,
                "sucursales_disponibles": [],
            }
            raise error

        return disponibles

    # ── Reglas HU-09 (RN-06 y RN-07) ──────────────────────────
    @staticmethod
    def validar_permiso_operativo(rol: str):
        if not isinstance(rol, str) or rol.strip().lower() not in ROLES_OPERATIVOS_VALIDOS:
            raise ErrorNegocio(MENSAJE_SIN_PERMISO, 403)

    @staticmethod
    def validar_sucursales_traslado(
        id_sucursal_origen: int,
        id_sucursal_solicitante: int,
        empresa_origen: int,
        empresa_solicitante: int,
        estado_origen: str,
        estado_solicitante: str,
    ):
        if id_sucursal_origen == id_sucursal_solicitante:
            raise ErrorNegocio(MENSAJE_MISMA_SUCURSAL, 400)

        if empresa_origen != empresa_solicitante:
            raise ErrorNegocio(MENSAJE_EMPRESA_DISTINTA, 409)

        if estado_origen.strip().lower() != "activa":
            raise ErrorNegocio(MENSAJE_ORIGEN_INACTIVA, 409)

        if estado_solicitante.strip().lower() != "activa":
            raise ErrorNegocio(MENSAJE_SOLICITANTE_INACTIVA, 409)

    @staticmethod
    def validar_disponibilidad(cantidad_solicitada: int, cantidad_disponible: int):
        if cantidad_solicitada <= 0:
            raise ErrorNegocio(MENSAJE_CANTIDAD_INVALIDA, 400)

        if cantidad_solicitada > cantidad_disponible:
            error = ErrorNegocio(MENSAJE_STOCK_INSUFICIENTE, 409)
            error.data = {
                "cantidad_solicitada": cantidad_solicitada,
                "cantidad_disponible": cantidad_disponible,
            }
            raise error

    def confirmar_ejecucion(self) -> bool:
        return self.estado == "completado"

    def to_response(self) -> dict:
        return {
            "id_traslado": self.id,
            "id_sucursal_origen": self.id_sucursal_origen,
            "id_sucursal_destino": self.id_sucursal_destino,
            "id_producto": self.id_producto,
            "cantidad": self.cantidad,
            "estado": self.estado,
            "fecha_solicitud": self.fecha_solicitud,
        }