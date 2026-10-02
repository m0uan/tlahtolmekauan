# -*- coding: utf-8 -*-
"""
© Roberto Spíndola Barrón, 2026.
Todos los derechos reservados.

Sistema estructural de análisis lingüístico Náhuatl ↔ Español.
Módulo: [tonal_uan_xiu]
Versión: v1.0
Fecha: [23-05-2026]

Prohibida la reproducción, redistribución, extracción estructural,
ingeniería inversa, entrenamiento de modelos de inteligencia artificial
o reutilización no autorizada.
"""
# === Single-Folder Project Bootstrap (Android/PC) ===

import os, sys, json, csv, importlib, importlib.util, unicodedata, re, platform, subprocess
from pathlib import Path

# ---------- 1) Raíz del proyecto (carpeta única) ----------
ANDROID_DL = Path("/storage/emulated/0/Download")   # carpeta típica en Android
try:
	BASE_DIR = Path(_file_).resolve().parent		# carpeta del script actual
except Exception:
	BASE_DIR = Path.cwd()

# Usa Download en Android si existe, si no la carpeta del script
PROJECT_ROOT = ANDROID_DL if ANDROID_DL.exists() else BASE_DIR

# En modo carpeta única, TODO vive aquí:
ASSETS_DIR = PROJECT_ROOT   # imágenes (opcional)
BASES_DIR  = PROJECT_ROOT   # bases (py/json/csv)
PAGES_DIR  = PROJECT_ROOT   # otros .py

# Asegura importación por nombre desde la raíz
pr = str(PROJECT_ROOT)
if pr not in sys.path:
	sys.path.insert(0, pr)

# ---------- 2) Utilidad de rutas ----------
def candidate_paths(*names: str):
	"""
	Busca archivos exclusivamente en PROJECT_ROOT (carpeta única).
	Evita confusiones con copias en subcarpetas.
	"""
	for nm in names:
		yield PROJECT_ROOT / nm

# ---------- 3) Carga de módulos de datos (PY) + tablas (JSON/CSV) ----------
def _collect_str2str_dicts_from_module(mod):
	"""
	Extrae dicts[str->str] no vacíos definidos en el módulo.
	"""
	res = []
	if not mod: return res
	for name, val in getattr(mod, "_dict_", {}).items():
		if isinstance(val, dict) and val:
			ok = True
			for k, v in val.items():
				if not (isinstance(k, str) and isinstance(v, str)):
					ok = False; break
			if ok:
				res.append(val)
	return res

def _safe_import_by_file(pyfile: Path):
	"""
	Importa un archivo .py por ruta sin romper la app si falla.
	"""
	try:
		spec = importlib.util.spec_from_file_location(pyfile.stem, str(pyfile))
		mod  = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mod)  # type: ignore
		return mod
	except Exception:
		return None

def _merge_dicts(dicts):
	"""
	Fusiona lista de dicts str->str normalizando a NFC y añade clave en minúsculas.
	"""
	out = {}
	for d in dicts or []:
		for k, v in d.items():
			try:
				kn = unicodedata.normalize("NFC", str(k))
				vn = unicodedata.normalize("NFC", str(v))
				out[kn] = vn
				out[kn.lower()] = vn  # variante en minúsculas (lookup robusto)
			except Exception:
				pass
	return out

def _load_json_csv_pairs(es_key, ntl_key, stems_like):
	"""
	Carga múltiples JSON/CSV cuyo nombre base esté en 'stems_like'.
	- JSON dict: {es: ntl}
	- JSON list[dict]: usa columns es_key/ntl_key
	- CSV: usa header es_key/ntl_key
	"""
	found = []
	for stem in stems_like:
		# JSON
		for p in candidate_paths(f"{stem}.json"):
			if p.exists():
				try:
					data = json.loads(p.read_text(encoding="utf-8"))
					if isinstance(data, dict):
						found.append({str(k): str(v) for k, v in data.items()})
					elif isinstance(data, list):
						tmp = {}
						for row in data:
							if isinstance(row, dict) and es_key in row and ntl_key in row:
								tmp[str(row[es_key])] = str(row[ntl_key])
						if tmp: found.append(tmp)
				except Exception:
					pass
		# CSV
		for p in candidate_paths(f"{stem}.csv"):
			if p.exists():
				try:
					tmp = {}
					with p.open("r", encoding="utf-8") as f:
						reader = csv.DictReader(f)
						for row in reader:
							a = row.get(es_key); b = row.get(ntl_key)
							if a and b: tmp[str(a)] = str(b)
					if tmp: found.append(tmp)
				except Exception:
					pass
	return _merge_dicts(found)

def _load_py_family(stems):
	"""
	Intenta cargar módulos por nombre y por archivo (en PROJECT_ROOT) y
	extrae dicts[str->str] de cada uno.
	"""
	try:
		importlib.invalidate_caches()
	except Exception:
		pass

	dicts = []
	for stem in stems:
		# 1) Import por nombre (PROJECT_ROOT ya está en sys.path)
		try:
			mod = importlib.import_module(stem)
		except Exception:
			mod = None
		dicts += _collect_str2str_dicts_from_module(mod)

		# 2) Import explícito por archivo .py
		for p in candidate_paths(stem + ".py"):
			if p.exists():
				mod2 = _safe_import_by_file(p)
				dicts += _collect_str2str_dicts_from_module(mod2)

	return _merge_dicts(dicts)

# ---------- 4) Listas “whitelist” de nombres de bases ----------
ES_NTL_STEMS = [
	"sp_ntl_roots","sp_ntl","spanish_to_nahuatl",
	"sp_ntl_conj","es_ntl_conj","es_ntl_forms","es_ntl_db"
]
NTL_ES_STEMS = [
	"ntl_sp_roots","ntl_sp","nahuatl_to_spanish",
	"ntl_sp_conj","ntl_es_conj","ntl_es_forms","ntl_es_db"
]

# ---------- 5) Construye los diccionarios completos ----------
sp_ntl_py  = _load_py_family(ES_NTL_STEMS)
ntl_sp_py  = _load_py_family(NTL_ES_STEMS)
sp_ntl_tab = _load_json_csv_pairs("es",  "ntl", ES_NTL_STEMS)
ntl_sp_tab = _load_json_csv_pairs("ntl", "es",  NTL_ES_STEMS)

SP_NTL_FULL = {}
SP_NTL_FULL.update(sp_ntl_tab)
SP_NTL_FULL.update(sp_ntl_py)

NTL_SP_FULL = {}
NTL_SP_FULL.update(ntl_sp_tab)
NTL_SP_FULL.update(ntl_sp_py)

# ---------- 6) Partir en frases/palabras (protege multi-palabra) ----------
def _split_phrase_dict(d):
	phrases, words = {}, {}
	if not isinstance(d, dict): return phrases, words
	for k, v in d.items():
		if not isinstance(k, str) or not isinstance(v, str): continue
		kk = unicodedata.normalize("NFC", k)
		kk_low = kk.lower()
		if (" " in kk) or ("\u00A0" in kk): # NBSP también
			phrases[kk] = v; phrases[kk_low] = v
		else:
			words[kk] = v;   words[kk_low]   = v
	return phrases, words

SP_PH_K, SP_WD_K = _split_phrase_dict(SP_NTL_FULL)
NT_PH_K, NT_WD_K = _split_phrase_dict(NTL_SP_FULL)

# ---------- 7) Utilidades de archivos y GUI (opcional) ----------
def _run_python(script_name: str):
	"""
	Ejecuta otro .py que esté en PROJECT_ROOT (carpeta única).
	"""
	for p in candidate_paths(script_name):
		if p.exists():
			try:
				subprocess.Popen([sys.executable, str(p)], shell=False)
				return
			except Exception as e:
				try:
					import tkinter.messagebox as messagebox
					messagebox.showerror("Error", f"No se pudo ejecutar:\n{e}")
				except Exception:
					print("No se pudo ejecutar:", e)
				return
	try:
		import tkinter.messagebox as messagebox
		messagebox.showerror("Error", f"Script no encontrado: {script_name}")
	except Exception:
		print("Script no encontrado:", script_name)

def _open_pdf(pdf_name: str):
	for p in candidate_paths(pdf_name):
		if p.exists():
			try:
				os.startfile(str(p)); return	# Windows
			except AttributeError:
				try:
					if sys.platform == "darwin": subprocess.Popen(["open", str(p)])
					else: subprocess.Popen(["xdg-open", str(p)])
				except Exception as e:
					try:
						import tkinter.messagebox as messagebox
						messagebox.showerror("Error", f"No se pudo abrir:\n{e}")
					except Exception:
						print("No se pudo abrir:", e)
			return
	try:
		import tkinter.messagebox as messagebox
		messagebox.showerror("Error", f"PDF no encontrado: {pdf_name}")
	except Exception:
		print("PDF no encontrado:", pdf_name)

# Usar solo si tienes Tk importado en este archivo
def _load_icon(root):
	"""
	Establece icono: primero .ico (PC), si falla prueba .png (PC/Android).
	Busca únicamente en PROJECT_ROOT.
	"""
	# 1) .ico — Windows
	for p in candidate_paths("Opoch_tlAhtol_64px.ico","Opoch_tlAhtol.ico","app.ico"):
		if p.exists():
			try:
				root.iconbitmap(str(p)); return
			except Exception:
				pass
	# 2) .png — Android/macOS/Linux/PC fallback
	for p in candidate_paths("Opoch_tlAhtol_64px.png","Opoch_tlAhtol.png","app.png"):
		if p.exists():
			try:
				import tkinter as tk
				img = tk.PhotoImage(file=str(p))
				root.iconphoto(True, img)
				root._iconphoto_ref = img   # prevenir GC
				return
			except Exception:
				pass
	# Silencioso si no hay icono
# -*- coding: utf-8 -*-
from datetime import datetime

# Este programa convierte la fecha ingresada en sistema calendárico "tonalpOual - xiuhpOual".

complete_day_name = [
	"•zipaktli", "••ehekatl", "•••kalli", "••••ketzpalli", "|koatl", "|•mikiztli", "|••mazatl", "|•••tochtli", "|••••atl", "||itzkuintli", "||•ozomahtli", "||••malinalli", "||•••akatl",
	"•ozelotl", "••kuauhtli", "•••kozkakuauhtli", "••••olin", "|tekpatl", "|•kiauitl", "|••xochitl", "|•••zipaktli", "|••••ehekatl", "||kalli", "||•ketzpalli", "||••koatl", "||•••mikiztli",
	"•mazatl", "••tochtli", "•••atl", "••••itzkuintli", "|ozomahtli", "|•malinalli", "|••akatl", "|•••ozelotl", "|••••kuauhtli", "||kozkakuauhtli", "||•olin", "||••tekpatl", "||•••kiauitl",
	"•xochitl", "••zipaktli", "•••ehekatl", "••••kalli", "|ketzpalli", "|•koatl", "|••mikiztli", "|•••mazatl", "|••••tochtli", "||atl", "||•itzkuintli", "||••ozomahtli", "||•••malinalli",
	"•akatl", "••ozelotl", "•••kuauhtli", "••••kozkakuauhtli", "|olin", "|•tekpatl", "|••kiauitl", "|•••xochitl", "|••••zipaktli", "||ehekatl", "||•kalli", "||••ketzpalli", "||•••koatl",
	"•mikiztli", "••mazatl", "•••tochtli", "••••atl", "|itzkuintli", "|•ozomahtli", "|••malinalli", "|•••akatl", "|••••ozelotl", "||kuauhtli", "||•kozkakuauhtli", "||••olin", "||•••tekpatl",
	"•kiauitl", "••xochitl", "•••zipaktli", "••••ehekatl", "|kalli", "|•ketzpalli", "|••koatl", "|•••mikiztli", "|••••mazatl", "||tochtli", "||•atl", "||••itzkuintli", "||•••ozomahtli",
	"•malinalli", "••akatl", "•••ozelotl", "••••kuauhtli", "|kozkakuauhtli", "|•olin", "|••tekpatl", "|•••kiauitl", "|••••xochitl", "||zipaktli", "||•ehekatl", "||••kalli", "||•••ketzpalli",
	"•koatl", "••mikiztli", "•••mazatl", "••••tochtli", "|atl", "|•itzkuintli", "|••ozomahtli", "|•••malinalli", "|••••akatl", "||ozelotl", "||•kuauhtli", "||••kozkakuauhtli", "||•••olin",
	"•tekpatl", "••kiauitl", "•••xochitl", "••••zipaktli", "|ehekatl", "|•kalli", "|••ketzpalli", "|•••koatl", "|••••mikiztli", "||mazatl", "||•tochtli", "||••atl", "||•••itzkuintli",
	"•ozomahtli", "••malinalli", "•••akatl", "••••ozelotl", "|kuauhtli", "|•kozkakuauhtli", "|••olin", "|•••tekpatl", "|••••kiauitl", "||xochitl", "||•zipaktli", "||••ehekatl", "||•••kalli",
	"•ketzpalli", "••koatl", "•••mikiztli", "••••mazatl", "|tochtli", "|•atl", "|••itzkuintli", "|•••ozomahtli", "|••••malinalli", "||akatl", "||•ozelotl", "||••kuauhtli", "||•••kozkakuauhtli",
	"•olin", "••tekpatl", "•••kiauitl", "••••xochitl", "|zipaktli", "|•ehekatl", "|••kalli", "|•••ketzpalli", "|••••koatl", "||mikiztli", "||•mazatl", "||••tochtli", "||•••atl",
	"•itzkuintli", "••ozomahtli", "•••malinalli", "••••akatl", "|ozelotl", "|•kuauhtli", "|••kozkakuauhtli", "|•••olin", "|••••tekpatl", "||kiauitl", "||•xochitl", "||••zipaktli", "||•••ehekatl",
	"•kalli", "••ketzpalli", "•••koatl", "••••mikiztli", "|mazatl", "|•tochtli", "|••atl", "|•••itzkuintli", "|••••ozomahtli", "||malinalli", "||•akatl", "||••ozelotl", "||•••kuauhtli",
	"•kozkakuauhtli", "••olin", "•••tekpatl", "••••kiauitl", "|xochitl", "|•zipaktli", "|••ehekatl", "|•••kalli", "|••••ketzpalli", "||koatl", "||•mikiztli", "||••mazatl", "||•••tochtli",
	"•atl", "••itzkuintli", "•••ozomahtli", "••••malinalli", "|akatl", "|•ozelotl", "|••kuauhtli", "|•••kozkakuauhtli", "|••••olin", "||tekpatl", "||•kiauitl", "||••xochitl", "||•••zipaktli",
	"•ehekatl", "••kalli", "•••ketzpalli", "••••koatl", "|mikiztli", "|•mazatl", "|••tochtli", "|•••atl", "|••••itzkuintli", "||ozomahtli", "||•malinalli", "||••akatl", "||•••ozelotl",
	"•kuauhtli", "••kozkakuauhtli", "•••olin", "••••tekpatl", "|kiauitl", "|•xochitl", "|••zipaktli", "|•••ehekatl", "|••••kalli", "||ketzpalli", "||•koatl", "||••mikiztli", "||•••mazatl",
	"•tochtli", "••atl", "•••itzkuintli", "••••ozomahtli", "|malinalli", "|•akatl", "|••ozelotl", "|•••kuauhtli", "|••••kozkakuauhtli", "||olin", "||•tekpatl", "||••kiauitl", "||•••xochitl"
	]

complete_year_name = [
	"•tochtli", "••akatl", "•••tekpatl", "••••kalli", "|tochtli", "|•akatl", "|••tekpatl", "|•••kalli", "|••••tochtli", "||akatl", "||•tekpatl", "||••kalli", "||•••tochtli", 
	"•akatl", "••tekpatl", "•••kalli", "••••tochtli", "|akatl", "|•tekpatl", "|••kalli", "|•••tochtli", "|••••akatl", "||tekpatl", "||•kalli", "||••tochtli", "||•••akatl", 
	"•tekpatl", "••kalli", "•••tochtli", "••••akatl", "|tekpatl", "|•kalli", "|••tochtli", "|•••akatl", "|••••tekpatl", "||kalli", "||•tochtli", "||••akatl", "||•••tekpatl", 
	"•kalli", "••tochtli", "•••akatl", "••••tekpatl", "|kalli", "|•tochtli", "|••akatl", "|•••tekpatl", "|••••kalli", "||tochtli", "||•akatl", "||••tekpatl", "||•••kalli"
	]

def is_leap_year_julian(year):
	return year % 4 == 0

def is_leap_year_gregorian(year):
	return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def calculate_difference(ref_day, ref_month, ref_year, target_day, target_month, target_year):
	# Ajuste para el salto del calendario gregoriano
	calendar_jump = 10 if ref_year < 1582 and target_year >= 1582 else 0

	ref_date = datetime(ref_year, ref_month, ref_day)
	target_date = datetime(target_year, target_month, target_day)
	difference = (target_date - ref_date).days - calendar_jump

	leap_days = 0
	for year in range(ref_year, target_year + 1):
		if year < 1582 and is_leap_year_julian(year) or year >= 1582 and is_leap_year_gregorian(year):
			leap_days += 1

	difference += leap_days - 1  # Restando 1 para alinear correctamente los índices

	day_cycle = 260
	adjusted_difference = difference % day_cycle
	return adjusted_difference

def get_day_name(day, month, year):
	ref_day, ref_month, ref_year = 13, 8, 1521
	ref_day_index = 53  # Assuming "• Akatl" is the index 53
	day_difference = calculate_difference(ref_day, ref_month, ref_year, day, month, year)
	day_index = (ref_day_index + day_difference) % len(complete_day_name)
	return complete_day_name[day_index]

def get_year_name(year):
	base_year = -2  # Asumiendo que el año base "•tOchtli" corresponde a -2
	year_difference = year - base_year
	year_index = year_difference % len(complete_year_name)
	return complete_year_name[year_index]

def iniciar_interfaz():
	import tkinter as tk
	from tkinter import messagebox

	frame = tk.Tk()
	frame.title("anAuak tOnal uan xiu")

	try:
		frame.iconbitmap("Opoch_tlAhtol_64px.ico")
	except Exception:
		pass

	frame.config(bg="beige")
	frame.config(bd="25")
	frame.config(relief="sunken")

	label_day = tk.Label(frame, text="Day:")
	label_day.pack()
	entry_day = tk.Entry(frame)
	entry_day.pack()

	label_month = tk.Label(frame, text="Month:")
	label_month.pack()
	entry_month = tk.Entry(frame)
	entry_month.pack()

	label_year = tk.Label(frame, text="Year:")
	label_year.pack()
	entry_year = tk.Entry(frame)
	entry_year.pack()

	def calculate():
		day = int(entry_day.get())
		month = int(entry_month.get())
		year = int(entry_year.get())
		day_name = get_day_name(day, month, year)
		year_name = get_year_name(year)
		messagebox.showinfo("tlAmik", f"tOnal: {day_name}\nxiu: {year_name}")

	calculate_button = tk.Button(frame, text="Calculate", command=calculate)
	calculate_button.pack()
	frame.mainloop()


if __name__ == "__main__":
	iniciar_interfaz()
