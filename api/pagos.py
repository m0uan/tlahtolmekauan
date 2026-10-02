from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, request

from .comunes import respuesta_json
from .acceso_web import activate_paid_access, connect as access_connect, current_client_id, init_db as init_access_db

MP_API_BASE = "https://api.mercadopago.com"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

PLANES: dict[str, dict[str, Any]] = {
    "7_days": {
        "titulo": "Acceso tlahtolmekauan — 7 días",
        "precio": 99.00,
        "dias": 7,
    },
    "30_days": {
        "titulo": "Acceso tlahtolmekauan — 30 días",
        "precio": 199.00,
        "dias": 30,
    },
    "90_days": {
        "titulo": "Acceso tlahtolmekauan — 90 días",
        "precio": 399.00,
        "dias": 90,
    },
    "365_days": {
        "titulo": "Acceso tlahtolmekauan — 1 año",
        "precio": 999.00,
        "dias": 365,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _data_dir() -> Path:
    configured = os.getenv("PAYMENT_DATA_DIR", "").strip()
    if configured:
        path = Path(configured)
    elif Path("/data").is_dir():
        path = Path("/data") / "pagos"
    else:
        path = Path(__file__).resolve().parent.parent / "data" / "pagos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _db_path() -> Path:
    return _data_dir() / "mercado_pago.sqlite3"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_db_path(), timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _init_db() -> None:
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'MXN',
                status TEXT NOT NULL,
                preference_id TEXT,
                payment_id TEXT UNIQUE,
                payment_status TEXT,
                payment_status_detail TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                approved_at TEXT,
                client_id TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_orders_email
            ON orders(email);

            CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status);
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")}
        if "client_id" not in columns:
            db.execute("ALTER TABLE orders ADD COLUMN client_id TEXT")


def _mp_token() -> str:
    token = os.getenv("MP_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("MP_ACCESS_TOKEN no está configurado en Railway.")
    return token


def _site_url() -> str:
    return os.getenv("SITE_URL", "https://speak-nahuatl.com").strip().rstrip("/")


def _mp_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_mp_token()}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }


def _parse_signature(header: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in header.split(","):
        key, separator, value = part.strip().partition("=")
        if separator:
            values[key] = value
    return values


def _valid_webhook_signature(data_id: str) -> bool:
    secret = os.getenv("MP_WEBHOOK_SECRET", "").strip()
    signature_header = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")

    if not secret or not signature_header or not request_id or not data_id:
        return False

    signature = _parse_signature(signature_header)
    timestamp = signature.get("ts", "")
    received_hash = signature.get("v1", "")
    if not timestamp or not received_hash:
        return False

    manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
    expected_hash = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received_hash, expected_hash)


def _get_payment(payment_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{MP_API_BASE}/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {_mp_token()}"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Mercado Pago devolvió una respuesta inválida.")
    return payload


def registrar_rutas_pagos(app: Flask) -> None:
    _init_db()
    init_access_db()

    @app.post("/api/pagos/crear-preferencia")
    def crear_preferencia():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return respuesta_json({"ok": False, "error": "Solicitud inválida."}, 400)

        plan_id = str(data.get("plan", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        plan = PLANES.get(plan_id)

        if plan is None:
            return respuesta_json({"ok": False, "error": "El plan seleccionado no existe."}, 400)
        if len(email) > 254 or not EMAIL_RE.fullmatch(email):
            return respuesta_json({
                "ok": False,
                "error": "Escribe un correo electrónico válido para identificar tu compra.",
            }, 400)

        order_id = str(uuid.uuid4())
        client_id = current_client_id()
        access_token = secrets.token_urlsafe(32)
        amount_cents = int(round(float(plan["precio"]) * 100))
        now = _utc_now()

        with _connect() as db:
            db.execute(
                """
                INSERT INTO orders (
                    order_id, access_token, email, plan_id, amount_cents,
                    status, created_at, updated_at, client_id
                ) VALUES (?, ?, ?, ?, ?, 'created', ?, ?, ?)
                """,
                (order_id, access_token, email, plan_id, amount_cents, now, now, client_id),
            )

        site_url = _site_url()
        return_url = f"{site_url}/?orden={order_id}&token={access_token}"
        preference = {
            "items": [{
                "id": plan_id,
                "title": plan["titulo"],
                "description": "Acceso al traductor tlahtolmekauan",
                "quantity": 1,
                "currency_id": "MXN",
                "unit_price": float(plan["precio"]),
            }],
            "payer": {"email": email},
            "external_reference": order_id,
            "metadata": {"order_id": order_id, "plan_id": plan_id},
            "back_urls": {
                "success": f"{return_url}&resultado=aprobado",
                "pending": f"{return_url}&resultado=pendiente",
                "failure": f"{return_url}&resultado=fallido",
            },
            "auto_return": "approved",
            "notification_url": f"{site_url}/api/pagos/webhook",
            "statement_descriptor": "TLAHTOLMEKAUAN",
        }

        try:
            response = requests.post(
                f"{MP_API_BASE}/checkout/preferences",
                headers=_mp_headers(),
                json=preference,
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            app.logger.exception("No fue posible crear la preferencia de Mercado Pago.")
            with _connect() as db:
                db.execute(
                    "UPDATE orders SET status='preference_error', updated_at=? WHERE order_id=?",
                    (_utc_now(), order_id),
                )
            return respuesta_json({
                "ok": False,
                "error": "Mercado Pago no pudo iniciar el cobro.",
                "detalle": str(exc) if app.debug else None,
            }, 502)

        preference_id = str(result.get("id", ""))
        checkout_url = result.get("init_point") or result.get("sandbox_init_point")
        if not preference_id or not checkout_url:
            return respuesta_json({
                "ok": False,
                "error": "Mercado Pago no devolvió un enlace de cobro.",
            }, 502)

        with _connect() as db:
            db.execute(
                """
                UPDATE orders
                SET preference_id=?, status='preference_created', updated_at=?
                WHERE order_id=?
                """,
                (preference_id, _utc_now(), order_id),
            )

        return respuesta_json({
            "ok": True,
            "order_id": order_id,
            "order_token": access_token,
            "preference_id": preference_id,
            "checkout_url": checkout_url,
        }, 201)

    @app.post("/api/pagos/webhook")
    def webhook_mercado_pago():
        body = request.get_json(silent=True) or {}
        data_id = str(
            request.args.get("data.id")
            or (body.get("data") or {}).get("id")
            or ""
        ).strip()
        notification_type = str(request.args.get("type") or body.get("type") or "").strip()

        if notification_type != "payment" or not data_id:
            return "", 200

        if not _valid_webhook_signature(data_id):
            app.logger.warning("Webhook de Mercado Pago con firma inválida.")
            return "", 401

        try:
            payment = _get_payment(data_id)
        except (requests.RequestException, ValueError, RuntimeError):
            app.logger.exception("No fue posible consultar el pago %s.", data_id)
            return "", 500

        order_id = str(payment.get("external_reference") or "").strip()
        status = str(payment.get("status") or "").strip()
        status_detail = str(payment.get("status_detail") or "").strip()
        currency = str(payment.get("currency_id") or "").strip()
        amount_cents = int(round(float(payment.get("transaction_amount") or 0) * 100))
        payer_email = str((payment.get("payer") or {}).get("email") or "").strip().lower()

        with _connect() as db:
            order = db.execute(
                "SELECT * FROM orders WHERE order_id=?",
                (order_id,),
            ).fetchone()
            if order is None:
                app.logger.error("Pago %s refiere una orden desconocida: %s", data_id, order_id)
                return "", 200

            valid_amount = amount_cents == int(order["amount_cents"])
            valid_currency = currency == str(order["currency"])
            valid_email = not payer_email or payer_email == str(order["email"]).lower()

            if not (valid_amount and valid_currency and valid_email):
                db.execute(
                    """
                    UPDATE orders
                    SET payment_id=?, payment_status=?, payment_status_detail=?,
                        status='validation_failed', updated_at=?
                    WHERE order_id=?
                    """,
                    (data_id, status, status_detail, _utc_now(), order_id),
                )
                app.logger.error("El pago %s no coincide con la orden %s.", data_id, order_id)
                return "", 200

            internal_status = "approved" if status == "approved" else status or "unknown"
            approved_at = _utc_now() if status == "approved" else None
            db.execute(
                """
                UPDATE orders
                SET payment_id=?, payment_status=?, payment_status_detail=?, status=?,
                    approved_at=COALESCE(approved_at, ?), updated_at=?
                WHERE order_id=?
                """,
                (data_id, status, status_detail, internal_status, approved_at, _utc_now(), order_id),
            )

        if status == "approved":
            plan = PLANES.get(str(order["plan_id"]))
            if plan is not None and order["client_id"]:
                activate_paid_access(
                    client_id=str(order["client_id"]),
                    email=str(order["email"]),
                    plan_id=str(order["plan_id"]),
                    payment_id=data_id,
                    days=plan["dias"],
                )
            app.logger.info("PAGO APROBADO Y ACCESO ACTIVADO | orden=%s | pago=%s", order_id, data_id)
        return "", 200

    @app.get("/api/pagos/orden/<order_id>")
    def consultar_orden(order_id: str):
        token = request.args.get("token", "")
        if not token:
            return respuesta_json({"ok": False, "error": "Token de consulta requerido."}, 401)

        with _connect() as db:
            order = db.execute(
                "SELECT * FROM orders WHERE order_id=? AND access_token=?",
                (order_id, token),
            ).fetchone()

        if order is None:
            return respuesta_json({"ok": False, "error": "Orden no encontrada."}, 404)

        plan = PLANES.get(str(order["plan_id"]), {})
        return respuesta_json({
            "ok": True,
            "order": {
                "order_id": order["order_id"],
                "email": order["email"],
                "plan_id": order["plan_id"],
                "plan_name": plan.get("titulo", order["plan_id"]),
                "amount": order["amount_cents"] / 100,
                "currency": order["currency"],
                "status": order["status"],
                "payment_status": order["payment_status"],
                "created_at": order["created_at"],
                "approved_at": order["approved_at"],
            },
            "message": (
                "Pago aprobado. Conserva este correo para la entrega o activación del acceso."
                if order["status"] == "approved"
                else "El pago todavía no aparece como aprobado."
            ),
        })
