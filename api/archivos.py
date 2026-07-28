from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory

from .comunes import respuesta_json


def registrar_rutas_archivos(app: Flask, base_dir: Path) -> None:
	@app.route("/api/<path:ruta>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
	def api_ruta_no_encontrada(ruta: str):
		return respuesta_json({
			"ok": False,
			"error": "Ruta no encontrada.",
		}, 404)

	@app.route("/", defaults={"ruta": "index.html"})
	@app.route("/<path:ruta>")
	def servir_archivo(ruta: str):
		return send_from_directory(base_dir, ruta)
