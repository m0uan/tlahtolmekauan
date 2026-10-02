# Variables recomendadas en Railway

## Cuenta de propietario
- `OWNER_ACCESS_CODE`: código privado que escribirás para activar tu cuenta.
- `OWNER_SESSION_SECRET`: cadena larga y aleatoria distinta del código anterior. Mantiene firmada la sesión del propietario.
- `PAYMENT_DATA_DIR=/data/pagos`: úsala junto con un volumen persistente montado en `/data`.

## Bandeja y respaldo por correo electrónico
Los mensajes siempre se guardan en la bandeja (`sugerencias.jsonl`). Para recibir además una copia por correo configura:
- `SMTP_HOST`
- `SMTP_PORT` (normalmente `587` o `465`)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SUGGESTIONS_TO_EMAIL`
- Opcional: `SUGGESTIONS_FILE=/data/sugerencias.jsonl`

No incluyas valores secretos en el repositorio. Configúralos directamente en Railway.
