def _payload_empresa_create(
    nit: str = "900123456-1",
    nombre: str = "TechStore S.A.S.",
    ubicacion: str = "Calle 36 # 15-20, Bucaramanga",
    fecha_creacion: str = "2020-05-10",
) -> dict:
    return {
        "nit": nit,
        "nombre": nombre,
        "ubicacion": ubicacion,
        "fecha_creacion": fecha_creacion,
    }


def _payload_empresa_update(
    telefono: str = "3119876543",
    correo: str = "contacto@techstore.com",
    ubicacion: str = "Carrera 27 # 45-10, Bucaramanga",
) -> dict:
    return {
        "telefono": telefono,
        "correo": correo,
        "ubicacion": ubicacion,
    }


# ── HU-01: Registrar empresa ──────────────────────────────────
def test_hu01_registrar_empresa_exitoso(client):
    resp = client.post("/api/v1/empresas", json=_payload_empresa_create())
    body = resp.json()

    assert resp.status_code == 201
    assert body["success"] is True
    assert body["data"]["nombre"] == "TechStore S.A.S."
    assert body["data"]["nit"] == "900123456-1"


def test_hu01_registrar_empresa_duplicada_falla(client):
    client.post("/api/v1/empresas", json=_payload_empresa_create())
    resp = client.post("/api/v1/empresas", json=_payload_empresa_create())
    body = resp.json()

    assert resp.status_code in (400, 409)
    assert body["success"] is False


def test_hu01_registrar_empresa_campos_invalidos(client):
    resp = client.post(
        "/api/v1/empresas",
        json=_payload_empresa_create(nit="", nombre="", ubicacion=""),
    )
    body = resp.json()

    assert resp.status_code == 400
    assert body["success"] is False


# ── HU-02: Consultar empresa ──────────────────────────────────
def test_hu02_consultar_empresa_por_nit_y_nombre(client):
    client.post("/api/v1/empresas", json=_payload_empresa_create())

    resp_nit = client.get("/api/v1/empresas", params={"nit": "900123456-1"})
    body_nit = resp_nit.json()
    assert resp_nit.status_code == 200
    assert body_nit["success"] is True

    data_nit = body_nit["data"]
    if isinstance(data_nit, list):
        assert len(data_nit) == 1
        assert data_nit[0]["nit"] == "900123456-1"
    else:
        assert data_nit["nit"] == "900123456-1"

    resp_nombre = client.get("/api/v1/empresas", params={"nombre": "TechStore S.A.S."})
    assert resp_nombre.status_code == 200
    assert resp_nombre.json()["success"] is True

    resp_no_existe = client.get("/api/v1/empresas", params={"nit": "000000000-0"})
    assert resp_no_existe.status_code == 404
    assert resp_no_existe.json()["success"] is False


def test_hu02_consultar_empresa_sin_filtros_falla(client):
    resp = client.get("/api/v1/empresas")
    assert resp.status_code == 400
    assert resp.json()["success"] is False


# ── HU-03: Actualizar empresa ─────────────────────────────────
def test_hu03_actualizar_empresa_exitoso(client):
    creada = client.post("/api/v1/empresas", json=_payload_empresa_create()).json()["data"]
    id_empresa = creada.get("id") or creada.get("id_empresa")
    assert id_empresa is not None

    resp = client.put(
        f"/api/v1/empresas/{id_empresa}",
        json=_payload_empresa_update(),
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert body["data"]["telefono"] == "3119876543"
    assert body["data"]["correo"] == "contacto@techstore.com"


def test_hu03_actualizar_empresa_inexistente(client):
    resp = client.put("/api/v1/empresas/999", json=_payload_empresa_update())
    body = resp.json()

    assert resp.status_code == 404
    assert body["success"] is False