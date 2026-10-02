from __future__ import annotations

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import contextlib
import io
import json
import os
import socket
import sys
import threading
import traceback
import webbrowser

BASE_DIR = Path(__file__).resolve().parent
MOTOR_DIR = BASE_DIR / "motor"
HOST = "127.0.0.1"
START_PORT = 8875
PORT = START_PORT
URL = f"http://{HOST}:{PORT}"

os.chdir(BASE_DIR)
sys.path.insert(0, str(MOTOR_DIR))
try:
	from Nahuatl_Translator import translate_sp_to_ntl, translate_ntl_to_sp
	from license_manager import DailyLimitReached, InvalidLicense, get_license_manager

	LICENSE_MANAGER = get_license_manager()

	MOTOR_ERROR = None

except Exception:
	translate_sp_to_ntl = None
	translate_ntl_to_sp = None
	LICENSE_MANAGER = None
	MOTOR_ERROR = traceback.format_exc()


class Handler(SimpleHTTPRequestHandler):
	def end_headers(self) -> None:
		# Permite que index.html muestre un diagnóstico incluso si se abrió por error
		# como archivo local (file://). La traducción sigue requiriendo este servidor.
		self.send_header("Access-Control-Allow-Origin", "*")
		self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		self.send_header("Access-Control-Allow-Headers", "Content-Type")
		self.send_header("Cache-Control", "no-store")
		super().end_headers()

	def _json(self, payload: dict, status: int = 200) -> None:
		body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
		self.send_response(status)
		self.send_header("Content-Type", "application/json; charset=utf-8")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def do_OPTIONS(self) -> None:
		self.send_response(204)
		self.end_headers()

	def do_GET(self):
		path = urlparse(self.path).path

		if not path.startswith("/api/"):
			return super().do_GET()

		if path == "/api/estado":
			self._json({
				"ok": True,
				"motor": "tlahtolmekauan",
				"version": "v2.8-error-corregido",
				"direcciones": ["sp_ntl","ntl_sp"]
			})
			return

		if path == "/api/identificador-equipo":
			if LICENSE_MANAGER is None:
				self._json({"ok":False,"error":"El administrador de licencias no está disponible."},status=500)
				return
			self._json({"ok":True,"machine_id":LICENSE_MANAGER.machine_id})
			return

		if path == "/api/licencia":
			if LICENSE_MANAGER is None:
				self._json({"ok":False,"error":"El administrador de licencias no está disponible."},status=500)
				return
			status=LICENSE_MANAGER.status()
			self._json({"ok":True,"license":{
				"kind":status.kind,
				"valid":status.valid,
				"machine_id":status.machine_id,
				"translations_used_today":status.translations_used_today,
				"translations_remaining_today":status.translations_remaining_today,
				"expires_on":status.expires_on,
				"message":status.message,
				"unlimited":status.unlimited}})
			return

		self.send_error(404,"File not found")

	def do_POST(self) -> None:
		if urlparse(self.path).path != "/api/traducir":
			self._json({"ok": False, "error": "Ruta no encontrada."}, 404)
			return

		try:
			length = int(self.headers.get("Content-Length", "0"))
			raw = self.rfile.read(length).decode("utf-8")
			data = json.loads(raw or "{}")
		except Exception:
			self._json({"ok": False, "error": "Solicitud inválida."}, 400)
			return

		texto = str(data.get("texto", "")).strip()
		direccion = str(data.get("direccion", "sp_ntl")).strip()

		if not texto:
			self._json({"ok": False, "error": "Escribe un texto para traducir."}, 400)
			return

		if direccion not in {"sp_ntl", "ntl_sp"}:
			self._json({"ok": False, "error": "Dirección de traducción inválida."}, 400)
			return

		if MOTOR_ERROR:
			self._json({
				"ok": False,
				"error": "El motor no pudo cargarse.",
				"detalle": MOTOR_ERROR,
			}, 500)
			return

		if LICENSE_MANAGER is None:
			self._json({
				"ok": False,
				"error": "El administrador de licencias no está disponible."
			}, 500)
			return

		try:
			LICENSE_MANAGER.ensure_translation_allowed()
		except (DailyLimitReached, InvalidLicense) as exc:
			status = LICENSE_MANAGER.status()
			self._json({
				"ok": False,
				"error": str(exc),
				"license": {
					"kind": status.kind,
					"valid": status.valid,
					"translations_used_today": status.translations_used_today,
					"translations_remaining_today": status.translations_remaining_today,
					"expires_on": status.expires_on,
					"message": status.message,
					"unlimited": status.unlimited
				}
			}, 403)
			return

		try:
			with contextlib.redirect_stdout(io.StringIO()):
				if direccion == "ntl_sp":
					resultado = translate_ntl_to_sp(texto)
				else:
					resultado = translate_sp_to_ntl(texto)

			license_status = LICENSE_MANAGER.register_translation()

			self._json({
				"ok": True,
				"entrada": texto,
				"direccion": direccion,
				"resultado": str(resultado or "").strip(),
				"license": {
					"kind": license_status.kind,
					"valid": license_status.valid,
					"translations_used_today": license_status.translations_used_today,
					"translations_remaining_today": license_status.translations_remaining_today,
					"expires_on": license_status.expires_on,
					"message": license_status.message,
					"unlimited": license_status.unlimited
				}
			})
		except Exception as exc:
			self._json({
				"ok": False,
				"error": str(exc),
				"detalle": traceback.format_exc(),
			}, 500)


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
	URL = f"http://{HOST}:{PORT}"

	print("=" * 66)
	print("tlahtolmekauan")
	print(f"Sitio: {URL}")
	if PORT != START_PORT:
		print(f"El puerto {START_PORT} estaba ocupado; se usará {PORT}.")
	print("No cierres esta ventana mientras uses el traductor.")
	print("=" * 66)

	if MOTOR_ERROR:
		print()
		print("ADVERTENCIA: el servidor abrirá, pero el motor no pudo cargarse:")
		print(MOTOR_ERROR)

	threading.Timer(1.0, abrir_navegador).start()

	try:
		ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
	except KeyboardInterrupt:
		print("\nServidor detenido.")
