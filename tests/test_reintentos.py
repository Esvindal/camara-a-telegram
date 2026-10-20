"""Tests de los reintentos con espera creciente."""

import pytest

from camara_telegram.reintentos import ReintentosAgotados, con_reintentos


def test_devuelve_el_resultado_si_funciona_a_la_primera():
    assert con_reintentos(lambda: "ok", intentos=3, esperar=lambda s: None) == "ok"


def test_reintenta_hasta_que_funcione():
    llamadas = []

    def inestable():
        llamadas.append(1)
        if len(llamadas) < 3:
            raise ConnectionError("falla")
        return "ok"

    assert con_reintentos(inestable, intentos=3, esperar=lambda s: None) == "ok"
    assert len(llamadas) == 3


def test_agotados_los_intentos_lanza_reintentos_agotados():
    def siempre_falla():
        raise TimeoutError("sin red")

    with pytest.raises(ReintentosAgotados):
        con_reintentos(siempre_falla, intentos=2, esperar=lambda s: None)


def test_la_espera_crece_entre_reintentos():
    esperas = []

    def falla():
        raise ConnectionError("falla")

    with pytest.raises(ReintentosAgotados):
        con_reintentos(falla, intentos=3, esperar=esperas.append, espera_inicial=1.0, factor=2.0)

    assert esperas == [1.0, 2.0]


def test_no_reintenta_excepciones_fuera_de_la_lista():
    def error_de_programa():
        raise ValueError("bug")

    with pytest.raises(ValueError):
        con_reintentos(
            error_de_programa, intentos=3, esperar=lambda s: None, recuperables=(ConnectionError,)
        )
