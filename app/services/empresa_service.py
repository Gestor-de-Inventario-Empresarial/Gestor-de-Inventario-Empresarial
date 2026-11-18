from datetime import date
from typing import Optional

from app.core.exceptions import ErrorNegocio
from app.domain.entities.empresa import (
    Empresa,
    EmpresaCreate,
    EmpresaEstadoUpdate,
    EmpresaUpdate,
)
from app.repositories.empresa_repository import EmpresaRepository

MENSAJE_FALLA = "No fue posible registrar la empresa"
MENSAJE_FALLA_PERFIL = "No fue posible procesar la solicitud de la empresa"
MENSAJE_FALLA_ESTADO = "No fue posible cambiar el estado de la empresa"
MENSAJE_NO_ENCONTRADA = "Empresa no encontrada"


class EmpresaService:
    """Coordina el flujo: aplica las reglas del dominio y llama al repositorio."""

    def __init__(self, repo: EmpresaRepository):
        self.repo = repo

    # ── HU-01: registrar empresa ──────────────────────────────
    def crear(self, datos: EmpresaCreate) -> dict:
        empresa = Empresa(
            id=None,
            nit=datos.nit,
            nombre=datos.nombre,
            ubicacion=datos.ubicacion,
            fecha_creacion=date.fromisoformat(datos.fecha_creacion),
        )

        empresa.validar_antiguedad()  # RN-01

        try:
            nit_registrado = self.repo.existe_nit(empresa.nit)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e
        Empresa.validar_nit_unico(nit_registrado)  # RN-02

        try:
            guardada = self.repo.crear(empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA, 503) from e
        return guardada.to_response()

    # ── HU-02: consultar empresa por NIT o por nombre ─────────
    def buscar(self, nit: Optional[str] = None, nombre: Optional[str] = None) -> dict:
        nit = (nit or "").strip()
        nombre = (nombre or "").strip()
        if not nit and not nombre:
            raise ErrorNegocio("Debe indicar el NIT o el nombre de la empresa", 400)

        try:
            empresa = self.repo.buscar_por_nit(nit) if nit else self.repo.buscar_por_nombre(nombre)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_PERFIL, 503) from e

        if empresa is None:
            raise ErrorNegocio(MENSAJE_NO_ENCONTRADA, 404)
        return empresa.to_detalle()

    # ── HU-02: actualizar datos de contacto ───────────────────
    def actualizar(self, id_empresa: int, datos: EmpresaUpdate) -> dict:
        try:
            empresa = self.repo.buscar_por_id(id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_PERFIL, 503) from e

        if empresa is None:
            raise ErrorNegocio(MENSAJE_NO_ENCONTRADA, 404)

        empresa.actualizar_contacto(datos.telefono, datos.correo, datos.ubicacion)

        try:
            self.repo.actualizar(empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_PERFIL, 503) from e
        return empresa.to_contacto()

    # ── HU-03: activar o inactivar empresa en cascada ─────────
    def cambiar_estado(self, id_empresa: int, datos: EmpresaEstadoUpdate) -> dict:
        try:
            empresa = self.repo.buscar_por_id(id_empresa)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_ESTADO, 503) from e

        if empresa is None:
            raise ErrorNegocio(MENSAJE_NO_ENCONTRADA, 404)

        empresa.validar_cambio_estado(datos.estado)

        # RN-03: antes de inactivar, verificar que no existan traslados en curso
        if datos.estado == "inactivo":
            try:
                traslados_pendientes = self.repo.consultar_traslados_pendientes(id_empresa)
            except Exception as e:
                raise ErrorNegocio(MENSAJE_FALLA_ESTADO, 503) from e
            empresa.validar_sin_traslados_pendientes(traslados_pendientes)

        try:
            sucursales_afectadas = self.repo.actualizar_estado_cascada(empresa.id, datos.estado)
        except Exception as e:
            raise ErrorNegocio(MENSAJE_FALLA_ESTADO, 503) from e

        empresa.cambiar_estado(datos.estado)
        return empresa.to_estado(sucursales_afectadas)