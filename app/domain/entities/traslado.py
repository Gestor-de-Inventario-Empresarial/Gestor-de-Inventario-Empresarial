from typing import Optional

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


class Traslado:
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