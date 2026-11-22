from app.core.exceptions import ErrorNegocio
from app.domain.entities.usuario import (
    MENSAJE_ACCESO_INACTIVO,
    MENSAJE_CREDENCIALES_INCORRECTAS,
    LoginRequest,
    Usuario,
    UsuarioCreate,
)
from app.repositories.usuario_repository import UsuarioRepository

MENSAJE_FALLA_LOGIN = "No fue posible iniciar sesión en este momento"
MENSAJE_FALLA_CREAR_USUARIO = "No fue posible crear el usuario"
MENSAJE_SUCURSAL_NO_ENCONTRADA = "Sucursal no encontrada"


class UsuarioService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    # ── HU-11: iniciar sesión ─────────────────────────────────
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

    # ── HU-12: crear usuario en una sucursal ──────────────────
    def crear_usuario(
        self,
        id_empresa_sesion: int,
        rol_sesion: str,
        datos: UsuarioCreate,
    ) -> dict:
        Usuario.validar_permiso_administrador(rol_sesion)
        rol_normalizado = Usuario.validar_rol_valido(datos.rol or "")
        Usuario.validar_longitud_contrasena(datos.contrasena or "")

        try:
            sucursal = self.repo.consultar_sucursal(datos.id_sucursal)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_CREAR_USUARIO, 503) from e

        if sucursal is None or sucursal["id_empresa"] != id_empresa_sesion:
            raise ErrorNegocio(MENSAJE_SUCURSAL_NO_ENCONTRADA, 404)

        Usuario.validar_sucursal_activa_para_usuario(sucursal["estado"])

        try:
            correo_registrado = self.repo.existe_correo(datos.correo or "")
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_CREAR_USUARIO, 503) from e

        Usuario.validar_correo_unico(correo_registrado)

        password_hash = Usuario.generar_hash_contrasena(datos.contrasena or "")
        nuevo_usuario = Usuario(
            id=None,
            id_empresa=id_empresa_sesion,
            id_sucursal=datos.id_sucursal,
            nombre=(datos.nombre or "").strip(),
            correo=(datos.correo or "").strip().lower(),
            password_hash=password_hash,
            rol=rol_normalizado,
            estado="activo",
        )

        try:
            guardado = self.repo.crear(nuevo_usuario)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_CREAR_USUARIO, 503) from e

        return guardado.to_response()