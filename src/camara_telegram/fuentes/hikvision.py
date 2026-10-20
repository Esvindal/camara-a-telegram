"""Fuente ``hikvision``: eventos y snapshots por ISAPI (protocolo publico).

Endpoints usados (documentados en la especificacion ISAPI de Hikvision y en
integraciones comunitarias como pyHik):

- Eventos: ``GET /ISAPI/Event/notification/alertStream`` responde
  ``multipart/mixed`` con partes ``application/xml`` ``EventNotificationAlert``.
- Foto: ``GET /ISAPI/Streaming/channels/{canal}01/picture`` devuelve un JPEG
  (canal 1 -> 101, canal 2 -> 201).

Partes de heartbeat y XML que no sea ``EventNotificationAlert`` se descartan.
El firmware varia entre modelos: verificar contra el dispositivo concreto.
"""

import logging
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx

from ..modelos import EventoCamara
from ..multipart import PartidorMultipart, boundary_de_content_type
from .base import FuenteEventos

log = logging.getLogger(__name__)


def _texto(raiz: ET.Element, nombre: str) -> str | None:
    for el in raiz.iter():
        if el.tag.rsplit("}", 1)[-1] == nombre:
            return (el.text or "").strip() or None
    return None


def traducir_parte(cuerpo: bytes) -> EventoCamara | None:
    """Traduce una parte ``application/xml`` Hikvision a evento normalizado."""
    texto = cuerpo.decode("utf-8", "replace").strip()
    if not texto.startswith("<"):
        return None
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError:
        return None
    if raiz.tag.rsplit("}", 1)[-1] != "EventNotificationAlert":
        return None
    tipo = _texto(raiz, "eventType")
    if not tipo:
        return None
    estado = (_texto(raiz, "eventState") or "").lower()
    canal = _texto(raiz, "channelID") or "?"
    return EventoCamara(
        tipo=tipo,
        activo=estado == "active",
        canal=canal,
        origen="hikvision",
        nombre_camara=_texto(raiz, "channelName") or f"Hikvision canal {canal}",
        ts=datetime.now(UTC),
        detalle={
            "eventState": estado,
            "descripcion": _texto(raiz, "eventDescription") or "",
        },
    )


class HikvisionFuente(FuenteEventos):
    def __init__(
        self,
        base_url: str,
        usuario: str,
        clave: str,
        cliente: httpx.Client | None = None,
        espera_reconexion: float = 5.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._espera = espera_reconexion
        self._cliente = cliente or httpx.Client(
            auth=httpx.DigestAuth(usuario, clave), timeout=httpx.Timeout(30.0, read=None)
        )

    def iterar_eventos(self) -> Iterator[EventoCamara]:
        url = f"{self._base}/ISAPI/Event/notification/alertStream"
        while True:
            try:
                with self._cliente.stream("GET", url) as resp:
                    resp.raise_for_status()
                    boundary = boundary_de_content_type(resp.headers.get("content-type", ""))
                    if boundary is None:
                        raise ValueError("la respuesta no declara boundary multipart")
                    partidor = PartidorMultipart(boundary)
                    for chunk in resp.iter_bytes(4096):
                        for parte in partidor.alimentar(chunk):
                            evento = traducir_parte(parte.cuerpo)
                            if evento is not None:
                                yield evento
            except httpx.HTTPError as e:
                log.warning("flujo Hikvision cortado (%s); reconectando en %ss", e, self._espera)
                time.sleep(self._espera)

    def snapshot(self, canal: str) -> bytes:
        # ISAPI numera canales de streaming como 101, 201, ... (canal N -> N01).
        canal_stream = f"{canal}01" if len(canal) <= 2 else canal
        resp = self._cliente.get(
            f"{self._base}/ISAPI/Streaming/channels/{canal_stream}/picture", timeout=15
        )
        resp.raise_for_status()
        return resp.content
