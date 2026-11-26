import hashlib
import hmac
import pytest


def _crear_empresa(client, nit: str, nombre: str) -> int:
    resp = client.post(
        "/api/v1/empresas",
        json={
            "nit": nit,
            "nombre": nombre,
            "ubicacion": "Bucaramanga",
            "fecha_creacion": "2020-05-10",
        },
    )
    data = resp.json()["data"]
    return data.get("id") or data.get("id_empresa")


def _firmar_wompi(referencia: str, status: str) -> str:
    return hmac.new(
        b"wompi-events-secret",
        f"{referencia}:{status}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# ── HU-15: Consultar estado de suscripción (ya integrada) ─────
def test_hu15_consultar_estado_suscripcion(client):
    id_emp_activa = _crear_empresa(client, "900111111-1", "Empresa Activa")
    id_emp_sin_pago = _crear_empresa(client, "900222222-2", "Empresa Sin Pago")

    resp_activa = client.get(
        "/api/v1/suscripciones/estado",
        headers={"X-Empresa-Id": str(id_emp_activa), "Authorization": "Bearer token"},
    )
    assert resp_activa.status_code == 200
    assert resp_activa.json()["data"]["estado"] == "activa"

    resp_vencida = client.get(
        "/api/v1/suscripciones/estado",
        headers={"X-Empresa-Id": str(id_emp_sin_pago), "Authorization": "Bearer token"},
    )
    assert resp_vencida.status_code == 200
    assert resp_vencida.json()["data"]["estado"] != "activa"


# ── HU-16, HU-17 y HU-18: Pendientes de integración ────────────
@pytest.mark.skip(reason="Pendiente de desarrollo e integración de HU-16, HU-17 y HU-18")
def test_hu16_hu17_hu18_flujo_completo_pagos(client):
    _crear_empresa(client, "900111111-1", "Empresa Base")
    id_empresa = _crear_empresa(client, "900333333-3", "Empresa Nueva")
    headers_admin = {"X-Empresa-Id": str(id_empresa), "X-Rol": "Administrador"}

    # HU-16: Pago pendiente (202)
    resp_pendiente = client.post(
        "/api/v1/pagos",
        headers=headers_admin,
        json={"id_plan": 1, "token_pago": "tok_pendiente"},
    )
    assert resp_pendiente.status_code == 202
    referencia = resp_pendiente.json()["data"]["referencia"]

    # HU-17: Webhook firma inválida (401)
    payload_webhook = {
        "event": "transaction.updated",
        "data": {"transaction": {"reference": referencia, "status": "APPROVED"}},
    }
    resp_firma_mala = client.post(
        "/api/v1/webhooks/wompi",
        headers={"X-Wompi-Signature": "firma-invalida"},
        json=payload_webhook,
    )
    assert resp_firma_mala.status_code == 401

    # HU-17: Webhook válido aprueba y renueva suscripción (200)
    firma = _firmar_wompi(referencia, "APPROVED")
    resp_webhook = client.post(
        "/api/v1/webhooks/wompi",
        headers={"X-Wompi-Signature": firma},
        json=payload_webhook,
    )
    assert resp_webhook.status_code == 200
    assert resp_webhook.json()["data"]["estado"] == "aprobada"

    # HU-17: Evento repetido es idempotente (200)
    resp_repetido = client.post(
        "/api/v1/webhooks/wompi",
        headers={"X-Wompi-Signature": firma},
        json=payload_webhook,
    )
    assert resp_repetido.status_code == 200
    assert "anteriormente" in resp_repetido.json()["message"].lower()

    # HU-15: Verificar que la suscripción quedó activa tras el webhook
    resp_estado = client.get(
        
        "/api/v1/suscripciones/estado",
        headers={"X-Empresa-Id": str(id_empresa), "Authorization": "Bearer token"},
    )
    assert resp_estado.json()["data"]["estado"] == "activa"

    # HU-18: Consultar historial de pagos (200)
    resp_historial = client.get("/api/v1/pagos", headers=headers_admin)
    body_hist = resp_historial.json()
    assert resp_historial.status_code == 200
    assert body_hist["success"] is True
    assert body_hist["data"]["total_registros"] == 1