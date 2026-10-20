"""Tests del enfriamiento por tipo de evento (anti-spam)."""

from camara_telegram.enfriamiento import Enfriador


def test_el_primer_evento_de_un_tipo_siempre_pasa():
    enf = Enfriador(segundos=60, ahora=lambda: 1000.0)
    assert enf.permite("VideoMotion") is True


def test_un_segundo_evento_dentro_del_enfriamiento_se_bloquea():
    reloj = [1000.0]
    enf = Enfriador(segundos=60, ahora=lambda: reloj[0])
    assert enf.permite("VideoMotion") is True
    assert enf.permite("VideoMotion") is False


def test_pasado_el_enfriamiento_vuelve_a_pasar():
    reloj = [1000.0]
    enf = Enfriador(segundos=60, ahora=lambda: reloj[0])
    assert enf.permite("VideoMotion") is True
    reloj[0] += 61
    assert enf.permite("VideoMotion") is True


def test_el_enfriamiento_es_por_tipo_de_evento():
    enf = Enfriador(segundos=60, ahora=lambda: 0.0)
    assert enf.permite("VideoMotion") is True
    assert enf.permite("CrossLineDetection") is True


def test_enfriamiento_cero_deshabilita_el_filtro():
    enf = Enfriador(segundos=0, ahora=lambda: 0.0)
    assert enf.permite("VideoMotion") is True
    assert enf.permite("VideoMotion") is True
