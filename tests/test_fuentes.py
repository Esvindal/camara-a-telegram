"""Tests de los traductores de eventos Dahua e Hikvision (sin red)."""

from camara_telegram.fuentes.dahua import traducir_parte as traducir_dahua
from camara_telegram.fuentes.hikvision import traducir_parte as traducir_hikvision
from camara_telegram.modelos import EventoCamara


def test_dahua_start_se_traduce_a_evento_activo():
    evento = traducir_dahua(b"Code=VideoMotion;action=Start;index=0")

    assert evento is not None
    assert evento.tipo == "VideoMotion"
    assert evento.activo is True
    assert evento.canal == "0"
    assert evento.origen == "dahua"


def test_dahua_stop_se_traduce_a_evento_inactivo():
    evento = traducir_dahua(b"Code=VideoMotion;action=Stop;index=0")

    assert evento is not None
    assert evento.activo is False


def test_dahua_parte_sin_code_se_descarta():
    assert traducir_dahua(b"") is None
    assert traducir_dahua(b"Heartbeat") is None


def test_dahua_action_desconocida_se_marca_activo_por_defecto():
    # Algunos firmwares usan actions distintas; se registra tal cual.
    evento = traducir_dahua(b"Code=AlarmLocal;action=Pulse;index=1")
    assert evento is not None
    assert evento.tipo == "AlarmLocal"
    assert evento.detalle.get("action") == "Pulse"


def test_hikvision_xml_activo_se_traduce(datos_dir):
    xml = (datos_dir / "alerta_hikvision.xml").read_bytes()

    evento = traducir_hikvision(xml)

    assert evento is not None
    assert evento.tipo == "fielddetection"
    assert evento.activo is True
    assert evento.canal == "1"
    assert evento.origen == "hikvision"
    assert evento.nombre_camara == "CAMARA DEMO"


def test_hikvision_inactive_se_traduce():
    xml = b"""<EventNotificationAlert xmlns="http://www.hikvision.com/ver20/XMLSchema">
<channelID>2</channelID><eventType>linedetection</eventType>
<eventState>inactive</eventState><eventDescription>linedetection alarm</eventDescription>
</EventNotificationAlert>"""
    evento = traducir_hikvision(xml)
    assert evento is not None
    assert evento.activo is False


def test_hikvision_heartbeat_y_basura_se_descartan():
    assert traducir_hikvision(b"<heartbeat/>") is None
    assert traducir_hikvision(b"no es xml") is None
    assert traducir_hikvision(b"") is None


def test_evento_lleva_timestamp_consciente():
    evento = traducir_dahua(b"Code=VideoMotion;action=Start;index=0")
    assert evento is not None
    assert evento.ts.tzinfo is not None
    assert isinstance(evento, EventoCamara)
