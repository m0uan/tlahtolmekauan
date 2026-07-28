# -*- coding: utf-8 -*-
"""Interfaz comercial del Traductor Español ↔ Náhuatl.

Estructura esperada del proyecto:

	tlahtolmekauan/
	├── traductor_app.py
	├── license_manager.py
	└── motor/
		├── __init__.py
		├── Nahuatl_Translator.py
		└── módulos y diccionarios del motor

La interfaz consume una traducción únicamente cuando el motor devuelve
un resultado.
"""
from __future__ import annotations

import importlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from license_manager import DailyLimitReached, InvalidLicense, get_license_manager

APP_TITLE = "Traductor Español ↔ Náhuatl"
PROJECT_DIR = Path(__file__).resolve().parent
MOTOR_DIR = PROJECT_DIR / "motor"


def load_engine():
	"""Carga el motor lingüístico desde la carpeta ``motor``.

	Se agregan al buscador de módulos tanto la carpeta principal como la
	carpeta ``motor``. Esto permite que el motor funcione aunque sus módulos
	internos todavía utilicen importaciones directas, por ejemplo::

		from MODIFIERS_SP_NTL import MODIFIERS

	y también cuando ya utilicen importaciones relativas del paquete.
	"""
	if not MOTOR_DIR.is_dir():
		raise ImportError(
			"No se encontró la carpeta del motor.\n\n"
			f"Ruta esperada: {MOTOR_DIR}"
		)

	engine_path = MOTOR_DIR / "Nahuatl_Translator.py"
	if not engine_path.is_file():
		raise ImportError(
			"No se encontró el archivo principal del motor.\n\n"
			f"Ruta esperada: {engine_path}"
		)

	for directory in (PROJECT_DIR, MOTOR_DIR):
		directory_text = str(directory)
		if directory_text not in sys.path:
			sys.path.insert(0, directory_text)

	importlib.invalidate_caches()

	try:
		return importlib.import_module("motor.Nahuatl_Translator")
	except Exception as error:
		raise ImportError(
			"No fue posible cargar motor.Nahuatl_Translator.\n"
			f"Detalle: {error}"
		) from error


class TranslatorApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title(APP_TITLE)
		self.geometry("900x650")
		self.minsize(760, 560)

		self.manager = get_license_manager()
		try:
			self.engine = load_engine()
		except Exception as exc:
			messagebox.showerror("Error al iniciar", str(exc), parent=self)
			self.destroy()
			raise

		self.direction = tk.StringVar(value="sp_ntl")
		self.license_text = tk.StringVar()
		self.status_text = tk.StringVar(value="Listo.")

		self._build_menu()
		self._build_ui()
		self.refresh_license_display()

	def _build_menu(self) -> None:
		menu = tk.Menu(self)

		license_menu = tk.Menu(menu, tearoff=False)
		license_menu.add_command(label="Activar licencia…", command=self.activate_license)
		license_menu.add_command(label="Ver estado", command=self.show_license_status)
		license_menu.add_separator()
		license_menu.add_command(label="Mostrar identificador del equipo", command=self.show_machine_id)
		menu.add_cascade(label="Licencia", menu=license_menu)

		help_menu = tk.Menu(menu, tearoff=False)
		help_menu.add_command(label="Acerca del Traductor", command=self.show_about)
		menu.add_cascade(label="Ayuda", menu=help_menu)

		self.config(menu=menu)

	def _build_ui(self) -> None:
		root = ttk.Frame(self, padding=18)
		root.pack(fill="both", expand=True)
		root.columnconfigure(0, weight=1)
		root.rowconfigure(3, weight=1)
		root.rowconfigure(6, weight=1)

		header = ttk.Frame(root)
		header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
		header.columnconfigure(0, weight=1)
		ttk.Label(header, text=APP_TITLE, font=("TkDefaultFont", 16, "bold")).grid(
			row=0, column=0, sticky="w"
		)
		ttk.Label(header, textvariable=self.license_text, justify="right").grid(
			row=0, column=1, sticky="e"
		)

		directions = ttk.LabelFrame(root, text="Sentido de traducción", padding=10)
		directions.grid(row=1, column=0, sticky="ew", pady=(0, 10))
		ttk.Radiobutton(
			directions,
			text="Español → Náhuatl",
			variable=self.direction,
			value="sp_ntl",
			command=self._update_labels,
		).pack(side="left", padx=(0, 24))
		ttk.Radiobutton(
			directions,
			text="Náhuatl → Español",
			variable=self.direction,
			value="ntl_sp",
			command=self._update_labels,
		).pack(side="left")

		self.input_label = ttk.Label(root, text="Texto en español")
		self.input_label.grid(row=2, column=0, sticky="w")
		self.input_text = tk.Text(root, height=8, wrap="word", undo=True)
		self.input_text.grid(row=3, column=0, sticky="nsew", pady=(4, 10))

		controls = ttk.Frame(root)
		controls.grid(row=4, column=0, sticky="ew", pady=(0, 10))
		ttk.Button(controls, text="Traducir", command=self.translate).pack(side="left")
		ttk.Button(controls, text="Limpiar", command=self.clear_fields).pack(side="left", padx=8)
		ttk.Button(controls, text="Copiar resultado", command=self.copy_result).pack(side="left")
		ttk.Button(controls, text="Activar licencia", command=self.activate_license).pack(side="right")

		self.output_label = ttk.Label(root, text="Resultado en Náhuatl")
		self.output_label.grid(row=5, column=0, sticky="w")
		self.output_text = tk.Text(root, height=8, wrap="word", state="disabled")
		self.output_text.grid(row=6, column=0, sticky="nsew", pady=(4, 10))

		ttk.Separator(root).grid(row=7, column=0, sticky="ew", pady=(2, 8))
		ttk.Label(root, textvariable=self.status_text).grid(row=8, column=0, sticky="w")

		self.bind("<Control-Return>", lambda _event: self.translate())
		self.input_text.focus_set()

	def _update_labels(self) -> None:
		if self.direction.get() == "sp_ntl":
			self.input_label.config(text="Texto en español")
			self.output_label.config(text="Resultado en Náhuatl")
		else:
			self.input_label.config(text="Texto en Náhuatl")
			self.output_label.config(text="Resultado en español")

	def refresh_license_display(self) -> None:
		status = self.manager.status()
		if not status.valid:
			self.license_text.set(f"Licencia inválida\n{status.message}")
		elif status.kind == "free":
			self.license_text.set(
				"Licencia gratuita\n"
				f"Disponibles: {status.translations_remaining_today} de 10"
			)
		else:
			detail = f"Licencia {status.label.lower()}"
			if status.days_remaining is not None:
				unit = "día" if status.days_remaining == 1 else "días"
				detail += f"\nQuedan: {status.days_remaining} {unit}"
			elif status.expires_on:
				detail += f"\nVence: {status.expires_on}"
			else:
				detail += "\nUso ilimitado"
			self.license_text.set(detail)

	def _set_output(self, text: str) -> None:
		self.output_text.config(state="normal")
		self.output_text.delete("1.0", "end")
		self.output_text.insert("1.0", text)
		self.output_text.config(state="disabled")

	def translate(self) -> None:
		source = self.input_text.get("1.0", "end").strip()
		if not source:
			messagebox.showinfo("Texto requerido", "Escribe el texto que deseas traducir.", parent=self)
			return

		try:
			# La autorización se comprueba antes de llamar al motor.
			# El consumo se registra únicamente después de obtener un resultado válido.
			self.manager.ensure_translation_allowed()
			if self.direction.get() == "sp_ntl":
				result = self.engine.translate_sp_to_ntl_licensed(source)
			else:
				result = self.engine.translate_ntl_to_sp_licensed(source)
		except DailyLimitReached as exc:
			self.refresh_license_display()
			self.status_text.set("Límite gratuito alcanzado.")
			answer = messagebox.askyesno(
				"Límite diario alcanzado",
				f"{exc}\n\n¿Deseas seleccionar ahora un archivo de licencia?",
				parent=self,
			)
			if answer:
				self.activate_license()
			return
		except InvalidLicense as exc:
			self.refresh_license_display()
			messagebox.showerror("Licencia inválida", str(exc), parent=self)
			return
		except Exception as exc:
			messagebox.showerror("No fue posible traducir", str(exc), parent=self)
			self.status_text.set("La traducción no pudo completarse.")
			return

		result_text = str(result or "").strip()
		if not result_text:
			self._set_output("No se obtuvo una traducción.")
			self.status_text.set("No se obtuvo una traducción; no se consumió el cupo.")
			return

		self._set_output(result_text)
		self.manager.register_translation()
		self.refresh_license_display()
		self.status_text.set("Traducción completada.")

	def activate_license(self) -> None:
		path = filedialog.askopenfilename(
			title="Seleccionar licencia",
			filetypes=(("Licencia JSON", "*.json"), ("Todos los archivos", "*.*")),
			parent=self,
		)
		if not path:
			return
		try:
			status = self.manager.install_license(path)
		except (InvalidLicense, OSError) as exc:
			self.refresh_license_display()
			messagebox.showerror("No se pudo activar", str(exc), parent=self)
			return

		self.refresh_license_display()
		detail = f"Licencia {status.label.lower()} activada correctamente."
		if status.expires_on:
			detail += f"\nVence: {status.expires_on}"
		if status.days_remaining is not None:
			unit = "día" if status.days_remaining == 1 else "días"
			detail += f"\nQuedan: {status.days_remaining} {unit}"
		self.status_text.set("Licencia activada.")
		messagebox.showinfo("Activación completada", detail, parent=self)

	def show_license_status(self) -> None:
		messagebox.showinfo("Estado de la licencia", self.manager.user_summary(), parent=self)

	def show_machine_id(self) -> None:
		machine_id = self.manager.machine_id
		self.clipboard_clear()
		self.clipboard_append(machine_id)
		messagebox.showinfo(
			"Identificador del equipo",
			"Envía este identificador al solicitar una licencia.\n\n"
			f"{machine_id}\n\nSe copió al portapapeles.",
			parent=self,
		)

	def show_about(self) -> None:
		window = tk.Toplevel(self)
		window.title("Acerca del Traductor")
		window.geometry("720x560")
		window.transient(self)
		window.grab_set()

		frame = ttk.Frame(window, padding=14)
		frame.pack(fill="both", expand=True)
		text = tk.Text(frame, wrap="word", padx=10, pady=10)
		text.pack(fill="both", expand=True)
		text.insert("1.0", self.engine.ABOUT_TRANSLATOR_TEXT)
		text.config(state="disabled")
		ttk.Button(frame, text="Cerrar", command=window.destroy).pack(pady=(10, 0))

	def clear_fields(self) -> None:
		self.input_text.delete("1.0", "end")
		self._set_output("")
		self.status_text.set("Listo.")
		self.input_text.focus_set()

	def copy_result(self) -> None:
		text = self.output_text.get("1.0", "end").strip()
		if not text:
			return
		self.clipboard_clear()
		self.clipboard_append(text)
		self.status_text.set("Resultado copiado.")


def main() -> None:
	app = TranslatorApp()
	app.mainloop()


if __name__ == "__main__":
	main()
