from typing import Optional

from app.repositories.sucursal_repository import sucursal_repository


class ReporteRepository:
    """
    Capa de lectura para generación de reportes (MOD-05).
    Consulta únicamente en modo lectura sin alterar datos transaccionales.
    """

    # Punto de enlace con MOD-01 (Sucursales)
    def consultar_sucursales_empresa(self, id_empresa: int) -> list[dict]:
        sucursales = sucursal_repository.listar_por_empresa(id_empresa)
        return [
            {
                "id_sucursal": s.id,
                "id_empresa": s.id_empresa,
                "nombre": s.nombre,
                "estado": s.estado,
            }
            for s in sucursales
        ]

    def buscar_sucursal_por_id(self, id_sucursal: int) -> Optional[dict]:
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

    # Punto de enlace con MOD-02 (Inventario.consultarHistorico)
    def consultar_historico_inventario(self) -> list[dict]:
        # Conectar con inventario_repository cuando se integre MOD-02
        return []

    # Punto de enlace con MOD-03 (Traslados.consultarHistorial)
    def consultar_historial_traslados(self) -> list[dict]:
        # Conectar con traslado_repository cuando se integre MOD-03
        return []


# Instancia única compartida por todo el programa
reporte_repository = ReporteRepository()
