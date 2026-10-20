"""Fuente ``dahua``: eventos y snapshots por HTTP Digest (protocolo publico).

Endpoints usados (documentados en la especificacion HTTP publica de
Dahua/Amcrest y en integraciones comunitarias como rroller/dahua):

- Eventos: ``GET /cgi-bin/eventManager.cgi?action=attach&codes=[...]&heartbeat=N``
  responde ``multipart/x-mixed-replace`` con partes ``text/plain`` del estilo
  ``Code=VideoMotion;action=Start;index=0``.
- Foto: ``GET /cgi-bin/snapshot.cgi?channel=N`` devuelve un JPEG.

El firmware varia entre modelos: los campos desconocidos se conservan en
``detalle`` y las partes sin ``Code=`` (heartbeats) se descartan. Verificar
contra el dispositivo concreto antes de produccion.
"""

import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx

from ..modelos import EventoCamara
from ..multipart import PartidorMultipart, boundary_de_content_type
from .base import FuenteEventos

log = logging.getLogger(__name__)

EVENTOS_POR_DEFECTO = "All"


def traducir_parte(cuerpo: bytes) -> EventoCamara | None:
    """Traduce una parte ``text/plain`` Dahua a un evento normalizado."""
    texto = cuerpo.decode("utf-8", "replace").strip()
    pares: dict[str, str] = {}
    for par in texto.split(";"):
        if "=" in par:
            clave, valor = par.split("=", 1)
            pares[clave.strip()] = valor.strip()
    if "Code" not in pares:
        return None
    action = pares.get("action", "")
    canal = pares.get("index", "?")
    return EventoCamara(
        tipo=pares["Code"],
        activo=action.lower() != "stop",
        canal=canal,
        origen="dahua",
        nombre_camara=f"Dahua canal {canal}",
        ts=datetime.now(UTC),
        detalle=pares,
    )


class DahuaFuente(FuenteEventos):
    def __init__(
        self,
        base_url: str,
        usuario: str,
        clave: str,
        codigos: str = EVENTOS_POR_DEFECTO,
        cliente: httpx.Client | None = None,
        espera_reconexion: float = 5.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._codigos = codigos
        self._espera = espera_reconexion
        self._cliente = cliente or httpx.Client(
            auth=httpx.DigestAuth(usuario, clave), timeout=httpx.Timeout(30.0, read=None)
        )

    def iterar_eventos(self) -> Iterator[EventoCamara]:
        url = f"{self._base}/cgi-bin/eventManager.cgi"
        params = {"action": "attach", "codes": f"[{self._codigos}]", "heartbeat": "5"}
        while True:
            try:
                with self._cliente.stream("GET", url, params=params) as resp:
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
                log.warning("flujo Dahua cortado (%s); reconectando en %ss", e, self._espera)
                import time

                time.sleep(self._espera)

    def snapshot(self, canal: str) -> bytes:
        resp = self._cliente.get(
            f"{self._base}/cgi-bin/snapshot.cgi", params={"channel": canal}, timeout=15
        )
        resp.raise_for_status()
        return resp.content
