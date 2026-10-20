"""Fuente ``simulator``: eventos y fotos de ejemplo, sin camara real.

Genera una escena sintetica con Pillow (rotulo "DATOS DE EJEMPLO" siempre
visible) o, detras de la bandera ``--webcam``, toma frames de la webcam con
OpenCV si esta instalado el extra ``webcam``.
"""

import io
import random
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageDraw

from ..modelos import EventoCamara


class Simulador:
    TIPOS = ("VideoMotion", "CrossLineDetection", "AlarmLocal", "FaceDetection")

    def __init__(
        self,
        intervalo: float = 5.0,
        semilla: int | None = None,
        carpeta_fotos: Path | None = None,
        usar_webcam: bool = False,
        dormir: Callable[[float], None] = time.sleep,
        nombre_camara: str = "Camara simulada",
    ) -> None:
        self._intervalo = intervalo
        self._dormir = dormir
        self._azar = random.Random(semilla)
        self._carpeta_fotos = carpeta_fotos
        self._usar_webcam = usar_webcam
        self._nombre = nombre_camara
        self._cuadro = 0

    def iterar_eventos(self, max_eventos: int | None = None) -> Iterator[EventoCamara]:
        emitidos = 0
        while max_eventos is None or emitidos < max_eventos:
            if emitidos > 0:
                self._dormir(self._intervalo)
            yield EventoCamara(
                tipo=self._azar.choice(self.TIPOS),
                activo=True,
                canal="1",
                origen="simulador",
                nombre_camara=self._nombre,
                ts=datetime.now(UTC),
                detalle={"action": "Start", "simulado": "si"},
            )
            emitidos += 1

    def snapshot(self, canal: str) -> bytes:
        if self._usar_webcam:
            foto = self._frame_webcam()
            if foto is not None:
                return foto
        self._cuadro += 1
        return self._jpeg_sintetico(canal)

    def _frame_webcam(self) -> bytes | None:
        """Intenta capturar un frame de la webcam (extra opcional ``webcam``)."""
        try:
            import cv2
        except ImportError:
            return None
        cap = cv2.VideoCapture(0)
        try:
            ok, frame = cap.read()
            if not ok:
                return None
            ok, buf = cv2.imencode(".jpg", frame)
            return bytes(buf) if ok else None
        finally:
            cap.release()

    def _jpeg_sintetico(self, canal: str) -> bytes:
        img = Image.new("RGB", (640, 360), (24, 28, 36))
        dib = ImageDraw.Draw(img)
        # Falso encuadre de camara: pared, piso y un rectangulo "en movimiento".
        dib.rectangle((0, 250, 640, 360), fill=(38, 44, 54))
        x = 60 + (self._cuadro * 37) % 440
        dib.rectangle((x, 150, x + 90, 250), outline=(92, 200, 250), width=3)
        ahora = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        dib.rectangle((0, 0, 640, 30), fill=(12, 14, 18))
        dib.text((10, 8), f"{self._nombre} - canal {canal} - {ahora}", fill=(220, 225, 230))
        dib.text((10, 330), "DATOS DE EJEMPLO - simulador", fill=(250, 180, 60))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
