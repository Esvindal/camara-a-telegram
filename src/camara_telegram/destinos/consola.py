"""Destino de consola (modo ``--dry-run``): imprime lo que se enviaria."""

import logging
import time
from collections.abc import Callable

log = logging.getLogger(__name__)


class ConsolaDestino:
    """No llama a Telegram: registra el caption y el tamano de la foto."""

    def __init__(self) -> None:
        self._contador = 0

    def enviar_foto(
        self, foto: bytes, caption: str, esperar: Callable[[float], None] = time.sleep
    ) -> int:
        self._contador += 1
        log.info("[dry-run] enviaria foto de %d bytes con caption:\n%s", len(foto), caption)
        return self._contador
