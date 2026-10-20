"""Armado del caption que acompana a la foto en Telegram.

La hora se muestra en UTC-3 (Argentina, sin horario de verano) usando un
offset fijo: no depende de la base tzdata, que en Windows no siempre esta.
El limite de caption de Telegram es 1024 caracteres
(fuente: https://core.telegram.org/bots/api#sendphoto).
"""

from datetime import timedelta, timezone

from .modelos import EventoCamara

TZ_ARG = timezone(timedelta(hours=-3))
MAX_CAPTION = 1024


def armar_caption(evento: EventoCamara) -> str:
    local = evento.ts.astimezone(TZ_ARG)
    caption = (
        f"\U0001f4f7 {evento.nombre_camara}\n"
        f"Evento: {evento.tipo}\n"
        f"Canal: {evento.canal}\n"
        f"Hora: {local:%Y-%m-%d %H:%M:%S} (UTC-3)"
    )
    return caption[:MAX_CAPTION]
