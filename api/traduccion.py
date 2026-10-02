from __future__ import annotations

import contextlib
import io
import traceback

from flask import Flask, request

from .acceso_web import (
    current_client_id,
    ensure_translation_allowed,
    get_registered_translation,
    register_translation_once,
)
from .comunes import respuesta_json


def _access_dict(status) -> dict:
    return {
        "kind": status.kind,
        "valid": status.valid,
        "translations_used_today": status.translations_used_today,
        "translations_remaining_today": status.translations_remaining_today,
        "expires_on": status.expires_on,
        "days_remaining": status.days_remaining,
        "message": status.message,
        "unlimited": status.unlimited,
    }


def registrar_ruta_traduccion(
    app: Flask,
    license_manager,
    motor_error,
    translate_ntl_to_sp,
    translate_sp_to_ntl,
    daily_limit_error,
    invalid_license_error,
) -> None:
    @app.route("/api/traducir", methods=["POST"])
    def api_traducir():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return respuesta_json({"ok": False, "error": "Solicitud inválida."}, 400)

        texto = str(data.get("texto", "")).strip()
        direccion = str(data.get("direccion", "sp_ntl")).strip()
        if not texto:
            return respuesta_json({"ok": False, "error": "Escribe un texto para traducir."}, 400)
        if len(texto) > 5000:
            return respuesta_json({"ok": False, "error": "El texto supera el máximo de 5000 caracteres."}, 413)
        if direccion not in {"sp_ntl", "ntl_sp"}:
            return respuesta_json({"ok": False, "error": "Dirección de traducción inválida."}, 400)
        if motor_error:
            return respuesta_json({"ok": False, "error": "El motor no pudo cargarse."}, 500)

        # La licencia local autoriza únicamente al servidor. No concede acceso
        # ilimitado a cada navegador que visite el sitio.
        if license_manager is not None:
            try:
                server_access = license_manager.status()
            except Exception:
                return respuesta_json({
                    "ok": False,
                    "error": "No fue posible comprobar la licencia del servidor.",
                }, 503)

            if not server_access.valid:
                return respuesta_json({
                    "ok": False,
                    "error": "La licencia del servidor no es válida.",
                }, 503)

        client_id = current_client_id()
        request_id = str(
            request.headers.get("Idempotency-Key")
            or data.get("request_id")
            or ""
        ).strip()
        if not request_id or len(request_id) > 200:
            return respuesta_json({
                "ok": False,
                "error": "La solicitud no contiene un identificador válido.",
            }, 400)

        previous = get_registered_translation(client_id, request_id)
        if previous is not None:
            from .acceso_web import status
            return respuesta_json({
                "ok": True,
                "entrada": previous["input_text"],
                "direccion": previous["direction"],
                "resultado": previous["result_text"],
                "license": _access_dict(status(client_id)),
                "duplicate": True,
            })

        try:
            ensure_translation_allowed(client_id)
        except PermissionError as exc:
            from .acceso_web import status
            return respuesta_json({
                "ok": False,
                "error": str(exc),
                "license": _access_dict(status(client_id)),
            }, 403)

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                lineas = texto.splitlines()

                if len(lineas) > 1:
                    resultados = []

                    for linea in lineas:
                        expresion = linea.strip()

                        if not expresion:
                            resultados.append("")
                            continue

                        resultado_linea = (
                            translate_ntl_to_sp(expresion)
                            if direccion == "ntl_sp"
                            else translate_sp_to_ntl(expresion)
                        )
                        resultados.append(str(resultado_linea or "").strip())

                    resultado_texto = "\n".join(resultados).strip()
                else:
                    resultado = (
                        translate_ntl_to_sp(texto)
                        if direccion == "ntl_sp"
                        else translate_sp_to_ntl(texto)
                    )
                    resultado_texto = str(resultado or "").strip()

            access, counted = register_translation_once(
                client_id=client_id,
                request_id=request_id,
                input_text=texto,
                direction=direccion,
                result_text=resultado_texto,
            )

            return respuesta_json({
                "ok": True,
                "entrada": texto,
                "direccion": direccion,
                "resultado": resultado_texto,
                "license": _access_dict(access),
                "counted": counted,
            })

        except Exception as exc:
            return respuesta_json({
                "ok": False,
                "error": str(exc),
                "detalle": traceback.format_exc() if app.debug else None,
            }, 500)