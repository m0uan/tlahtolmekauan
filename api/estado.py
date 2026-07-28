from __future__ import annotations

from flask import Flask

from .comunes import licencia_a_dict, respuesta_json


def registrar_rutas_estado(app: Flask, license_manager) -> None:
	@app.route("/api/estado", methods=["GET"])
	def api_estado():
		if license_manager is None:
			return respuesta_json({
				"ok": False,
				"error": "El administrador de licencias no está disponible.",
			}, 500)

		status = license_manager.status()
		license_data = licencia_a_dict(status, incluir_dias=True)

		return respuesta_json({
			"ok": True,
			"motor": "tlahtolmekauan",
			"version": "v2.9-licencias-coherentes",
			"direcciones": ["sp_ntl", "ntl_sp"],
			**license_data,
		})

	@app.route("/api/identificador-equipo", methods=["GET"])
	def api_identificador_equipo():
		if license_manager is None:
			return respuesta_json({
				"ok": False,
				"error": "El administrador de licencias no está disponible.",
			}, 500)

		return respuesta_json({
			"ok": True,
			"machine_id": license_manager.machine_id,
		})
