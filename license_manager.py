from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

APP_NAME = "Traductor_Nahuatl"
FREE_DAILY_LIMIT = 10
LICENSE_FILE_NAME = "license.json"
STATE_FILE_NAME = "usage_state.json"
PUBLIC_KEY_FILE_NAME = "public_key.pem"
CURRENT_LICENSE_VERSION = 2
SUPPORTED_LICENSE_VERSIONS = {1, 2}

# Protege el contador local contra ediciones casuales. No es una firma remota.
_LOCAL_STATE_KEY = b"traductor-nahuatl-local-state-v1-2026"

# Respaldo para instalaciones antiguas. En distribuciones nuevas se carga
# public_key.pem, lo que permite rotar la clave sin editar este módulo.
_FALLBACK_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAx1jAs2zY0Da7H0O74H6dExoY2Jxd2ADsQa7ytm24T70=
-----END PUBLIC KEY-----
"""

EXPIRING_KINDS = {"temporary", "trial", "monthly", "yearly", "educational"}
UNLIMITED_KINDS = EXPIRING_KINDS | {"permanent", "lifetime", "enterprise"}
VALID_PAID_KINDS = UNLIMITED_KINDS

_KIND_LABELS = {
    "free": "Gratuita",
    "temporary": "Temporal",
    "trial": "Prueba",
    "monthly": "Mensual",
    "yearly": "Anual",
    "educational": "Educativa",
    "permanent": "Permanente",
    "lifetime": "De por vida",
    "enterprise": "Institucional",
}


class LicenseError(RuntimeError):
    """Error general del sistema de licencias."""


class DailyLimitReached(LicenseError):
    """La versión gratuita agotó sus traducciones del día."""


class InvalidLicense(LicenseError):
    """La licencia es inválida, está dañada o pertenece a otro equipo."""


@dataclass(frozen=True)
class LicenseStatus:
    kind: str
    valid: bool
    machine_id: str
    version: int = CURRENT_LICENSE_VERSION
    license_id: str | None = None
    translations_used_today: int = 0
    translations_remaining_today: int | None = None
    expires_on: str | None = None
    days_remaining: int | None = None
    message: str = ""

    @property
    def unlimited(self) -> bool:
        return self.valid and self.kind in UNLIMITED_KINDS

    @property
    def label(self) -> str:
        return _KIND_LABELS.get(self.kind, self.kind.capitalize())


@dataclass
class UsageState:
    date: str
    used: int
    machine_id: str
    signature: str = ""


class LicenseManager:
    """Administra el modo gratuito y las licencias Ed25519 firmadas.

    Una traducción completada consume una unidad sin importar su sentido.
    Las licencias inválidas, dañadas o vencidas degradan al modo gratuito.
    """

    def __init__(
        self,
        data_dir: str | os.PathLike[str] | None = None,
        public_key_path: str | os.PathLike[str] | None = None,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir else self.default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.license_path = self.data_dir / LICENSE_FILE_NAME
        self.state_path = self.data_dir / STATE_FILE_NAME
        self.machine_id = self.get_machine_id()
        self.public_key_path = (
            Path(public_key_path)
            if public_key_path
            else Path(__file__).resolve().parent / PUBLIC_KEY_FILE_NAME
        )

    @staticmethod
    def default_data_dir() -> Path:
        if os.name == "nt":
            root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        elif platform.system() == "Darwin":
            root = Path.home() / "Library" / "Application Support"
        else:
            root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return root / APP_NAME

    @staticmethod
    def get_machine_id() -> str:
        values: list[str] = [platform.system(), platform.machine(), platform.node()]
        if os.name == "nt":
            try:
                import winreg  # type: ignore
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography",
                ) as key:
                    values.append(str(winreg.QueryValueEx(key, "MachineGuid")[0]))
            except OSError:
                pass
        else:
            for candidate in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
                try:
                    value = candidate.read_text(encoding="utf-8").strip()
                    if value:
                        values.append(value)
                        break
                except OSError:
                    continue
        values.append(str(uuid.getnode()))
        return hashlib.sha256("|".join(values).encode("utf-8", errors="ignore")).hexdigest()[:32]

    @staticmethod
    def _canonical_json(payload: dict[str, Any]) -> bytes:
        return json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def _state_signature(self, payload: dict[str, Any]) -> str:
        machine_key = hashlib.sha256(
            _LOCAL_STATE_KEY + self.machine_id.encode("ascii")
        ).digest()
        return hmac.new(machine_key, self._canonical_json(payload), hashlib.sha256).hexdigest()

    def _fresh_state(self) -> UsageState:
        payload = {"date": date.today().isoformat(), "used": 0, "machine_id": self.machine_id}
        return UsageState(**payload, signature=self._state_signature(payload))

    def _save_state(self, state: UsageState) -> None:
        payload = {"date": state.date, "used": int(state.used), "machine_id": state.machine_id}
        payload["signature"] = self._state_signature(payload)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)

    def _load_state(self) -> UsageState:
        if not self.state_path.exists():
            state = self._fresh_state()
            self._save_state(state)
            return state
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            signature = str(raw.pop("signature"))
            if not hmac.compare_digest(signature, self._state_signature(raw)):
                raise InvalidLicense("El contador local fue modificado o está dañado.")
            if raw.get("machine_id") != self.machine_id:
                raise InvalidLicense("El contador pertenece a otra instalación.")
            state = UsageState(**raw, signature=signature)
        except InvalidLicense:
            raise
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise InvalidLicense("No fue posible leer el contador local.") from exc

        today = date.today().isoformat()
        if state.date > today:
            raise InvalidLicense("La fecha del sistema parece haber retrocedido.")
        if state.date < today:
            state = self._fresh_state()
            self._save_state(state)
        return state

    def _load_public_key(self) -> Ed25519PublicKey:
        try:
            pem = self.public_key_path.read_bytes()
        except OSError:
            pem = _FALLBACK_PUBLIC_KEY_PEM
        try:
            key = serialization.load_pem_public_key(pem)
        except (ValueError, TypeError) as exc:
            raise InvalidLicense("La clave pública configurada no pudo leerse.") from exc
        if not isinstance(key, Ed25519PublicKey):
            raise InvalidLicense("La clave pública configurada no es Ed25519.")
        return key

    def _write_warning(self, message: str) -> None:
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            with (self.data_dir / "license_warnings.log").open("a", encoding="utf-8") as log:
                log.write(f"[{timestamp}] {message}\n")
        except OSError:
            pass

    def _quarantine_file(self, path: Path, reason: str) -> Path | None:
        if not path.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = path.with_name(f"{path.stem}_{reason}_{timestamp}{path.suffix}")
        counter = 1
        while candidate.exists():
            candidate = path.with_name(f"{path.stem}_{reason}_{timestamp}_{counter}{path.suffix}")
            counter += 1
        try:
            path.replace(candidate)
            return candidate
        except OSError:
            return None

    def _free_status(self, notice: str = "") -> LicenseStatus:
        try:
            state = self._load_state()
        except InvalidLicense as exc:
            quarantined = self._quarantine_file(self.state_path, "invalido")
            detail = f"Contador local inválido: {exc}"
            if quarantined:
                detail += f" Se conservó como {quarantined.name}."
            self._write_warning(detail)
            state = self._fresh_state()
            try:
                self._save_state(state)
            except OSError:
                pass
        remaining = max(0, FREE_DAILY_LIMIT - state.used)
        message = f"Traducciones disponibles hoy: {remaining} de {FREE_DAILY_LIMIT}"
        if notice:
            message = f"{notice} {message}"
        return LicenseStatus(
            kind="free",
            valid=True,
            machine_id=self.machine_id,
            translations_used_today=state.used,
            translations_remaining_today=remaining,
            message=message,
        )

    def _read_license_payload(self) -> dict[str, Any] | None:
        if not self.license_path.exists():
            return None
        try:
            envelope = json.loads(self.license_path.read_text(encoding="utf-8"))
            payload = envelope["payload"]
            if not isinstance(payload, dict):
                raise TypeError("payload inválido")
            signature = base64.b64decode(envelope["signature"], validate=True)
            self._load_public_key().verify(signature, self._canonical_json(payload))
            return payload
        except (OSError, ValueError, KeyError, TypeError, InvalidSignature) as exc:
            raise InvalidLicense("La licencia no es válida o fue modificada.") from exc

    @staticmethod
    def _validate_version(payload: dict[str, Any]) -> int:
        # Licencias anteriores no incluían version y se consideran versión 1.
        version = int(payload.get("version", 1))
        if version not in SUPPORTED_LICENSE_VERSIONS:
            raise InvalidLicense(f"Versión de licencia no compatible: {version}.")
        return version

    def _licensed_status(self, payload: dict[str, Any]) -> LicenseStatus:
        version = self._validate_version(payload)
        kind = str(payload.get("kind", ""))
        if kind not in VALID_PAID_KINDS:
            raise InvalidLicense("Tipo de licencia desconocido.")
        if payload.get("machine_id") != self.machine_id:
            raise InvalidLicense("La licencia pertenece a otro equipo.")

        license_id = payload.get("license_id")
        if version >= 2 and (not isinstance(license_id, str) or not license_id.strip()):
            raise InvalidLicense("La licencia versión 2 no contiene license_id.")

        expires_on = payload.get("expires_on")
        days_remaining: int | None = None
        if kind in EXPIRING_KINDS:
            if not expires_on:
                raise InvalidLicense("La licencia temporal no contiene vencimiento.")
            expiration = date.fromisoformat(str(expires_on))
            days_remaining = (expiration - date.today()).days
            if days_remaining < 0:
                raise InvalidLicense("La licencia temporal venció.")
        elif expires_on:
            # Se acepta por compatibilidad, pero se valida el formato.
            date.fromisoformat(str(expires_on))

        return LicenseStatus(
            kind=kind,
            valid=True,
            machine_id=self.machine_id,
            version=version,
            license_id=str(license_id) if license_id else None,
            expires_on=str(expires_on) if expires_on else None,
            days_remaining=days_remaining,
            message="Licencia válida.",
        )

    def status(self) -> LicenseStatus:
        """Devuelve el estado; cualquier fallo degrada al modo gratuito."""
        try:
            payload = self._read_license_payload()
            if not payload:
                return self._free_status()
            return self._licensed_status(payload)
        except InvalidLicense as exc:
            reason = "vencida" if "venció" in str(exc) else "invalida"
            quarantined = self._quarantine_file(self.license_path, reason)
            detail = str(exc)
            if quarantined:
                detail += f" Se conservó como {quarantined.name}."
            self._write_warning(detail)
            return self._free_status(
                "La licencia no pudo utilizarse; se continuará en modo gratuito."
            )
        except Exception as exc:
            self._write_warning(f"Fallo inesperado al validar la licencia: {exc!r}")
            return self._free_status(
                "El sistema de licencias presentó un problema; se continuará en modo gratuito."
            )

    def ensure_translation_allowed(self) -> LicenseStatus:
        status = self.status()
        if status.unlimited:
            return status
        if not status.translations_remaining_today:
            raise DailyLimitReached(
                f"Has utilizado las {FREE_DAILY_LIMIT} traducciones gratuitas de hoy. "
                "Puedes activar una licencia para continuar."
            )
        return status

    def register_translation(self) -> LicenseStatus:
        """Registra sólo una traducción completada correctamente."""
        current = self.ensure_translation_allowed()
        if current.unlimited:
            return current
        state = self._load_state()
        state.used += 1
        self._save_state(state)
        return self.status()

    def install_license(self, source: str | os.PathLike[str]) -> LicenseStatus:
        source_path = Path(source)
        if not source_path.is_file():
            raise InvalidLicense("No se encontró el archivo de licencia.")

        # Validar en una ubicación temporal antes de reemplazar la licencia activa.
        original_path = self.license_path
        candidate = self.data_dir / "license_candidate.json"
        try:
            candidate.write_bytes(source_path.read_bytes())
            self.license_path = candidate
            payload = self._read_license_payload()
            if not payload:
                raise InvalidLicense("El archivo no contiene una licencia.")
            status = self._licensed_status(payload)
        finally:
            self.license_path = original_path
            candidate.unlink(missing_ok=True)

        temporary = original_path.with_suffix(".tmp")
        temporary.write_bytes(source_path.read_bytes())
        temporary.replace(original_path)
        return status

    def remove_license(self) -> None:
        self.license_path.unlink(missing_ok=True)

    def user_summary(self) -> str:
        status = self.status()
        if status.kind == "free":
            return (
                "Licencia: Gratuita\n"
                f"Traducciones disponibles hoy: {status.translations_remaining_today} "
                f"de {FREE_DAILY_LIMIT}"
            )
        lines = [f"Licencia: {status.label}"]
        if status.license_id:
            lines.append(f"Identificador: {status.license_id}")
        if status.expires_on:
            lines.append(f"Vence: {status.expires_on}")
        if status.days_remaining is not None:
            unit = "día" if status.days_remaining == 1 else "días"
            lines.append(f"Tiempo restante: {status.days_remaining} {unit}")
        lines.append(f"Formato: versión {status.version}")
        return "\n".join(lines)


_default_manager: LicenseManager | None = None


def get_license_manager() -> LicenseManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = LicenseManager()
    return _default_manager
