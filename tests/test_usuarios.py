from app.repositories.empresa_repository import empresa_repository


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

    # Activar la empresa en memoria para habilitar el inicio de sesión (HU-11)
    for empresa in empresa_repository._datos:
        if empresa.id == id_empresa:
            empresa.estado = "activa"

    suc = client.post(
        "/api/v1/sucursales",
        headers={"X-Empresa-Id": str(id_empresa)},
        json={"nombre": "Sucursal Centro", "direccion": "Dir 1", "codigo": "SUC-01"},
    ).json()["data"]
    id_sucursal = suc.get("id") or suc.get("id_sucursal")
    return id_empresa, id_sucursal


# ── HU-11: Registrar usuario y login ──────────────────────────
def test_hu11_registrar_usuario_y_login_exitoso(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)

    resp_crear = client.post(
        "/api/v1/usuarios",
        headers={"X-Empresa-Id": str(id_empresa), "X-Rol": "Administrador"},
        json={
            "nombre": "Carlos Gómez",
            "correo": "carlos@techstore.com",
            "contrasena": "ClaveSegura123*",
            "rol": "Administrador",
            "id_sucursal": id_sucursal,
        },
    )
    body_crear = resp_crear.json()
    assert resp_crear.status_code == 201
    assert body_crear["success"] is True

    resp_login = client.post(
        "/api/v1/auth/login",
        json={"correo": "carlos@techstore.com", "contrasena": "ClaveSegura123*"},
    )
    body_login = resp_login.json()
    assert resp_login.status_code == 200
    assert body_login["success"] is True


def test_hu11_login_credenciales_invalidas(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"correo": "noexiste@techstore.com", "contrasena": "ClaveIncorrecta1*"},
    )
    assert resp.status_code in (400, 401, 404)
    assert resp.json()["success"] is False


# ── HU-12 y HU-13: Consultar, actualizar y proteger último admin (RN-09) ──
def test_hu12_y_hu13_gestion_usuarios_y_proteccion_ultimo_admin(client):
    id_empresa, id_sucursal = _preparar_empresa_y_sucursal(client)
    headers = {"X-Empresa-Id": str(id_empresa), "X-Rol": "Administrador"}

    admin = client.post(
        "/api/v1/usuarios",
        headers=headers,
        json={
            "nombre": "Admin Único",
            "correo": "admin@techstore.com",
            "contrasena": "ClaveSegura123*",
            "rol": "Administrador",
            "id_sucursal": id_sucursal,
        },
    ).json()["data"]
    id_admin = admin.get("id") or admin.get("id_usuario")

    empleado = client.post(
        "/api/v1/usuarios",
        headers=headers,
        json={
            "nombre": "Laura Pérez",
            "correo": "laura@techstore.com",
            "contrasena": "ClaveSegura123*",
            "rol": "Usuario",
            "id_sucursal": id_sucursal,
        },
    ).json()["data"]
    id_empleado = empleado.get("id") or empleado.get("id_usuario")

    # Consultar listado
    resp_lista = client.get("/api/v1/usuarios", headers=headers)
    assert resp_lista.status_code == 200
    assert len(resp_lista.json()["data"]) == 2

    # RN-09: No debe permitir inactivar al único Administrador activo
    resp_inactivar_admin = client.patch(
        f"/api/v1/usuarios/{id_admin}/estado",
        headers=headers,
        json={"estado": "inactivo"},
    )
    assert resp_inactivar_admin.status_code in (400, 409)
    assert resp_inactivar_admin.json()["success"] is False

    # Sí debe permitir inactivar al usuario estándar
    resp_inactivar_emp = client.patch(
        f"/api/v1/usuarios/{id_empleado}/estado",
        headers=headers,
        json={"estado": "inactivo"},
    )
    assert resp_inactivar_emp.status_code == 200
    assert resp_inactivar_emp.json()["success"] is True