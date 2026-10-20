"""Tests del destino Telegram con HTTP simulado (respx, sin red)."""

import httpx
import pytest
import respx

from camara_telegram.destinos.telegram import ErrorTelegram, TelegramDestino

TOKEN = "123456:TEST-TOKEN-DE-EJEMPLO"


@pytest.fixture
def destino():
    return TelegramDestino(token=TOKEN, chat_id="99887766")


@respx.mock
def test_enviar_foto_llama_a_sendphoto_con_chat_id_y_caption(destino):
    ruta = respx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {"message_id": 7}})
    )

    mid = destino.enviar_foto(b"\xff\xd8\xff-jpeg-de-ejemplo", "Movimiento en porton")

    assert mid == 7
    assert ruta.called
    cuerpo = ruta.calls[0].request.content
    assert b"99887766" in cuerpo
    assert b"Movimiento en porton" in cuerpo


@respx.mock
def test_enviar_foto_reintenta_y_luego_funciona(destino):
    ruta = respx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto").mock(
        side_effect=[
            httpx.Response(500, json={"ok": False, "description": "falla interna"}),
            httpx.Response(200, json={"ok": True, "result": {"message_id": 9}}),
        ]
    )

    assert destino.enviar_foto(b"foto", "caption", esperar=lambda s: None) == 9
    assert ruta.call_count == 2


@respx.mock
def test_respuesta_ok_false_lanza_error_telegram(destino):
    respx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto").mock(
        return_value=httpx.Response(400, json={"ok": False, "description": "chat not found"})
    )

    with pytest.raises(ErrorTelegram, match="chat not found"):
        destino.enviar_foto(b"foto", "caption", esperar=lambda s: None)


@respx.mock
def test_el_token_no_aparece_en_el_mensaje_de_error(destino):
    respx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto").mock(
        return_value=httpx.Response(401, json={"ok": False, "description": "unauthorized"})
    )

    with pytest.raises(ErrorTelegram) as exc:
        destino.enviar_foto(b"foto", "caption", esperar=lambda s: None)
    assert TOKEN not in str(exc.value)
