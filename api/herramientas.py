from __future__ import annotations

from datetime import datetime

from flask import request


def registrar_rutas_herramientas(
	app,
	get_day_name,
	get_year_name,
	descomponer_numero,
):

	@app.post("/api/tonal-uan-xiu")
	def tonal_uan_xiu():

		if (
			not callable(get_day_name)
			or not callable(get_year_name)
		):
			return {
				"ok": False,
				"error": (
					"tonal_uan_xiu no pudo cargarse "
					"en el servidor."
				),
			}, 503

		data = request.get_json(
			silent=True
		) or {}

		try:
			day = int(
				data.get("day")
			)

			month = int(
				data.get("month")
			)

			year = int(
				data.get("year")
			)

			datetime(
				year,
				month,
				day,
			)

		except (TypeError, ValueError):
			return {
				"ok": False,
				"error": "Ingresa una fecha válida.",
			}, 400

		try:
			tonal = get_day_name(
				day,
				month,
				year,
			)

			xiu = get_year_name(
				year
			)

		except Exception as error:
			app.logger.exception(
				"Error ejecutando tonal_uan_xiu"
			)

			return {
				"ok": False,
				"error": (
					"No se pudo calcular "
					f"tonal_uan_xiu: {error}"
				),
			}, 500

		return {
			"ok": True,
			"tonal": tonal,
			"xiu": xiu,
		}, 200


	@app.post("/api/poualyotl")
	def poualyotl():

		if not callable(
			descomponer_numero
		):
			return {
				"ok": False,
				"error": (
					"poualyotl no pudo cargarse "
					"en el servidor."
				),
			}, 503

		data = request.get_json(
			silent=True
		) or {}

		try:
			numero = int(
				data.get("numero")
			)

		except (TypeError, ValueError):
			return {
				"ok": False,
				"error": (
					"Ingresa sólo números enteros."
				),
			}, 400

		try:
			resultado = descomponer_numero(
				numero
			)

		except Exception as error:
			app.logger.exception(
				"Error ejecutando poualyotl"
			)

			return {
				"ok": False,
				"error": (
					"No se pudo calcular "
					f"poualyotl: {error}"
				),
			}, 500

		if (
			not isinstance(resultado, (tuple, list))
			or len(resultado) < 2
		):
			return {
				"ok": False,
				"error": (
					"poualyotl devolvió "
					"un resultado no reconocido."
				),
			}, 500

		simbolo = resultado[0]
		nombre = resultado[1]

		if simbolo == "Número fuera de rango":
			return {
				"ok": False,
				"error": simbolo,
			}, 400

		return {
			"ok": True,
			"simbolo": simbolo,
			"nombre": nombre,
		}, 200