"""Configuracion desde variables de entorno / archivo .env."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ErrorConfig(Exception):
    pass


@dataclass(frozen=True)
class Config:
    fuente: str  # simulator | dahua | hikvision
    camara_url: str
    camara_usuario: str
    camara_clave: str
    telegram_token: str
    telegram_chat_id: str
    intervalo: float
    enfriamiento: float
    db_path: Path
    usar_webcam: bool
    sheets_credenciales: str
    sheets_planilla: str


def _req(entorno: dict[str, str], nombre: str, faltantes: list[str]) -> str:
    valor = entorno.get(nombre, "").strip()
    if not valor:
        faltantes.append(nombre)
    return valor


def cargar_config(archivo_env: Path | None = None) -> Config:
    load_dotenv(archivo_env or Path(".env"))
    env = dict(os.environ)
    faltantes: list[str] = []

    fuente = env.get("CAMARA_FUENTE", "simulator").strip().lower()
    if fuente not in ("simulator", "dahua", "hikvision"):
        raise ErrorConfig(f"CAMARA_FUENTE invalida: {fuente!r} (simulator|dahua|hikvision)")

    camara_url = camara_usuario = camara_clave = ""
    if fuente != "simulator":
        camara_url = _req(env, "CAMARA_URL", faltantes)
        camara_usuario = _req(env, "CAMARA_USUARIO", faltantes)
        camara_clave = _req(env, "CAMARA_CLAVE", faltantes)

    token = env.get("TELEGRAM_TOKEN", "").strip()
    chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()

    if faltantes:
        raise ErrorConfig("faltan variables de entorno: " + ", ".join(faltantes))

    return Config(
        fuente=fuente,
        camara_url=camara_url,
        camara_usuario=camara_usuario,
        camara_clave=camara_clave,
        telegram_token=token,
        telegram_chat_id=chat_id,
        intervalo=float(env.get("SIM_INTERVALO", "5")),
        enfriamiento=float(env.get("ENFRIAMIENTO_SEG", "60")),
        db_path=Path(env.get("DB_PATH", "datos/eventos.db")),
        usar_webcam=env.get("SIM_WEBCAM", "").lower() in ("1", "true", "si"),
        sheets_credenciales=env.get("SHEETS_CREDENCIALES", "").strip(),
        sheets_planilla=env.get("SHEETS_PLANILLA", "").strip(),
    )
