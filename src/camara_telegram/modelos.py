"""Modelo de dominio: un evento emitido por una camara o por el simulador."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EventoCamara:
    """Evento normalizado, independiente del fabricante.

    ``activo`` distingue el flanco de subida (Start / active) del de bajada
    (Stop / inactive): solo los eventos activos disparan foto y aviso.
    """

    tipo: str  # VideoMotion, CrossLineDetection, fielddetection, ...
    activo: bool
    canal: str
    origen: str  # "simulador" | "dahua" | "hikvision"
    ts: datetime
    nombre_camara: str = "Camara"
    detalle: dict[str, str] = field(default_factory=dict)
