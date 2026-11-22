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
                estado="activo",
            )
        ]
        self._siguiente_id: int = 2
        self._suscripciones_empresa: dict[int, str] = {1: "activa"}

    def buscar_por_correo(self, correo: str) -> Optional[Usuario]:
        buscado = correo.strip().lower()
        return next((u for u in self._datos if u.correo == buscado), None)

    def buscar_por_id_y_empresa(
        self, id_usuario: int, id_empresa: int
    ) -> Optional[Usuario]:
        return next(
            (
                u
                for u in self._datos
                if u.id == id_usuario and u.id_empresa == id_empresa
            ),
            None,
        )

    def existe_correo(self, correo: str) -> bool:
        return self.buscar_por_correo(correo) is not None

    def listar_por_empresa(
        self,
        id_empresa: int,
        id_sucursal: Optional[int] = None,
        estado: Optional[str] = None,
    ) -> list[Usuario]:
        estado_norm = estado.strip().lower() if estado else None
        return [
            u
            for u in self._datos
            if u.id_empresa == id_empresa
            and (id_sucursal is None or u.id_sucursal == id_sucursal)
            and (estado_norm is None or u.estado.strip().lower() == estado_norm)
        ]

    def contar_administradores_activos(self, id_empresa: int) -> int:
        return sum(
            1
            for u in self._datos
            if u.id_empresa == id_empresa
            and u.rol.strip().lower() == "administrador"
            and u.estado.strip().lower() in ("activo", "activa")
        )

    def crear(self, usuario: Usuario) -> Usuario:
        usuario.id = self._siguiente_id
        self._siguiente_id += 1
        self._datos.append(usuario)
        return usuario

    def actualizar(self, usuario: Usuario) -> Usuario:
        for i, existente in enumerate(self._datos):
            if existente.id == usuario.id:
                self._datos[i] = usuario
                break
        return usuario

    def consultar_sucursal(self, id_sucursal: int) -> Optional[dict]:
        sucursal = next(
            (s for s in sucursal_repository._datos if s.id == id_sucursal),
            None,
        )
        if sucursal is None:
            return None
        return {
            "id_sucursal": sucursal.id,
            "id_empresa": sucursal.id_empresa,
            "nombre": sucursal.nombre,
            "estado": sucursal.estado,
        }

    def obtener_estado_sucursal(self, id_sucursal: int) -> Optional[str]:
        sucursal = self.consultar_sucursal(id_sucursal)
        return sucursal["estado"] if sucursal else None

    def obtener_estado_empresa(self, id_empresa: int) -> Optional[str]:
        empresa = next(
            (e for e in empresa_repository._datos if e.id == id_empresa),
            None,
        )
        return empresa.estado if empresa else None

    def consultar_estado_suscripcion(self, id_empresa: int) -> str:
        return self._suscripciones_empresa.get(id_empresa, "activa")


usuario_repository = UsuarioRepository()