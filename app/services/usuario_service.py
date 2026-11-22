from app.core.exceptions import ErrorNegocio
from app.domain.entities.usuario import (
    MENSAJE_ACCESO_INACTIVO,
    MENSAJE_CREDENCIALES_INCORRECTAS,
    LoginRequest,
    Usuario,
)
from app.repositories.usuario_repository import UsuarioRepository

MENSAJE_FALLA_LOGIN = "No fue posible iniciar sesión en este momento"


class UsuarioService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def iniciar_sesion(self, datos: LoginRequest) -> dict:
        try:
            usuario = self.repo.buscar_por_correo(datos.correo or "")
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_LOGIN, 503) from e

        if usuario is None or not Usuario.validar_credencial_cifrada(
            datos.contrasena or "", usuario.password_hash
        ):
            raise ErrorNegocio(MENSAJE_CREDENCIALES_INCORRECTAS, 401)

        try:
            estado_sucursal = self.repo.obtener_estado_sucursal(usuario.id_sucursal)
            estado_empresa = self.repo.obtener_estado_empresa(usuario.id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_LOGIN, 503) from e

        if estado_sucursal is None or estado_empresa is None:
            raise ErrorNegocio(MENSAJE_ACCESO_INACTIVO, 403)

        Usuario.validar_estados_activos(
            estado_usuario=usuario.estado,
            estado_sucursal=estado_sucursal,
            estado_empresa=estado_empresa,
        )

        try:
            estado_suscripcion = self.repo.consultar_estado_suscripcion(
                usuario.id_empresa
            )
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_LOGIN, 503) from e

        token = Usuario.generar_token_acceso(
            id_usuario=usuario.id,
            rol=usuario.rol,
            id_sucursal=usuario.id_sucursal,
        )

        return {
            "token": token,
            "usuario": usuario.to_auth_response(),
            "suscripcion": estado_suscripcion,
        }