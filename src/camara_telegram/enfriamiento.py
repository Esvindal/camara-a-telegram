"""Enfriamiento por tipo de evento: evita spamear Telegram en rafagas."""

import time
from collections.abc import Callable


class Enfriador:
    """Deja pasar un evento de cada ``tipo`` como maximo cada ``segundos``.

    ``segundos <= 0`` deshabilita el filtro (todo pasa). El reloj es inyectable
    para que los tests no dependan del tiempo real.
    """

    def __init__(self, segundos: float, ahora: Callable[[], float] = time.monotonic) -> None:
        self._segundos = segundos
        self._ahora = ahora
        self._ultimos: dict[str, float] = {}

    def permite(self, tipo: str) -> bool:
        if self._segundos <= 0:
            return True
        ahora = self._ahora()
        ultimo = self._ultimos.get(tipo)
        if ultimo is None or ahora - ultimo >= self._segundos:
            self._ultimos[tipo] = ahora
            return True
        return False
