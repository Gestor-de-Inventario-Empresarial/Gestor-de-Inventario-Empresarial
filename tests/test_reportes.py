from datetime import date
from app.repositories.reporte_repository import reporte_repository


def test_hu14_consultar_reportes_inventario_y_traslados(client, monkeypatch):
    emp = client.post(
        "/api/v1/empresas",
        json={
            "nit": "900123456-1",
            "nombre": "TechStore S.A.S.",
            "ubicacion": "Calle 36 # 15-20",
            "fecha_creacion": "2020-05-10",
        },
    ).json()["data"]
    id_empresa = emp.get("id") or emp.get("id_empresa")
    headers = {"X-Empresa-Id": str(id_empresa)}

    suc = client.post(
        "/api/v1/sucursales",
        headers=headers,
        json={"nombre": "Sucursal Centro", "direccion": "Dir 1", "codigo": "SUC-01"},
    ).json()["data"]
    id_sucursal = suc.get("id") or suc.get("id_sucursal")

    hoy = date.today().isoformat()
    params = {"fecha_inicio": "2026-01-01", "fecha_fin": hoy}

    # Sin registros históricos debe responder 404
    resp_vacio = client.get("/api/v1/reportes/inventario", headers=headers, params=params)
    assert resp_vacio.status_code == 404
    assert resp_vacio.json()["success"] is False

    # Simular registros de lectura para validar consolidación (200)
    monkeypatch.setattr(
        reporte_repository,
        "consultar_historico_inventario",
        lambda: [
            {
                "id_sucursal": id_sucursal,
                "fecha": hoy,
                "codigo": "LAP-001",
                "tipo": "entrada",
                "cantidad": 8,
            }
        ],
    )
    monkeypatch.setattr(
        reporte_repository,
        "consultar_historial_traslados",
        lambda: [
            {
                "id_traslado": 1,
                "id_sucursal_origen": id_sucursal,
                "id_sucursal_destino": 99,
                "sucursal_origen": "Sucursal Centro",
                "sucursal_destino": "Sucursal Norte",
                "producto": "Portátil Empresarial",
                "cantidad": 2,
                "estado": "aceptado",
                "fecha": hoy,
            },
            {
                "id_traslado": 2,
                "id_sucursal_origen": id_sucursal,
                "id_sucursal_destino": 99,
                "sucursal_origen": "Sucursal Centro",
                "sucursal_destino": "Sucursal Norte",
                "producto": "Portátil Empresarial",
                "cantidad": 1,
                "estado": "rechazado",
                "motivo_rechazo": "Stock reservado",
                "fecha": hoy,
            },
        ],
    )

    for ruta in (
        "/api/v1/reportes/inventario",
        "/api/v1/reportes/traslados",
        "/api/v1/reportes/traslados-rechazados",
    ):
        resp = client.get(ruta, headers=headers, params=params)
        assert resp.status_code == 200
        assert resp.json()["success"] is True


def test_hu14_reporte_rango_fechas_invalido(client):
    resp = client.get(
        "/api/v1/reportes/inventario",
        headers={"X-Empresa-Id": "1"},
        params={"fecha_inicio": "2026-12-31", "fecha_fin": "2026-01-01"},
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False