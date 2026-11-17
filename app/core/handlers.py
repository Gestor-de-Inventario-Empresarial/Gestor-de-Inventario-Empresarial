from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import ErrorNegocio
from app.core.responses import respuesta


def registrar_manejadores(app):
    """Convierte cualquier error en la respuesta estándar (success, data, message)."""

    @app.exception_handler(ErrorNegocio)
    async def manejar_error_negocio(request: Request, exc: ErrorNegocio):
        return JSONResponse(
            status_code=exc.codigo_http,
            content=respuesta(False, exc.data, exc.mensaje),
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion(request: Request, exc: RequestValidationError):
        error = exc.errors()[0]
        prefijo = "Value error, "
        if error["msg"].startswith(prefijo):
            mensaje = error["msg"][len(prefijo):]
        else:
            campo = str(error["loc"][-1])
            mensaje = f"Dato no válido en '{campo}': {error['msg']}"
        return JSONResponse(status_code=400, content=respuesta(False, None, mensaje))

    @app.exception_handler(Exception)
    async def manejar_error_inesperado(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=respuesta(False, None, "Error interno del servidor"),
        )