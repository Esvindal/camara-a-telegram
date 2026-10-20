"""Tests del armado del mensaje de Telegram (hora Argentina UTC-3)."""

from datetime import UTC, datetime

from camara_telegram.mensaje import armar_caption
from camara_telegram.modelos import EventoCamara


def evento(ts: datetime) -> EventoCamara:
    return EventoCamara(
        tipo="VideoMotion",
        activo=True,
        canal="1",
        origen="simulador",
        nombre_camara="Camara porton",
        ts=ts,
    )


def test_el_caption_incluye_tipo_camara_y_hora_en_utc3():
    # 13:00 UTC son las 10:00 en Argentina (UTC-3).
    caption = armar_caption(evento(datetime(2026, 10, 20, 13, 0, 0, tzinfo=UTC)))

    assert "VideoMotion" in caption
    assert "Camara porton" in caption
    assert "10:00" in caption
    assert "2026-10-20" in caption


def test_el_caption_no_pasa_de_1024_caracteres():
    evento_largo = EventoCamara(
        tipo="X" * 2000,
        activo=True,
        canal="1",
        origen="simulador",
        nombre_camara="Y" * 2000,
        ts=datetime(2026, 10, 20, 13, 0, 0, tzinfo=UTC),
    )
    assert len(armar_caption(evento_largo)) <= 1024
