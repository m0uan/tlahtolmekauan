from __future__ import annotations

from pathlib import Path
import tempfile

from flask import Flask, request

from .comunes import licencia_a_dict, respuesta_json


def registrar_rutas_licencia(app: Flask, license_manager, invalid_license_error) -> None:
	@app.route("/api/licencia", methods=["GET"])
	def api_licencia():
		if license_manager is None:
			return respuesta_json({
				"ok": False,
				"error": "El administrador de licencias no está disponible.",
			}, 500)

		status = license_manager.status()

		return respuesta_json({
			"ok": True,
			"license": licencia_a_dict(status),
		})

	@app.route("/api/activar-licencia", methods=["POST"])
	def api_activar_licencia():
		if license_manager is None:
			return respuesta_json({
				"ok": False,
				"error": "El administrador de licencias no está disponible.",
			}, 500)

		if request.content_length is None or request.content_length <= 0:
			return respuesta_json({
				"ok": False,
				"error": "No se recibió ningún archivo de licencia.",
			}, 400)

		content_type = request.content_type or ""
		if "multipart/form-data" not in content_type:
			return respuesta_json({
				"ok": False,
				"error": "Formato de solicitud inválido.",
			}, 400)

		license_file = request.files.get("license")

		if license_file is None or not license_file.filename:
			return respuesta_json({
				"ok": False,
				"error": "No se encontró el archivo de licencia.",
			}, 400)

		if not license_file.filename.lower().endswith(".json"):
			return respuesta_json({
				"ok": False,
				"error": "La licencia debe ser un archivo JSON.",
			}, 400)

		temporary_path = None

		try:
			with tempfile.NamedTemporaryFile(
				mode="wb",
				suffix=".json",
				delete=False,
			) as temporary_file:
				license_file.save(temporary_file)
				temporary_path = temporary_file.name

			status = license_manager.install_license(temporary_path)

			return respuesta_json({
				"ok": True,
				"message": "Licencia activada correctamente.",
				"license": licencia_a_dict(status),
			})

		except invalid_license_error as exc:
			return respuesta_json({
				"ok": False,
				"error": str(exc),
			}, 400)

		except Exception as exc:
			return respuesta_json({
				"ok": False,
				"error": "No fue posible activar la licencia.",
				"detalle": str(exc),
			}, 500)

		finally:
			if temporary_path:
				try:
					Path(temporary_path).unlink(missing_ok=True)
				except OSError:
					pass
