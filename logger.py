from __future__ import annotations

from pathlib import Path

import logging
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "tlahtolmekauan.log"


def crear_logger(nombre: str = "tlahtolmekauan") -> logging.Logger:
	logger = logging.getLogger(nombre)

	# Evita agregar manejadores duplicados
	if logger.handlers:
		return logger

	logger.setLevel(logging.INFO)

	formatter = logging.Formatter(
		"%(asctime)s | %(levelname)s | %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	file_handler = logging.FileHandler(
		LOG_FILE,
		encoding="utf-8",
	)

	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(formatter)

	console_handler = logging.StreamHandler(sys.stdout)

	console_handler.setLevel(logging.INFO)
	console_handler.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(console_handler)

	logger.propagate = False

	return logger


logger = crear_logger()


def info(mensaje: str):
	logger.info(mensaje)


def warning(mensaje: str):
	logger.warning(mensaje)


def error(mensaje: str):
	logger.error(mensaje)


def debug(mensaje: str):
	logger.debug(mensaje)


def critical(mensaje: str):
	logger.critical(mensaje)


def registrar_excepcion(mensaje: str):
	logger.exception(mensaje)