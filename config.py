# config.py

from pathlib import Path

# ===========================
# Información de la aplicación
# ===========================

APP_NAME = "tlahtolmekauan"
APP_VERSION = "2.0.0"

# ===========================
# Servidor
# ===========================

HOST = "0.0.0.0"
PORT = 8875

# ===========================
# Flask
# ===========================

DEBUG = False

# ===========================
# Directorios
# ===========================

ROOT = Path(__file__).resolve().parent

STATIC_FOLDER = ROOT / "static"
TEMPLATE_FOLDER = ROOT / "templates"

DATA_FOLDER = ROOT / "data"

LOG_FOLDER = ROOT / "logs"

# ===========================
# Licencias
# ===========================

LICENSE_FILE = ROOT / "licencia.json"

# ===========================
# Traducción
# ===========================

DEFAULT_DIRECTION = "sp_ntl"

MAX_TEXT_LENGTH = 5000

# ===========================
# Logging
# ===========================

LOG_LEVEL = "INFO"