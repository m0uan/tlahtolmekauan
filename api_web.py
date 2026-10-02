from __future__ import annotations

from pathlib import Path

import os
import importlib.util
import socket
import sys
import threading
import traceback
import webbrowser
import time

from flask import Flask, g, request
from werkzeug.exceptions import HTTPException
from api.acceso_web import set_client_cookie

from config import HOST, PORT
from api.archivos import registrar_rutas_archivos
from api.estado import registrar_rutas_estado
from api.herramientas import registrar_rutas_herramientas
from api.licencia import registrar_rutas_licencia
from api.pagos import registrar_rutas_pagos
from api.propietario import registrar_ruta_propietario
from api.traduccion import registrar_ruta_traduccion
from api.sugerencias import registrar_ruta_sugerencias
from utils.logger import logger


BASE_DIR = Path(__file__).resolve().parent
MOTOR_DIR = BASE_DIR / "motor"
START_PORT = PORT
BROWSER_HOST = "127.0.0.1"

os.chdir(BASE_DIR)

if str(MOTOR_DIR) not in sys.path:
	sys.path.insert(0, str(MOTOR_DIR))


MOTOR_ERROR = None
TOOLS_ERROR = None
LICENSE_ERROR = None

translate_sp_to_ntl = None
translate_ntl_to_sp = None

get_day_name = None
get_year_name = None
descomponer_numero = None

LICENSE_MANAGER = None


class DailyLimitReached(Exception):
	pass


class InvalidLicense(Exception):
	pass


# ============================================================
# MOTOR DE TRADUCCIÓN
# ============================================================

try:
	motor_file = MOTOR_DIR / "Nahuatl_Translator.py"
	if not motor_file.is_file():
		raise FileNotFoundError(
			f"No existe el motor de traducción requerido: {motor_file}"
		)

	spec = importlib.util.spec_from_file_location(
		"tlahtolmekauan_nahuatl_translator",
		motor_file,
	)
	if spec is None or spec.loader is None:
		raise ImportError(
			f"No se pudo preparar la carga del motor: {motor_file}"
		)

	motor_mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(motor_mod)

	translate_ntl_to_sp = motor_mod.translate_ntl_to_sp
	translate_sp_to_ntl = motor_mod.translate_sp_to_ntl

	logger.info("Motor cargado desde: %s", motor_file)
except Exception:
	MOTOR_ERROR = traceback.format_exc()


# ============================================================
# CARGA DIRECTA DE MÓDULOS DESDE motor/
# ============================================================

def _cargar_modulo_motor(nombre_modulo: str, nombre_archivo: str):
	ruta = MOTOR_DIR / nombre_archivo

	if not ruta.is_file():
		raise FileNotFoundError(
			f"No existe el módulo requerido: {ruta}"
		)

	spec = importlib.util.spec_from_file_location(
		nombre_modulo,
		ruta,
	)

	if spec is None or spec.loader is None:
		raise ImportError(
			f"No se pudo preparar la carga de {ruta}"
		)

	modulo = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(modulo)

	return modulo


# ============================================================
# tonal_uan_xiu
# ============================================================

try:
	_tonal_mod = _cargar_modulo_motor(
		"tlahtolmekauan_tonal_uan_xiu",
		"tOnal_uan_xiu.py",
	)

	get_day_name = _tonal_mod.get_day_name
	get_year_name = _tonal_mod.get_year_name

except Exception:
	TOOLS_ERROR = (
		"tonal_uan_xiu:\n"
		+ traceback.format_exc()
	)


# ============================================================
# poualyotl
# ============================================================

try:
	_poualyotl_mod = _cargar_modulo_motor(
		"tlahtolmekauan_poualyotl",
		"pouAlyotl.py",
	)

	descomponer_numero = _poualyotl_mod.descomponer_numero

except Exception:
	poualyotl_error = (
		"poualyotl:\n"
		+ traceback.format_exc()
	)

	if TOOLS_ERROR:
		TOOLS_ERROR += "\n" + poualyotl_error
	else:
		TOOLS_ERROR = poualyotl_error


# ============================================================
# LICENCIA
# ============================================================

try:
	from license_manager import (
		DailyLimitReached,
		InvalidLicense,
		get_license_manager,
	)

	LICENSE_MANAGER = get_license_manager()

except Exception:
	LICENSE_ERROR = traceback.format_exc()


# ============================================================
# FLASK
# ============================================================

app = Flask(
	__name__,
	static_folder=None,
)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


if MOTOR_ERROR:
	logger.warning(
		"El motor de traducción no pudo cargarse:\n%s",
		MOTOR_ERROR,
	)

if TOOLS_ERROR:
	logger.warning(
		"Una o más herramientas no pudieron cargarse:\n%s",
		TOOLS_ERROR,
	)

if LICENSE_ERROR:
	logger.warning(
		"El gestor de licencia no pudo cargarse:\n%s",
		LICENSE_ERROR,
	)


@app.get("/api/salud")
def salud():
	return {
		"ok": True,
		"nombre": "tlahtolmekauan",
		"mensaje": "Servidor funcionando correctamente.",
		"herramientas": {
			"tonal uan xiu": (
				callable(get_day_name)
				and callable(get_year_name)
			),
			"poualyotl": callable(descomponer_numero),
		},
	}, 200


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
	set_client_cookie(response)

	response.headers["Cache-Control"] = "no-store"

	inicio = getattr(
		g,
		"inicio_peticion",
		None,
	)

	if inicio is not None:
		tiempo_txt = (
			f"{time.perf_counter() - inicio:.3f} s"
		)
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

	if isinstance(error, HTTPException):
		return error

	logger.exception(
		"Error no controlado en %s %s",
		request.method,
		request.path,
	)

	return {
		"ok": False,
		"error": "Error interno del servidor.",
	}, 500


# ============================================================
# REGISTRO DE RUTAS
# ============================================================

registrar_rutas_estado(app)

registrar_rutas_herramientas(
	app,
	get_day_name,
	get_year_name,
	descomponer_numero,
)

registrar_rutas_licencia(
	app,
	LICENSE_MANAGER,
	InvalidLicense,
)

registrar_ruta_traduccion(
	app,
	LICENSE_MANAGER,
	MOTOR_ERROR,
	translate_ntl_to_sp,
	translate_sp_to_ntl,
	DailyLimitReached,
	InvalidLicense,
)

registrar_rutas_pagos(app)

registrar_ruta_propietario(
	app,
	BASE_DIR,
)

registrar_ruta_sugerencias(
	app,
	BASE_DIR,
)

registrar_rutas_archivos(
	app,
	BASE_DIR,
)


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

def encontrar_puerto_libre(
	inicio: int = START_PORT,
	intentos: int = 50,
) -> int:

	for candidato in range(
		inicio,
		inicio + intentos,
	):

		with socket.socket(
			socket.AF_INET,
			socket.SOCK_STREAM,
		) as sock:

			try:
				sock.bind(
					(
						HOST,
						candidato,
					)
				)

			except OSError:
				continue

			return candidato

	raise RuntimeError(
		"No se encontró un puerto disponible."
	)


def abrir_navegador() -> None:
	webbrowser.open(URL)


if __name__ == "__main__":

	PORT = encontrar_puerto_libre()

	URL = (
		f"http://{BROWSER_HOST}:{PORT}"
	)

	logger.info("=" * 66)
	logger.info("tlahtolmekauan")
	logger.info("Sitio: %s", URL)

	if PORT != START_PORT:
		logger.info(
			"El puerto %s estaba ocupado; se usará %s.",
			START_PORT,
			PORT,
		)

	logger.info(
		"No cierres esta ventana mientras uses el traductor."
	)

	logger.info("=" * 66)

	if MOTOR_ERROR:
		logger.warning(
			"El servidor abrirá, pero el motor no pudo cargarse:\n%s",
			MOTOR_ERROR,
		)

	if TOOLS_ERROR:
		logger.warning(
			"Herramientas no cargadas:\n%s",
			TOOLS_ERROR,
		)

	threading.Timer(
		1.0,
		abrir_navegador,
	).start()

	from waitress import serve

	try:
		serve(
			app,
			host=HOST,
			port=PORT,
			threads=8,
		)

	except KeyboardInterrupt:
		logger.info(
			"Servidor detenido."
		)