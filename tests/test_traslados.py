def _preparar_escenario_traslados(client) -> tuple[int, int, int, int]:
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

    suc_origen = client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_empresa)},
        json={"nombre": "Sucursal Origen", "direccion": "Dir 1", "codigo": "SUC-01"},
    ).json()["data"]
    id_origen = suc_origen.get("id") or suc_origen.get("id_sucursal")

    suc_destino = client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_empresa)},
        json={"nombre": "Sucursal Destino", "direccion": "Dir 2", "codigo": "SUC-02"},
    ).json()["data"]
    id_destino = suc_destino.get("id") or suc_destino.get("id_sucursal")

    prod = client.post(
        "/api/v1/productos",
        headers={"X-Empresa-Id": str(id_empresa), "X-Sucursal-Id": str(id_origen)},
        json={
            "codigo": "MON-001",
            "nombre": "Monitor 27 Pulgadas",
            "categoria": "Monitores",
            "precio": 950000,
            "cantidad": 10,
        },
    ).json()["data"]
    id_producto = prod.get("id") or prod.get("id_producto")

    return id_empresa, id_origen, id_destino, id_producto


# ── HU-08: Consultar disponibilidad en otras sucursales ────────
def test_hu08_consultar_disponibilidad_traslado(client):
    id_empresa, _, id_destino, _ = _preparar_escenario_traslados(client)

    resp = client.get(
        "/api/v1/traslados/disponibilidad",
        headers={
            "X-Empresa-Id": str(id_empresa),
            "X-Sucursal-Id": str(id_destino),
            "Authorization": "Bearer token-prueba",
        },
        params={"producto": "Monitor"},
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert len(body["data"]) >= 1


# ── HU-09 y HU-10: Solicitar, aceptar y rechazar traslados ────
def test_hu09_y_hu10_solicitar_y_aceptar_traslado(client):
    id_empresa, id_origen, id_destino, id_producto = _preparar_escenario_traslados(client)

    # Sucursal destino solicita 4 unidades a sucursal origen
    resp_crear = client.post(
        "/api/v1/traslados",
        headers={
            "X-Empresa-Id": str(id_empresa),
            "X-Sucursal-Id": str(id_destino),
            "X-Rol": "Administrador",
        },
        json={
            "id_sucursal_origen": id_origen,
            "id_producto": id_producto,
            "cantidad": 4,
        },
    )
    body_crear = resp_crear.json()
    assert resp_crear.status_code == 201
    assert body_crear["success"] is True
    id_traslado = body_crear["data"].get("id") or body_crear["data"].get("id_traslado")

    # Sucursal origen acepta el traslado
    resp_aceptar = client.patch(
        f"/api/v1/traslados/{id_traslado}/aceptar",
        headers={
            "X-Empresa-Id": str(id_empresa),
            "X-Sucursal-Id": str(id_origen),
        },
    )
    assert resp_aceptar.status_code == 200
    assert resp_aceptar.json()["success"] is True


def test_hu10_rechazar_traslado_con_motivo(client):
    id_empresa, id_origen, id_destino, id_producto = _preparar_escenario_traslados(client)

    creado = client.post(
        "/api/v1/traslados",
        headers={
            "X-Empresa-Id": str(id_empresa),
            "X-Sucursal-Id": str(id_destino),
            "X-Rol": "Administrador",
        },
        json={
            "id_sucursal_origen": id_origen,
            "id_producto": id_producto,
            "cantidad": 2,
        },
    ).json()["data"]
    id_traslado = creado.get("id") or creado.get("id_traslado")

    resp_rechazar = client.patch(
        f"/api/v1/traslados/{id_traslado}/rechazar",
        headers={
            "X-Empresa-Id": str(id_empresa),
            "X-Sucursal-Id": str(id_origen),
        },
        json={"motivo": "Stock reservado para pedido corporativo"},
    )
    assert resp_rechazar.status_code == 200
    assert resp_rechazar.json()["success"] is True