"""Test de integracion del pipeline: evento -> foto -> mensaje -> destino -> registro."""

from datetime import UTC, datetime

from camara_telegram.almacen.registro import RegistroEventos
from camara_telegram.modelos import EventoCamara
from camara_telegram.pipeline import Pipeline


class FuenteFalsa:
    def __init__(self, eventos, foto=b"jpeg"):
        self._eventos = eventos
        self._foto = foto

    def iterar_eventos(self):
        yield from self._eventos

    def snapshot(self, canal: str) -> bytes:
        return self._foto


class DestinoFalso:
    def __init__(self):
        self.enviados = []

    def enviar_foto(self, foto: bytes, caption: str, esperar=lambda s: None) -> int:
        self.enviados.append(caption)
        return len(self.enviados)


def evento(tipo="VideoMotion", activo=True) -> EventoCamara:
    return EventoCamara(
        tipo=tipo,
        activo=activo,
        canal="1",
        origen="simulador",
        nombre_camara="Camara demo",
        ts=datetime(2026, 10, 20, 13, 0, 0, tzinfo=UTC),
    )


def test_un_evento_activo_llega_al_destino_y_queda_registrado(tmp_path):
    reg = RegistroEventos(tmp_path / "e.db")
    destino = DestinoFalso()
    pipe = Pipeline(
        fuente=FuenteFalsa([evento()]),
        destino=destino,
        registro=reg,
        enfriador_segundos=0,
    )

    procesados = pipe.correr(max_eventos=10)

    assert procesados == 1
    assert len(destino.enviados) == 1
    assert "VideoMotion" in destino.enviados[0]
    assert len(reg.listar()) == 1


def test_un_evento_inactivo_no_se_notifica_ni_registra(tmp_path):
    reg = RegistroEventos(tmp_path / "e.db")
    destino = DestinoFalso()
    pipe = Pipeline(
        fuente=FuenteFalsa([evento(activo=False)]),
        destino=destino,
        registro=reg,
        enfriador_segundos=0,
    )

    assert pipe.correr(max_eventos=10) == 0
    assert destino.enviados == []
    assert reg.listar() == []


def test_el_enfriamiento_evita_duplicados_en_rafaga(tmp_path):
    reg = RegistroEventos(tmp_path / "e.db")
    destino = DestinoFalso()
    pipe = Pipeline(
        fuente=FuenteFalsa([evento(), evento(), evento()]),
        destino=destino,
        registro=reg,
        enfriador_segundos=3600,
    )

    procesados = pipe.correr(max_eventos=10)

    assert procesados == 1
    assert len(destino.enviados) == 1
