from __future__ import annotations

from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

import logging
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "tlahtolmekauan.log"


def crear_logger(nombre: str = "tlahtolmekauan") -> Logger:
	logger = logging.getLogger(nombre)

	if logger.handlers:
		return logger

	logger.setLevel(logging.INFO)
	logger.propagate = False

	formato = logging.Formatter(
		"%(asctime)s | %(levelname)s | %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	archivo = RotatingFileHandler(
		LOG_FILE,
		maxBytes=2 * 1024 * 1024,
		backupCount=5,
		encoding="utf-8",
	)
	archivo.setLevel(logging.INFO)
	archivo.setFormatter(formato)

	consola = logging.StreamHandler(sys.stdout)
	consola.setLevel(logging.INFO)
	consola.setFormatter(formato)

	logger.addHandler(archivo)
	logger.addHandler(consola)

	return logger


logger = crear_logger()


def info(mensaje: str, *args, **kwargs) -> None:
	logger.info(mensaje, *args, **kwargs)


def warning(mensaje: str, *args, **kwargs) -> None:
	logger.warning(mensaje, *args, **kwargs)


def error(mensaje: str, *args, **kwargs) -> None:
	logger.error(mensaje, *args, **kwargs)


def debug(mensaje: str, *args, **kwargs) -> None:
	logger.debug(mensaje, *args, **kwargs)


def critical(mensaje: str, *args, **kwargs) -> None:
	logger.critical(mensaje, *args, **kwargs)


def registrar_excepcion(mensaje: str = "Excepción no controlada") -> None:
	logger.exception(mensaje)
