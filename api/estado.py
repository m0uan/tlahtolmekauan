from __future__ import annotations

from flask import Flask

from .acceso_web import current_client_id, status
from .comunes import respuesta_json


def registrar_rutas_estado(app: Flask) -> None:
    @app.route("/api/estado", methods=["GET"])
    def api_estado():
        # El estado visible pertenece al navegador actual. La licencia local
        # del servidor solo autoriza la instalación y nunca debe heredarse
        # a los visitantes.
        client_id = current_client_id()
        access = status(client_id)

        return respuesta_json({
            "ok": True,
            "motor": "tlahtolmekauan",
            "version": "v3.0-mercado-pago-multiusuario",
            "direcciones": ["sp_ntl", "ntl_sp"],
            "kind": access.kind,
            "valid": access.valid,
            "translations_used_today": access.translations_used_today,
            "translations_remaining_today": access.translations_remaining_today,
            "expires_on": access.expires_on,
            "days_remaining": access.days_remaining,
            "message": access.message,
            "unlimited": access.unlimited,
            "plan_id": getattr(access, "plan_id", None),
            "email": getattr(access, "email", None),
        })

    @app.route("/api/identificador-equipo", methods=["GET"])
    def api_identificador_equipo():
        return respuesta_json({
            "ok": True,
            "machine_id": current_client_id(),
            "message": "Identificador de este navegador.",
        })
