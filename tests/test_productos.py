def _preparar_empresa_y_sucursal(client) -> tuple[int, int]:
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

    suc = client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_empresa)},
        json={
            "nombre": "Sucursal Centro",
            "direccion": "Calle 36 # 15-20",
            "codigo": "SUC-001",
        },
    ).json()["data"]
    id_sucursal = suc.get("id") or suc.get("id_sucursal")
    return id_empresa, id_sucursal


def _payload_producto(
    codigo: str = "PROD-001",
    nombre: str = "Teclado Mecánico RGB",
    categoria: str = "Periféricos",
    precio: float = 250000,
    cantidad: int = 15,
) -> dict:
    return {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "cantidad": cantidad,
    }


# ── HU-06: Registrar y consultar productos ────────────────────
def test_hu06_registrar_y_consultar_productos(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)
    headers = {
        "X-Empresa-Id": str(id_empresa),
        "X-Sucursal-Id": str(id_sucursal),
    }

    resp_crear = client.post("/api/v1/productos", headers=headers, json=_payload_producto())
    body_crear = resp_crear.json()

    assert resp_crear.status_code == 201
    assert body_crear["success"] is True
    assert body_crear["data"]["codigo"] == "PROD-001"
    assert body_crear["data"]["cantidad"] == 15

    resp_lista = client.get("/api/v1/productos", headers=headers)
    assert resp_lista.status_code == 200
    assert resp_lista.json()["success"] is True
    assert len(resp_lista.json()["data"]) == 1

    resp_busqueda = client.get(
        "/api/v1/productos",
        headers=headers,
        params={"busqueda": "Teclado"},
    )
    assert resp_busqueda.status_code == 200
    assert len(resp_busqueda.json()["data"]) == 1


def test_hu06_registrar_producto_duplicado_falla(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)
    headers = {
        "X-Empresa-Id": str(id_empresa),
        "X-Sucursal-Id": str(id_sucursal),
    }

    client.post("/api/v1/productos", headers=headers, json=_payload_producto())
    resp = client.post("/api/v1/productos", headers=headers, json=_payload_producto())

    assert resp.status_code in (400, 409)
    assert resp.json()["success"] is False


# ── HU-07: Actualizar y retirar producto ──────────────────────
def test_hu07_actualizar_producto_exitoso(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)
    headers = {
        "X-Empresa-Id": str(id_empresa),
        "X-Sucursal-Id": str(id_sucursal),
    }

    creado = client.post("/api/v1/productos", headers=headers, json=_payload_producto()).json()["data"]
    id_producto = creado.get("id") or creado.get("id_producto")

    resp = client.put(
        f"/api/v1/productos/{id_producto}",
        headers=headers,
        json={"precio": 275000, "cantidad": 20},
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert body["data"]["cantidad"] == 20


def test_hu07_retirar_producto_motivo_invalido_y_exitoso(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)
    headers = {
        "X-Empresa-Id": str(id_empresa),
        "X-Sucursal-Id": str(id_sucursal),
    }

    creado = client.post("/api/v1/productos", headers=headers, json=_payload_producto()).json()["data"]
    id_producto = creado.get("id") or creado.get("id_producto")

    # Motivo distinto a ('averia', 'vencimiento', 'ajuste') debe fallar con 400
    resp_invalido = client.post(
        f"/api/v1/productos/{id_producto}/retiros",
        headers=headers,
        json={"motivo": "descontinuado"},
    )
    assert resp_invalido.status_code == 400
    assert resp_invalido.json()["success"] is False

    # Motivo válido ('averia') retira existencias correctamente
    resp_valido = client.post(
        f"/api/v1/productos/{id_producto}/retiros",
        headers=headers,
        json={"motivo": "averia"},
    )
    assert resp_valido.status_code == 200
    assert resp_valido.json()["success"] is True