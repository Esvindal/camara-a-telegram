"""Reintentos con espera creciente (backoff exponencial simple)."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class ReintentosAgotados(Exception):
    """Se agotaron los intentos; ``ultimo_error`` guarda la causa."""

    def __init__(self, ultimo_error: BaseException) -> None:
        super().__init__(f"se agotaron los reintentos: {ultimo_error}")
        self.ultimo_error = ultimo_error


def con_reintentos[T](
    fn: Callable[[], T],
    intentos: int = 3,
    esperar: Callable[[float], None] = time.sleep,
    espera_inicial: float = 1.0,
    factor: float = 2.0,
    recuperables: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Ejecuta ``fn`` reintentando ante excepciones ``recuperables``.

    Entre intento e intento espera ``espera_inicial * factor ** n`` segundos
    (espera inyectable para tests). Las excepciones fuera de ``recuperables``
    se propagan sin reintentar.
    """
    espera = espera_inicial
    ultimo: BaseException | None = None
    for i in range(intentos):
        try:
            return fn()
        except recuperables as e:
            ultimo = e
            if i < intentos - 1:
                esperar(espera)
                espera *= factor
    assert ultimo is not None
    raise ReintentosAgotados(ultimo) from ultimo
