"""Interfaz comun a todas las fuentes de eventos."""

from collections.abc import Iterator
from typing import Protocol

from ..modelos import EventoCamara


class FuenteEventos(Protocol):
    """Una fuente sabe emitir eventos y pedir la foto del momento."""

    def iterar_eventos(self) -> Iterator[EventoCamara]:
        """Iterador (potencialmente infinito) de eventos normalizados."""
        ...

    def snapshot(self, canal: str) -> bytes:
        """Devuelve un JPEG del canal en el momento de la llamada."""
        ...
