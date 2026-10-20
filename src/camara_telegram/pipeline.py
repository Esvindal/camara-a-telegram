"""Pipeline: evento activo -> snapshot -> caption -> destino -> registro."""

import logging
import time
from collections.abc import Callable
from typing import Protocol

import httpx

from .almacen.registro import RegistroEventos
from .enfriamiento import Enfriador
from .fuentes.base import FuenteEventos
from .mensaje import armar_caption
from .modelos import EventoCamara

log = logging.getLogger(__name__)


class Destino(Protocol):
    """Lo minimo que el pipeline necesita de un destino (Telegram, consola...)."""

    def enviar_foto(
        self, foto: bytes, caption: str, esperar: Callable[[float], None] = time.sleep
    ) -> int: ...


class Pipeline:
    def __init__(
        self,
        fuente: FuenteEventos,
        destino: Destino,
        registro: RegistroEventos,
        enfriador_segundos: float = 60.0,
        ahora: Callable[[], float] = time.monotonic,
        max_eventos: int | None = None,
    ) -> None:
        self._fuente = fuente
        self._destino = destino
        self._registro = registro
        self._enfriador = Enfriador(enfriador_segundos, ahora=ahora)
        self._max = max_eventos

    def correr(self, max_eventos: int | None = None) -> int:
        """Procesa eventos activos; devuelve cuantos se notificaron."""
        limite = max_eventos if max_eventos is not None else self._max
        procesados = 0
        for i, evento in enumerate(self._fuente.iterar_eventos()):
            if limite is not None and i >= limite:
                break
            if not evento.activo:
                log.debug("evento inactivo ignorado: %s", evento.tipo)
                continue
            if not self._enfriador.permite(evento.tipo):
                log.info("evento %s en enfriamiento; no se notifica", evento.tipo)
                continue
            foto, foto_ok = self._tomar_foto(evento.canal)
            telegram_ok = self._notificar(foto, evento) if foto_ok else False
            self._registro.guardar(evento, foto_ok=foto_ok, telegram_ok=telegram_ok)
            procesados += 1
            log.info(
                "evento %s canal %s procesado (foto=%s, telegram=%s)",
                evento.tipo,
                evento.canal,
                foto_ok,
                telegram_ok,
            )
        return procesados

    def _tomar_foto(self, canal: str) -> tuple[bytes, bool]:
        try:
            return self._fuente.snapshot(canal), True
        except (httpx.HTTPError, OSError) as e:
            log.error("no se pudo obtener snapshot del canal %s: %s", canal, e)
            return b"", False

    def _notificar(self, foto: bytes, evento: EventoCamara) -> bool:
        try:
            self._destino.enviar_foto(foto, armar_caption(evento))
            return True
        except Exception as e:  # el destino define sus excepciones
            log.error("fallo el envio a Telegram: %s", e)
            return False
