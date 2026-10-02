from __future__ import annotations

from pathlib import Path

from flask import Flask, request

from .acceso_web import activate_owner, current_client_id, status
from .comunes import respuesta_json


def registrar_ruta_propietario(
	app: Flask,
	base_dir: Path | None = None,
) -> None:
	"""Registra únicamente las rutas de autenticación del propietario.

	La bandeja de mensajes pertenece a ``api/sugerencias.py`` para que la
	escritura y la lectura usen exactamente la misma función de almacenamiento.
	"""
	@app.post("/api/propietario/activar")
	def activar_propietario():
		data = request.get_json(silent=True)

		if not isinstance(data, dict):
			return respuesta_json(
				{"ok": False, "error": "Solicitud inválida."},
				400,
			)

		code = str(data.get("code", "")).strip()
		if not code:
			return respuesta_json(
				{"ok": False, "error": "Escribe el código de propietario."},
				400,
			)

		try:
			client_id = current_client_id()
			activate_owner(client_id, code)
			access = status(client_id)
		except ValueError as error:
			return respuesta_json(
				{"ok": False, "error": str(error)},
				403,
			)
		except RuntimeError as error:
			return respuesta_json(
				{"ok": False, "error": str(error)},
				500,
			)

		return respuesta_json({
			"ok": True,
			"message": "Licencia de Propietario activada correctamente.",
			"client_id": client_id,
			"kind": access.kind,
			"unlimited": access.unlimited,
			"valid": access.valid,
			"plan_id": getattr(access, "plan_id", None),
			"expires_at": getattr(access, "expires_at", None),
		})
