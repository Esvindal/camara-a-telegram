"""Partidor incremental de flujos ``multipart/x-mixed-replace`` / ``multipart/mixed``.

Las camaras IP (Dahua ``eventManager.cgi`` e Hikvision ``alertStream``) emiten
sus eventos como partes separadas por un boundary dentro de una respuesta HTTP
que no termina. Este modulo no depende de la red: se alimenta con chunks de
bytes y devuelve las partes completas, lo que lo hace testeable sin camara.
"""

from dataclasses import dataclass


@dataclass
class Parte:
    headers: dict[str, str]
    cuerpo: bytes


class PartidorMultipart:
    def __init__(self, boundary: bytes) -> None:
        self._marca = b"--" + boundary
        self._buf = bytearray()
        self._iniciado = False

    def alimentar(self, chunk: bytes) -> list[Parte]:
        """Agrega un chunk al buffer y devuelve las partes completas."""
        self._buf += chunk
        return self._extraer()

    def cerrar(self) -> list[Parte]:
        """Vacia lo que haya quedado completo al cerrar el flujo."""
        return self._extraer()

    def _extraer(self) -> list[Parte]:
        partes: list[Parte] = []
        while True:
            if not self._iniciado:
                idx = self._buf.find(self._marca)
                if idx == -1:
                    break
                del self._buf[: idx + len(self._marca)]
                self._iniciado = True
            idx = self._buf.find(self._marca)
            if idx == -1:
                break
            segmento = bytes(self._buf[:idx])
            del self._buf[: idx + len(self._marca)]
            parte = _parsear_segmento(segmento)
            if parte is not None:
                partes.append(parte)
        return partes


def _parsear_segmento(seg: bytes) -> Parte | None:
    seg = seg.strip(b"\r\n")
    if not seg or seg == b"--":
        return None
    sep = b"\r\n\r\n" if b"\r\n\r\n" in seg else b"\n\n"
    if sep in seg:
        crudo_headers, cuerpo = seg.split(sep, 1)
    else:
        crudo_headers, cuerpo = b"", seg
    headers: dict[str, str] = {}
    for linea in crudo_headers.splitlines():
        if b":" in linea:
            clave, valor = linea.split(b":", 1)
            headers[clave.decode("latin-1").strip()] = valor.decode("latin-1").strip()
    return Parte(headers=headers, cuerpo=cuerpo.rstrip(b"\r\n"))


def boundary_de_content_type(content_type: str) -> bytes | None:
    """Extrae ``boundary=...`` de un header Content-Type, si esta."""
    for pedazo in content_type.split(";"):
        pedazo = pedazo.strip()
        if pedazo.startswith("boundary="):
            return pedazo[len("boundary=") :].strip('"').encode()
    return None
