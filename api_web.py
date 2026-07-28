from __future__ import annotations

from pathlib import Path

import os
import socket
import sys
import threading
import traceback
import webbrowser
import time

from flask import Flask, g, request
from waitress import serve

from config import HOST, PORT
from api.archivos import registrar_rutas_archivos
from api.estado import registrar_rutas_estado
from api.licencia import registrar_rutas_licencia
from api.traduccion import registrar_ruta_traduccion
from utils.logger import logger


BASE_DIR = Path(__file__).resolve().parent
MOTOR_DIR = BASE_DIR / "motor"
START_PORT = PORT
BROWSER_HOST = "127.0.0.1"

os.chdir(BASE_DIR)
sys.path.insert(0, str(MOTOR_DIR))


try:
	from Nahuatl_Translator import (
		translate_ntl_to_sp,
		translate_sp_to_ntl,
	)
	from license_manager import (
		DailyLimitReached,
		InvalidLicense,
		get_license_manager,
	)

	LICENSE_MANAGER = get_license_manager()
	MOTOR_ERROR = None

except Exception:
	translate_sp_to_ntl = None
	translate_ntl_to_sp = None
	LICENSE_MANAGER = None
	MOTOR_ERROR = traceback.format_exc()

	class DailyLimitReached(Exception):
		pass

	class InvalidLicense(Exception):
		pass


app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.before_request
def registrar_peticion() -> None:
	g.inicio_peticion = time.perf_counter()
	logger.info(
		"%s | %s %s",
		request.remote_addr,
		request.method,
		request.path,
	)


@app.after_request
def agregar_encabezados(response):
	response.headers["Access-Control-Allow-Origin"] = "*"
	response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
	response.headers["Access-Control-Allow-Headers"] = "Content-Type"
	response.headers["Cache-Control"] = "no-store"

	inicio = getattr(g, "inicio_peticion", None)

	if inicio is not None:
		tiempo_txt = f"{time.perf_counter() - inicio:.3f} s"
	else:
		tiempo_txt = "---"

	logger.info(
		"%s | %s | %s | %s | %s",
		request.remote_addr,
		request.method,
		response.status_code,
		tiempo_txt,
		request.path,
	)

	return response


@app.errorhandler(Exception)
def registrar_error_no_controlado(error):
	logger.exception(
		"Error no controlado en %s %s",
		request.method,
		request.path,
	)

	return {
		"ok": False,
		"error": "Error interno del servidor.",
	}, 500


registrar_rutas_estado(app, LICENSE_MANAGER)
registrar_rutas_licencia(app, LICENSE_MANAGER, InvalidLicense)
registrar_ruta_traduccion(
	app,
	LICENSE_MANAGER,
	MOTOR_ERROR,
	translate_ntl_to_sp,
	translate_sp_to_ntl,
	DailyLimitReached,
	InvalidLicense,
)
registrar_rutas_archivos(app, BASE_DIR)


def encontrar_puerto_libre(inicio: int = START_PORT, intentos: int = 50) -> int:
	for candidato in range(inicio, inicio + intentos):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.bind((HOST, candidato))
			except OSError:
				continue
			return candidato

	raise RuntimeError("No se encontró un puerto disponible.")


def abrir_navegador() -> None:
	webbrowser.open(URL)


if __name__ == "__main__":
	PORT = encontrar_puerto_libre()
	URL = f"http://{BROWSER_HOST}:{PORT}"

	logger.info("=" * 66)
	logger.info("tlahtolmekauan")
	logger.info("Sitio: %s", URL)

	if PORT != START_PORT:
		logger.info(
			"El puerto %s estaba ocupado; se usará %s.",
			START_PORT,
			PORT,
		)

	logger.info("No cierres esta ventana mientras uses el traductor.")
	logger.info("=" * 66)

	if MOTOR_ERROR:
		logger.warning(
			"El servidor abrirá, pero el motor no pudo cargarse:\n%s",
			MOTOR_ERROR,
		)

	threading.Timer(1.0, abrir_navegador).start()

	try:
		serve(
			app,
			host=HOST,
			port=PORT,
			threads=8,
		)
	except KeyboardInterrupt:
		logger.info("Servidor detenido.")
