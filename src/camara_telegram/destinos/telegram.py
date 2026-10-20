"""Destino Telegram: envia la foto del evento con ``sendPhoto``.

API oficial (https://core.telegram.org/bots/api#sendphoto):
``POST https://api.telegram.org/bot<token>/sendPhoto`` con
``multipart/form-data`` (chat_id, photo, caption <= 1024). La respuesta es
JSON con ``ok`` y ``description``.

El token jamas se incluye en logs ni mensajes de error: las excepciones solo
llevan el ``description`` que devuelve Telegram.
"""

import time
from collections.abc import Callable

import httpx

from ..mensaje import MAX_CAPTION
from ..reintentos import ReintentosAgotados, con_reintentos


class ErrorTelegram(Exception):
    """Telegram rechazo el envio (4xx, ok=false) o se agotaron los reintentos."""


class _FalloTransitorio(Exception):
    """Error de red o 5xx/429: entra en la politica de reintentos."""


class TelegramDestino:
    def __init__(
        self,
        token: str,
        chat_id: str,
        base_url: str = "https://api.telegram.org",
        cliente: httpx.Client | None = None,
        intentos: int = 3,
    ) -> None:
        self._url = f"{base_url}/bot{token}/sendPhoto"
        self._chat_id = chat_id
        self._cliente = cliente or httpx.Client(timeout=30)
        self._intentos = intentos

    def enviar_foto(
        self, foto: bytes, caption: str, esperar: Callable[[float], None] = time.sleep
    ) -> int:
        """Envia la foto y devuelve el ``message_id`` asignado."""

        def llamada() -> int:
            try:
                resp = self._cliente.post(
                    self._url,
                    data={"chat_id": self._chat_id, "caption": caption[:MAX_CAPTION]},
                    files={"photo": ("evento.jpg", foto, "image/jpeg")},
                )
            except httpx.HTTPError as e:
                raise _FalloTransitorio(str(e)) from e
            datos = self._json(resp)
            if resp.status_code == 200 and datos.get("ok"):
                return int(datos["result"]["message_id"])
            desc = str(datos.get("description") or f"HTTP {resp.status_code}")
            if resp.status_code in (429,) or resp.status_code >= 500:
                raise _FalloTransitorio(desc)
            raise ErrorTelegram(desc)

        try:
            return con_reintentos(
                llamada, intentos=self._intentos, esperar=esperar, recuperables=(_FalloTransitorio,)
            )
        except ReintentosAgotados as e:
            raise ErrorTelegram(str(e.ultimo_error)) from e

    @staticmethod
    def _json(resp: httpx.Response) -> dict:
        try:
            datos = resp.json()
        except ValueError:
            return {}
        return datos if isinstance(datos, dict) else {}
