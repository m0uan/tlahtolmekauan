from __future__ import annotations

from flask import jsonify


def respuesta_json(payload: dict, status: int = 200):
	return jsonify(payload), status


def licencia_a_dict(status, incluir_dias: bool = False) -> dict:
	payload = {
		"kind": status.kind,
		"valid": status.valid,
		"machine_id": status.machine_id,
		"translations_used_today": status.translations_used_today,
		"translations_remaining_today": status.translations_remaining_today,
		"expires_on": status.expires_on,
		"message": status.message,
		"unlimited": status.unlimited,
	}

	if incluir_dias:
		payload["days_remaining"] = status.days_remaining

	return payload
