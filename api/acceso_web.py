from __future__ import annotations

import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

FREE_DAILY_LIMIT = 10
CLIENT_COOKIE = "tlahtolmekauan_cliente"
CLIENT_ID_MIN_LENGTH = 32
CLIENT_ID_MAX_LENGTH = 128
OWNER_COOKIE = "tlahtolmekauan_propietario"
OWNER_SESSION_MAX_AGE = 60 * 60 * 24 * 365
OWNER_SESSION_SALT = "tlahtolmekauan-owner-v1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).replace(microsecond=0).isoformat()


def data_dir() -> Path:
    configured = os.getenv("PAYMENT_DATA_DIR", "").strip()
    if configured:
        path = Path(configured)
    elif Path("/data").is_dir():
        path = Path("/data") / "pagos"
    else:
        path = Path(__file__).resolve().parent.parent / "data" / "pagos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "mercado_pago.sqlite3"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(db_path(), timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS web_licenses (
                license_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                email TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                payment_id TEXT NOT NULL UNIQUE,
                starts_at TEXT NOT NULL,
                expires_at TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(client_id)
            );

            CREATE INDEX IF NOT EXISTS idx_web_licenses_client
            ON web_licenses(client_id, active);

            CREATE TABLE IF NOT EXISTS daily_usage (
                client_id TEXT NOT NULL,
                usage_date TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(client_id, usage_date),
                FOREIGN KEY(client_id) REFERENCES clients(client_id)
            );

            CREATE TABLE IF NOT EXISTS translation_requests (
                client_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                usage_date TEXT NOT NULL,
                input_text TEXT NOT NULL,
                direction TEXT NOT NULL,
                result_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(client_id, request_id),
                FOREIGN KEY(client_id) REFERENCES clients(client_id)
            );

            CREATE TABLE IF NOT EXISTS owner_clients (
                client_id TEXT PRIMARY KEY,
                activated_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(client_id)
            );
            """
        )


def _valid_client_id(value: str) -> bool:
    """Comprueba que el identificador tenga un formato seguro y razonable."""
    if not (CLIENT_ID_MIN_LENGTH <= len(value) <= CLIENT_ID_MAX_LENGTH):
        return False
    return all(character.isalnum() or character in "-_" for character in value)


def current_client_id() -> str:
    """Devuelve un identificador estable para el navegador actual.

    El valor también se conserva en ``g`` para evitar que dos llamadas dentro
    de la misma petición generen identificadores diferentes antes de que el
    navegador reciba la cookie.
    """
    request_client_id = getattr(g, "client_id", None)
    if request_client_id:
        return request_client_id

    existing = str(request.cookies.get(CLIENT_COOKIE, "")).strip()
    if _valid_client_id(existing):
        client_id = existing
    else:
        client_id = secrets.token_urlsafe(32)
        g.set_client_cookie = client_id

    g.client_id = client_id

    now = utc_text()
    with connect() as db:
        db.execute(
            """
            INSERT INTO clients(client_id, created_at, last_seen_at)
            VALUES (?, ?, ?)
            ON CONFLICT(client_id) DO UPDATE SET last_seen_at=excluded.last_seen_at
            """,
            (client_id, now, now),
        )
        db.commit()

    return client_id


def _owner_serializer() -> URLSafeTimedSerializer | None:
    """Crea el firmador de la sesión del propietario.

    OWNER_SESSION_SECRET es la opción recomendada. Si todavía no existe, se
    utiliza OWNER_ACCESS_CODE para mantener compatibilidad con la instalación
    actual sin exponer el código en la cookie.
    """
    secret = (
        os.getenv("OWNER_SESSION_SECRET", "").strip()
        or os.getenv("OWNER_ACCESS_CODE", "").strip()
    )
    if not secret:
        return None
    return URLSafeTimedSerializer(secret_key=secret, salt=OWNER_SESSION_SALT)


def owner_session_client_id() -> str | None:
    """Devuelve el client_id autenticado por la cookie firmada del propietario."""
    token = str(request.cookies.get(OWNER_COOKIE, "")).strip()
    serializer = _owner_serializer()
    if not token or serializer is None:
        return None

    try:
        payload = serializer.loads(token, max_age=OWNER_SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None

    if not isinstance(payload, dict):
        return None
    client_id = str(payload.get("client_id", "")).strip()
    return client_id if _valid_client_id(client_id) else None


def owner_authenticated(client_id: str | None = None) -> bool:
    """Comprueba la cuenta de propietario por sesión firmada o por registro DB."""
    expected_client_id = str(client_id or current_client_id()).strip()
    session_client_id = owner_session_client_id()
    if session_client_id and secrets.compare_digest(session_client_id, expected_client_id):
        return True
    return is_owner(expected_client_id)


def _request_uses_https() -> bool:
    """Detecta HTTPS directo o HTTPS terminado por un proxy como Railway."""
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    if forwarded_proto:
        return forwarded_proto.split(",", 1)[0].strip().lower() == "https"
    return bool(request.is_secure)


def set_client_cookie(response):
    """Adjunta al navegador el identificador generado durante la petición."""
    client_id = getattr(g, "set_client_cookie", None)
    secure_cookie = _request_uses_https()

    if client_id:
        response.set_cookie(
            CLIENT_COOKIE,
            client_id,
            max_age=60 * 60 * 24 * 365 * 5,
            secure=secure_cookie,
            httponly=True,
            samesite="Lax",
            path="/",
        )

    owner_client_id = getattr(g, "set_owner_cookie", None)
    if owner_client_id:
        serializer = _owner_serializer()
        if serializer is not None:
            token = serializer.dumps({"client_id": owner_client_id})
            response.set_cookie(
                OWNER_COOKIE,
                token,
                max_age=OWNER_SESSION_MAX_AGE,
                secure=secure_cookie,
                httponly=True,
                samesite="Strict",
                path="/",
            )

    if getattr(g, "clear_owner_cookie", False):
        response.delete_cookie(OWNER_COOKIE, path="/")

    return response


@dataclass(frozen=True)
class WebAccessStatus:
    kind: str
    valid: bool
    translations_used_today: int
    translations_remaining_today: int | None
    expires_on: str | None
    days_remaining: int | None
    message: str
    unlimited: bool
    plan_id: str | None = None
    email: str | None = None


def _active_license(client_id: str):
    now = utc_text()
    with connect() as db:
        return db.execute(
            """
            SELECT * FROM web_licenses
            WHERE client_id=? AND active=1
              AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY CASE WHEN expires_at IS NULL THEN 1 ELSE 0 END DESC,
                     expires_at DESC
            LIMIT 1
            """,
            (client_id, now),
        ).fetchone()



def is_owner(client_id: str) -> bool:
    """Indica si el navegador está registrado como propietario."""
    client_id = str(client_id).strip()
    if not _valid_client_id(client_id):
        return False

    init_db()
    with connect() as db:
        row = db.execute(
            "SELECT 1 FROM owner_clients WHERE client_id=?",
            (client_id,),
        ).fetchone()
    return row is not None


def activate_owner(client_id: str, supplied_code: str) -> None:
    """Activa acceso ilimitado tras validar OWNER_ACCESS_CODE."""
    client_id = str(client_id).strip()
    expected_code = os.environ.get("OWNER_ACCESS_CODE", "").strip()
    supplied_code = str(supplied_code).strip()

    if not _valid_client_id(client_id):
        raise ValueError("El identificador del navegador no es válido.")

    if not expected_code:
        raise RuntimeError(
            "OWNER_ACCESS_CODE no está configurada en Railway."
        )

    if not secrets.compare_digest(supplied_code, expected_code):
        raise ValueError("El código de propietario es incorrecto.")

    init_db()
    with connect() as db:
        db.execute(
            """
            INSERT INTO owner_clients(client_id, activated_at)
            VALUES (?, ?)
            ON CONFLICT(client_id) DO UPDATE
            SET activated_at=excluded.activated_at
            """,
            (client_id, utc_text()),
        )
        db.commit()

    g.set_owner_cookie = client_id


def status(client_id: str | None = None) -> WebAccessStatus:
    init_db()
    client_id = client_id or current_client_id()

    # El propietario tiene prioridad sobre cualquier licencia comercial
    # o límite gratuito.
    if owner_authenticated(client_id):
        return WebAccessStatus(
            kind="owner",
            valid=True,
            translations_used_today=0,
            translations_remaining_today=None,
            expires_on=None,
            days_remaining=None,
            message="Acceso ilimitado del propietario",
            unlimited=True,
            plan_id="owner",
            email=None,
        )

    license_row = _active_license(client_id)
    if license_row is not None:
        expires_at = license_row["expires_at"]
        permanent = expires_at is None
        days_remaining = None
        expires_on = None
        if expires_at:
            expiry = datetime.fromisoformat(expires_at)
            days_remaining = max(0, (expiry.date() - utc_now().date()).days)
            expires_on = expiry.date().isoformat()
        return WebAccessStatus(
            kind="permanent" if permanent else "temporary",
            valid=True,
            translations_used_today=0,
            translations_remaining_today=None,
            expires_on=expires_on,
            days_remaining=days_remaining,
            message="Uso ilimitado" if permanent else f"Acceso vigente hasta {expires_on}",
            unlimited=True,
            plan_id=license_row["plan_id"],
            email=license_row["email"],
        )

    today = date.today().isoformat()
    with connect() as db:
        row = db.execute(
            "SELECT used FROM daily_usage WHERE client_id=? AND usage_date=?",
            (client_id, today),
        ).fetchone()
    used = int(row["used"]) if row else 0
    remaining = max(0, FREE_DAILY_LIMIT - used)
    return WebAccessStatus(
        kind="free",
        valid=True,
        translations_used_today=used,
        translations_remaining_today=remaining,
        expires_on=None,
        days_remaining=None,
        message=f"Traducciones disponibles hoy: {remaining} de {FREE_DAILY_LIMIT}",
        unlimited=False,
    )


def ensure_translation_allowed(client_id: str | None = None) -> WebAccessStatus:
    current = status(client_id)
    if current.unlimited:
        return current
    if (current.translations_remaining_today or 0) <= 0:
        raise PermissionError("Alcanzaste el límite gratuito de 10 traducciones de hoy.")
    return current


def get_registered_translation(client_id: str, request_id: str):
    if not request_id:
        return None
    init_db()
    with connect() as db:
        return db.execute(
            """
            SELECT input_text, direction, result_text
            FROM translation_requests
            WHERE client_id=? AND request_id=?
            """,
            (client_id, request_id),
        ).fetchone()


def register_translation_once(
    *,
    client_id: str,
    request_id: str,
    input_text: str,
    direction: str,
    result_text: str,
) -> tuple[WebAccessStatus, bool]:
    """Registra como máximo un uso por request_id.

    Devuelve (estado, counted), donde counted es True únicamente cuando la
    solicitud se contabilizó por primera vez.
    """
    init_db()
    current = status(client_id)
    if current.unlimited:
        return current, False

    today = date.today().isoformat()
    now = utc_text()

    with connect() as db:
        db.execute("BEGIN IMMEDIATE")

        duplicate = db.execute(
            "SELECT 1 FROM translation_requests WHERE client_id=? AND request_id=?",
            (client_id, request_id),
        ).fetchone()
        if duplicate is not None:
            db.rollback()
            return status(client_id), False

        row = db.execute(
            "SELECT used FROM daily_usage WHERE client_id=? AND usage_date=?",
            (client_id, today),
        ).fetchone()
        used = int(row["used"]) if row else 0
        if used >= FREE_DAILY_LIMIT:
            db.rollback()
            raise PermissionError(
                f"Alcanzaste el límite gratuito de {FREE_DAILY_LIMIT} traducciones de hoy."
            )

        db.execute(
            """
            INSERT INTO translation_requests(
                client_id, request_id, usage_date, input_text, direction,
                result_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, request_id, today, input_text, direction, result_text, now),
        )
        db.execute(
            """
            INSERT INTO daily_usage(client_id, usage_date, used)
            VALUES (?, ?, 1)
            ON CONFLICT(client_id, usage_date)
            DO UPDATE SET used=used+1
            """,
            (client_id, today),
        )
        db.commit()

    return status(client_id), True


def activate_paid_access(*, client_id: str, email: str, plan_id: str, payment_id: str, days: int | None) -> None:
    """Activa una compra sin perder el tiempo restante de una licencia vigente.

    Cada payment_id se procesa una sola vez. Para los planes temporales, la
    renovación comienza al vencer la licencia activa más larga del cliente; si
    no hay una licencia vigente, comienza en el momento de la aprobación.
    """
    init_db()
    now = utc_now()
    now_text = utc_text(now)

    with connect() as db:
        db.execute("BEGIN IMMEDIATE")

        already_registered = db.execute(
            "SELECT 1 FROM web_licenses WHERE payment_id=?",
            (payment_id,),
        ).fetchone()
        if already_registered is not None:
            db.rollback()
            return

        starts = now
        expires: datetime | None = None

        if days is not None:
            active_license = db.execute(
                """
                SELECT expires_at
                FROM web_licenses
                WHERE client_id=? AND active=1
                  AND expires_at IS NOT NULL
                  AND expires_at > ?
                ORDER BY expires_at DESC
                LIMIT 1
                """,
                (client_id, now_text),
            ).fetchone()

            if active_license is not None:
                current_expiry = datetime.fromisoformat(active_license["expires_at"])
                if current_expiry > starts:
                    starts = current_expiry

            expires = starts + timedelta(days=days)

        db.execute(
            """
            INSERT INTO web_licenses(
                license_id, client_id, email, plan_id, payment_id,
                starts_at, expires_at, active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                secrets.token_urlsafe(24),
                client_id,
                email,
                plan_id,
                payment_id,
                utc_text(starts),
                utc_text(expires) if expires else None,
                now_text,
            ),
        )
        db.commit()
