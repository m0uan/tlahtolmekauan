from __future__ import annotations

import contextlib
import io
import traceback

from flask import Flask, request

from .comunes import licencia_a_dict, respuesta_json


def registrar_ruta_traduccion(
	app: Flask,
	license_manager,
	motor_error,
	translate_ntl_to_sp,
	translate_sp_to_ntl,
	daily_limit_error,
	invalid_license_error,
) -> None:
	@app.route("/api/traducir", methods=["POST"])
	def api_traducir():
		data = request.get_json(silent=True)

		if not isinstance(data, dict):
			return respuesta_json({
				"ok": False,
				"error": "Solicitud inválida.",
			}, 400)

		texto = str(data.get("texto", "")).strip()
		direccion = str(data.get("direccion", "sp_ntl")).strip()

		if not texto:
			return respuesta_json({
				"ok": False,
				"error": "Escribe un texto para traducir.",
			}, 400)

		if direccion not in {"sp_ntl", "ntl_sp"}:
			return respuesta_json({
				"ok": False,
				"error": "Dirección de traducción inválida.",
			}, 400)

		if motor_error:
			return respuesta_json({
				"ok": False,
				"error": "El motor no pudo cargarse.",
				"detalle": motor_error,
			}, 500)

		if license_manager is None:
			return respuesta_json({
				"ok": False,
				"error": "El administrador de licencias no está disponible.",
			}, 500)

		try:
			license_manager.ensure_translation_allowed()

		except (daily_limit_error, invalid_license_error) as exc:
			status = license_manager.status()

			return respuesta_json({
				"ok": False,
				"error": str(exc),
				"license": licencia_a_dict(status),
			}, 403)

		try:
			with contextlib.redirect_stdout(io.StringIO()):
				if direccion == "ntl_sp":
					resultado = translate_ntl_to_sp(texto)
				else:
					resultado = translate_sp_to_ntl(texto)

			license_status = license_manager.register_translation()

			return respuesta_json({
				"ok": True,
				"entrada": texto,
				"direccion": direccion,
				"resultado": str(resultado or "").strip(),
				"license": licencia_a_dict(license_status),
			})

		except Exception as exc:
			return respuesta_json({
				"ok": False,
				"error": str(exc),
				"detalle": traceback.format_exc(),
			}, 500)
