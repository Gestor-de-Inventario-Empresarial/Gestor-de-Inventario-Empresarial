def _crear_empresa_base(client, nit: str = "900123456-1", nombre: str = "TechStore S.A.S.") -> int:
    resp = client.post(
        "/api/v1/empresas",
        json={
            "nit": nit,
            "nombre": nombre,
            "ubicacion": "Calle 36 # 15-20",
            "fecha_creacion": "2020-05-10",
        },
    )
    data = resp.json()["data"]
    return data.get("id") or data.get("id_empresa")


def _payload_sucursal_create(
    nombre: str = "Sucursal Centro",
    direccion: str = "Calle 36 # 15-20",
    codigo: str = "SUC-001",
) -> dict:
    return {
        "nombre": nombre,
        "direccion": direccion,
        "codigo": codigo,
    }


# ── HU-04: Registrar sucursal ─────────────────────────────────
def test_hu04_registrar_sucursal_exitoso(client):
    id_empresa = _crear_empresa_base(client)

    resp = client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_empresa)},
        json=_payload_sucursal_create(),
    )
    body = resp.json()

    assert resp.status_code == 201
    assert body["success"] is True
    assert body["data"]["nombre"] == "Sucursal Centro"
    assert body["data"]["codigo"] == "SUC-001"


def test_hu04_registrar_sucursal_duplicada_falla(client):
    id_empresa = _crear_empresa_base(client)
    headers = {"X-Empresa-Id": str(id_empresa)}

    client.post("/api/v1/sucursales", headers=headers, json=_payload_sucursal_create())
    resp = client.post("/api/v1/sucursales", headers=headers, json=_payload_sucursal_create())

    assert resp.status_code in (400, 409)
    assert resp.json()["success"] is False


def test_hu05_actualizar_sucursal_inexistente(client):
    id_empresa = _crear_empresa_base(client)
    resp = client.put(
        "/api/v1/sucursales/999",
        headers={"X-Empresa-Id": str(id_empresa)},
        json={
            "nombre": "Sucursal Fantasma",
            "direccion": "Calle 1 # 2-3",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["success"] is False


# ── HU-05: Consultar y gestionar sucursales ───────────────────
def test_hu05_consultar_sucursales_aisladas_por_empresa(client):
    id_emp_1 = _crear_empresa_base(client, nit="900111111-1", nombre="Empresa Uno")
    id_emp_2 = _crear_empresa_base(client, nit="900222222-2", nombre="Empresa Dos")

    client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_emp_1)},
        json=_payload_sucursal_create("Sucursal Centro", "Dir 1", "SUC-01"),
    )
    client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_emp_1)},
        json=_payload_sucursal_create("Sucursal Norte", "Dir 2", "SUC-02"),
    )
    client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_emp_2)},
        json=_payload_sucursal_create("Sucursal Externa", "Dir 3", "SUC-03"),
    )

    resp = client.get("/api/v1/sucursales", headers={"X-Empresa-Id": str(id_emp_1)})
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert len(body["data"]) == 2


def test_hu05_actualizar_sucursal_exitoso(client):
    id_empresa = _crear_empresa_base(client)
    headers = {"X-Empresa-Id": str(id_empresa)}

    creada = client.post(
        "/api/v1/sucursales",
        headers=headers,
        json=_payload_sucursal_create(),
    ).json()["data"]
    id_sucursal = creada.get("id") or creada.get("id_sucursal")

    resp = client.put(
        f"/api/v1/sucursales/{id_sucursal}",
        headers=headers,
        json={
            "nombre": "Sucursal Centro Principal",
            "direccion": "Carrera 27 # 40-10",
        },
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert body["data"]["nombre"] == "Sucursal Centro Principal"