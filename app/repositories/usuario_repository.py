from typing import Optional

from app.domain.entities.usuario import Usuario
from app.repositories.empresa_repository import empresa_repository
from app.repositories.sucursal_repository import sucursal_repository


class UsuarioRepository:
    def __init__(self):
        self._datos: list[Usuario] = [
            Usuario(
                id=1,
                id_empresa=1,
                id_sucursal=1,
                nombre="Laura Gómez",
                correo="laura@empresa.com",
                password_hash=Usuario.generar_hash_contrasena("Admin123*"),
                rol="Administrador",
                estado="activa",
            )
        ]
        self._siguiente_id: int = 2
        self._suscripciones_empresa: dict[int, str] = {1: "activa"}

    def buscar_por_correo(self, correo: str) -> Optional[Usuario]:
        buscado = correo.strip().lower()
        return next((u for u in self._datos if u.correo == buscado), None)

    # Punto de enlace con MOD-01 (INT-11: Sucursales.consultarSucursal)
    def obtener_estado_sucursal(self, id_sucursal: int) -> Optional[str]:
        sucursal = next(
            (s for s in sucursal_repository._datos if s.id == id_sucursal),
            None,
        )
        return sucursal.estado if sucursal else None

    # Punto de enlace con MOD-01 (INT-12: Empresas.validarEstado)
    def obtener_estado_empresa(self, id_empresa: int) -> Optional[str]:
        empresa = next(
            (e for e in empresa_repository._datos if e.id == id_empresa),
            None,
        )
        return empresa.estado if empresa else None

    # Punto de enlace con MOD-06 (INT-14: Suscripciones.consultarEstado)
    def consultar_estado_suscripcion(self, id_empresa: int) -> str:
        return self._suscripciones_empresa.get(id_empresa, "activa")


usuario_repository = UsuarioRepository()