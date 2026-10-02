from __future__ import annotations

import json
import os
import smtplib
import threading
import time
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from flask import Flask, request

from .acceso_web import current_client_id, owner_authenticated


_LOCK = threading.Lock()
_RECENT_REQUESTS: dict[str, list[float]] = {}


def _clean_text(value: Any, max_length: int) -> str:
	if value is None:
		return ""
	text = str(value).replace("\x00", "").strip()
	return text[:max_length]


def _client_ip() -> str:
	forwarded = request.headers.get("X-Forwarded-For", "")
	if forwarded:
		return forwarded.split(",", 1)[0].strip()
	return request.remote_addr or "desconocida"


def _rate_limited(ip_address: str, limit: int = 5, window_seconds: int = 600) -> bool:
	now = time.time()
	cutoff = now - window_seconds

	with _LOCK:
		timestamps = [stamp for stamp in _RECENT_REQUESTS.get(ip_address, []) if stamp >= cutoff]
		if len(timestamps) >= limit:
			_RECENT_REQUESTS[ip_address] = timestamps
			return True

		timestamps.append(now)
		_RECENT_REQUESTS[ip_address] = timestamps
		return False


def _storage_path(base_dir: Path) -> Path:
	configured = os.getenv("SUGGESTIONS_FILE", "").strip()
	if configured:
		return Path(configured).expanduser()

	data_dir = Path(os.getenv("DATA_DIR", str(base_dir / "data"))).expanduser()
	return data_dir / "sugerencias.jsonl"


def _normalize_message(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
	"""Completa campos administrativos sin perder mensajes antiguos."""
	normalized = dict(record)
	changed = False

	defaults = {
		"id": uuid.uuid4().hex,
		"read": False,
		"archived": False,
		"favorite": False,
		"replied_at": "",
		"updated_at": normalized.get("created_at", ""),
	}

	for key, value in defaults.items():
		if key not in normalized:
			normalized[key] = value
			changed = True

	return normalized, changed


def _write_messages(path: Path, records: list[dict[str, Any]]) -> None:
	"""Reescribe el archivo de manera atómica para evitar datos parciales."""
	path.parent.mkdir(parents=True, exist_ok=True)
	temporary_path = path.with_suffix(path.suffix + ".tmp")

	with temporary_path.open("w", encoding="utf-8") as file:
		for record in records:
			line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
			file.write(line + "\n")

	temporary_path.replace(path)


def _save_message(path: Path, record: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	normalized, _ = _normalize_message(record)
	line = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

	with _LOCK:
		with path.open("a", encoding="utf-8") as file:
			file.write(line + "\n")


def _load_all_messages(path: Path) -> list[dict[str, Any]]:
	if not path.exists():
		return []

	records: list[dict[str, Any]] = []
	changed = False

	with _LOCK:
		with path.open("r", encoding="utf-8") as file:
			for line in file:
				line = line.strip()
				if not line:
					continue
				try:
					record = json.loads(line)
				except json.JSONDecodeError:
					continue
				if isinstance(record, dict):
					normalized, record_changed = _normalize_message(record)
					records.append(normalized)
					changed = changed or record_changed

		if changed:
			_write_messages(path, records)

	return records


def _load_messages(path: Path, limit: int = 100) -> list[dict[str, Any]]:
	"""Carga los mensajes más recientes y migra registros anteriores."""
	records = _load_all_messages(path)
	return list(reversed(records[-max(1, min(limit, 500)):]))


def _update_message(path: Path, message_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
	with _LOCK:
		if not path.exists():
			return None

		records: list[dict[str, Any]] = []
		updated: dict[str, Any] | None = None

		with path.open("r", encoding="utf-8") as file:
			for line in file:
				line = line.strip()
				if not line:
					continue
				try:
					record = json.loads(line)
				except json.JSONDecodeError:
					continue
				if not isinstance(record, dict):
					continue

				record, _ = _normalize_message(record)
				if record.get("id") == message_id:
					record.update(updates)
					record["updated_at"] = datetime.now(timezone.utc).isoformat()
					updated = record
				records.append(record)

		if updated is None:
			return None

		_write_messages(path, records)
		return updated


def _delete_message(path: Path, message_id: str) -> bool:
	with _LOCK:
		if not path.exists():
			return False

		records: list[dict[str, Any]] = []
		deleted = False

		with path.open("r", encoding="utf-8") as file:
			for line in file:
				line = line.strip()
				if not line:
					continue
				try:
					record = json.loads(line)
				except json.JSONDecodeError:
					continue
				if not isinstance(record, dict):
					continue

				record, _ = _normalize_message(record)
				if record.get("id") == message_id:
					deleted = True
					continue
				records.append(record)

		if not deleted:
			return False

		_write_messages(path, records)
		return True


def _send_email_notification(record: dict[str, Any]) -> bool:
	smtp_host = os.getenv("SMTP_HOST", "").strip()
	smtp_port = int(os.getenv("SMTP_PORT", "587"))
	smtp_user = os.getenv("SMTP_USER", "").strip()
	smtp_password = os.getenv("SMTP_PASSWORD", "")
	recipient = os.getenv("SUGGESTIONS_TO_EMAIL", "").strip()
	sender = os.getenv("SMTP_FROM", smtp_user).strip()

	if not smtp_host or not recipient or not sender:
		return False

	message = EmailMessage()
	message["Subject"] = f"Nuevo mensaje de tlahtolmekauan: {record['category']}"
	message["From"] = sender
	message["To"] = recipient

	if record.get("email"):
		message["Reply-To"] = record["email"]

	message.set_content(
		"\n".join(
			[
				"Se recibió un mensaje desde speak-nahuatl.com.",
				"",
				f"Fecha UTC: {record['created_at']}",
				f"Nombre: {record.get('name') or 'No indicado'}",
				f"Correo: {record.get('email') or 'No indicado'}",
				f"Categoría: {record['category']}",
				f"Página: {record.get('page') or 'No indicada'}",
				"",
				"Mensaje:",
				record["message"],
			]
		)
	)

	if smtp_port == 465:
		with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
			if smtp_user:
				smtp.login(smtp_user, smtp_password)
			smtp.send_message(message)
	else:
		with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
			smtp.ehlo()
			smtp.starttls()
			smtp.ehlo()
			if smtp_user:
				smtp.login(smtp_user, smtp_password)
			smtp.send_message(message)

	return True


def registrar_ruta_sugerencias(app: Flask, base_dir: Path) -> None:
	@app.post("/api/sugerencias")
	def recibir_sugerencia():
		ip_address = _client_ip()

		if _rate_limited(ip_address):
			return {
				"ok": False,
				"error": "Se enviaron demasiados mensajes. Espera unos minutos e inténtalo de nuevo.",
			}, 429

		payload = request.get_json(silent=True)
		if not isinstance(payload, dict):
			return {"ok": False, "error": "La solicitud no contiene datos válidos."}, 400

		# Campo trampa. Los visitantes normales nunca lo completan.
		if _clean_text(payload.get("website"), 200):
			return {"ok": True, "message": "Mensaje recibido."}, 200

		name = _clean_text(payload.get("name"), 100)
		email = _clean_text(payload.get("email"), 160)
		category = _clean_text(payload.get("category"), 60) or "Other"
		message = _clean_text(payload.get("message"), 4000)
		page = _clean_text(payload.get("page"), 500)

		if not message:
			return {"ok": False, "error": "Escribe un mensaje antes de enviarlo."}, 400

		if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
			return {"ok": False, "error": "El correo electrónico no parece válido."}, 400

		now = datetime.now(timezone.utc).isoformat()
		record = {
			"id": uuid.uuid4().hex,
			"created_at": now,
			"updated_at": now,
			"read": False,
			"archived": False,
			"favorite": False,
			"replied_at": "",
			"name": name,
			"email": email,
			"category": category,
			"message": message,
			"page": page,
			"ip": ip_address,
			"user_agent": _clean_text(request.headers.get("User-Agent"), 300),
		}

		storage_path = _storage_path(base_dir)
		_save_message(storage_path, record)

		email_sent = False
		try:
			email_sent = _send_email_notification(record)
		except Exception:
			app.logger.exception("No se pudo enviar la notificación de sugerencia por correo.")

		return {
			"ok": True,
			"message": "Gracias. Tu mensaje fue recibido correctamente.",
			"email_notified": email_sent,
			"storage_file": str(storage_path),
		}, 201

	def _owner_or_error():
		client_id = current_client_id()
		if owner_authenticated(client_id):
			return None
		return {
			"ok": False,
			"error": "Debes activar la cuenta de propietario para administrar la bandeja.",
		}, 403

	@app.get("/api/propietario/mensajes")
	def bandeja_propietario():
		error = _owner_or_error()
		if error:
			return error

		try:
			limit = int(request.args.get("limit", "100"))
		except ValueError:
			limit = 100

		storage_path = _storage_path(base_dir)
		messages = _load_messages(storage_path, limit=limit)
		return {
			"ok": True,
			"messages": messages,
			"count": len(messages),
			"unread_count": sum(1 for item in messages if not item.get("read")),
			"archived_count": sum(1 for item in messages if item.get("archived")),
			"storage_file": str(storage_path),
			"email_fallback_configured": bool(
				os.getenv("SMTP_HOST", "").strip()
				and os.getenv("SUGGESTIONS_TO_EMAIL", "").strip()
			),
		}, 200

	@app.post("/api/propietario/mensajes/<message_id>/leer")
	def marcar_mensaje_leido(message_id: str):
		error = _owner_or_error()
		if error:
			return error

		payload = request.get_json(silent=True) or {}
		read = bool(payload.get("read", True))
		message = _update_message(_storage_path(base_dir), message_id, {"read": read})
		if message is None:
			return {"ok": False, "error": "Mensaje no encontrado."}, 404
		return {"ok": True, "message": message}, 200

	@app.post("/api/propietario/mensajes/<message_id>/archivar")
	def archivar_mensaje(message_id: str):
		error = _owner_or_error()
		if error:
			return error

		payload = request.get_json(silent=True) or {}
		archived = bool(payload.get("archived", True))
		message = _update_message(
			_storage_path(base_dir),
			message_id,
			{"archived": archived, "read": True},
		)
		if message is None:
			return {"ok": False, "error": "Mensaje no encontrado."}, 404
		return {"ok": True, "message": message}, 200

	@app.post("/api/propietario/mensajes/<message_id>/favorito")
	def marcar_mensaje_favorito(message_id: str):
		error = _owner_or_error()
		if error:
			return error

		payload = request.get_json(silent=True) or {}
		favorite = bool(payload.get("favorite", True))
		message = _update_message(_storage_path(base_dir), message_id, {"favorite": favorite})
		if message is None:
			return {"ok": False, "error": "Mensaje no encontrado."}, 404
		return {"ok": True, "message": message}, 200

	@app.post("/api/propietario/mensajes/<message_id>/responder")
	def responder_mensaje(message_id: str):
		error = _owner_or_error()
		if error:
			return error

		payload = request.get_json(silent=True) or {}
		subject = _clean_text(payload.get("subject"), 160)
		body = _clean_text(payload.get("body"), 4000)
		if not subject or not body:
			return {"ok": False, "error": "Escribe el asunto y la respuesta."}, 400

		storage_path = _storage_path(base_dir)
		record = next((item for item in _load_all_messages(storage_path) if item.get("id") == message_id), None)
		if record is None:
			return {"ok": False, "error": "Mensaje no encontrado."}, 404
		recipient = _clean_text(record.get("email"), 160)
		if not recipient:
			return {"ok": False, "error": "Este mensaje no incluye correo para responder."}, 400

		smtp_host = os.getenv("SMTP_HOST", "").strip()
		smtp_port = int(os.getenv("SMTP_PORT", "587"))
		smtp_user = os.getenv("SMTP_USER", "").strip()
		smtp_password = os.getenv("SMTP_PASSWORD", "")
		sender = os.getenv("SMTP_FROM", smtp_user).strip()
		if not smtp_host or not sender:
			return {"ok": False, "error": "Configura SMTP_HOST y SMTP_FROM para responder desde la plataforma."}, 503

		email_message = EmailMessage()
		email_message["Subject"] = subject
		email_message["From"] = sender
		email_message["To"] = recipient
		email_message.set_content(body)
		try:
			if smtp_port == 465:
				with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
					if smtp_user:
						smtp.login(smtp_user, smtp_password)
					smtp.send_message(email_message)
			else:
				with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
					smtp.ehlo(); smtp.starttls(); smtp.ehlo()
					if smtp_user:
						smtp.login(smtp_user, smtp_password)
					smtp.send_message(email_message)
		except Exception:
			app.logger.exception("No se pudo enviar la respuesta del propietario.")
			return {"ok": False, "error": "No se pudo enviar la respuesta por correo."}, 502

		now = datetime.now(timezone.utc).isoformat()
		_update_message(storage_path, message_id, {"read": True, "replied_at": now})
		return {"ok": True, "message": "Respuesta enviada correctamente."}, 200

	@app.delete("/api/propietario/mensajes/<message_id>")
	def eliminar_mensaje(message_id: str):
		error = _owner_or_error()
		if error:
			return error

		if not _delete_message(_storage_path(base_dir), message_id):
			return {"ok": False, "error": "Mensaje no encontrado."}, 404
		return {"ok": True, "message": "Mensaje eliminado."}, 200
