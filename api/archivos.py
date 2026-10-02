from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory

from .comunes import respuesta_json


def registrar_rutas_archivos(app: Flask, base_dir: Path) -> None:
    @app.route(
        "/api/<path:ruta>",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    def api_ruta_no_encontrada(ruta: str):
        return respuesta_json(
            {
                "ok": False,
                "error": "Ruta no encontrada.",
            },
            404,
        )

    @app.route("/", defaults={"ruta": ""})
    @app.route("/<path:ruta>")
    def servir_archivo(ruta: str):
        ruta_limpia = ruta.strip("/")
        destino = base_dir / ruta_limpia

        # Raíz del sitio.
        if not ruta_limpia:
            return send_from_directory(base_dir, "index.html")

        # Carpetas como /lsm/ y /lsm/diccionario/ sirven su index.html.
        if destino.is_dir():
            return send_from_directory(destino, "index.html")

        # Archivos normales: CSS, JS, JSON, imágenes, etc.
        return send_from_directory(base_dir, ruta_limpia)