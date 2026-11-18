from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.sucursal import Sucursal, SucursalCreate, SucursalUpdate
from app.repositories.sucursal_repository import SucursalRepository

MENSAJE_FALLA = "No fue posible procesar la solicitud de sucursal"
MENSAJE_NO_ENCONTRADA = "Sucursal no encontrada"


class SucursalService:
    """Coordina el flujo de sucursales: aplica reglas del dominio y llama al repositorio."""

    def __init__(self, repo: SucursalRepository):
        self.repo = repo

    # ── HU-04: registrar sucursal ─────────────────────────────
    def crear(self, id_empresa: int, datos: SucursalCreate) -> dict:
        try:
            codigo_registrado = self.repo.existe_codigo_en_empresa(id_empresa, datos.codigo)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        Sucursal.validar_codigo_unico(codigo_registrado)

        sucursal = Sucursal(
            id=None,
            id_empresa=id_empresa,
            nombre=datos.nombre,
            direccion=datos.direccion,
            codigo=datos.codigo,
            estado="activa",
        )

        try:
            guardada = self.repo.crear(sucursal)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return guardada.to_response()

    # ── HU-04: consultar sucursales de la empresa ─────────────
    def listar(self, id_empresa: int, estado: Optional[str] = None) -> list[dict]:
        if estado is not None and estado.strip():
            valor_estado = estado.strip().lower()
            if valor_estado not in ("activa", "inactiva"):
                raise ErrorNegocio("El estado debe ser 'activa' o 'inactiva'", 400)

        try:
            sucursales = self.repo.listar_por_empresa(id_empresa, estado=estado)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return [s.to_resumen() for s in sucursales]

    # ── HU-04: actualizar nombre y dirección de sucursal ──────
    def actualizar(self, id_sucursal: int, id_empresa: int, datos: SucursalUpdate) -> dict:
        try:
            sucursal = self.repo.buscar_por_id_y_empresa(id_sucursal, id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        if sucursal is None:
            raise ErrorNegocio(MENSAJE_NO_ENCONTRADA, 404)

        sucursal.actualizar_datos(datos.nombre, datos.direccion)

        try:
            actualizada = self.repo.actualizar(sucursal)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e

        return actualizada.to_response()