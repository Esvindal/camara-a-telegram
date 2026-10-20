"""Registro de eventos en SQLite con exportacion a CSV y JSON."""

import csv
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ..modelos import EventoCamara

_SCHEMA = """
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc TEXT NOT NULL,
    tipo TEXT NOT NULL,
    canal TEXT,
    camara TEXT,
    origen TEXT,
    detalle TEXT,
    foto_ok INTEGER NOT NULL,
    telegram_ok INTEGER NOT NULL
)
"""


class RegistroEventos:
    def __init__(self, ruta_db: Path) -> None:
        ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(ruta_db)
        self._con.execute(_SCHEMA)
        self._con.commit()

    def guardar(self, evento: EventoCamara, foto_ok: bool, telegram_ok: bool) -> int:
        cur = self._con.execute(
            "INSERT INTO eventos (ts_utc, tipo, canal, camara, origen, detalle,"
            " foto_ok, telegram_ok) VALUES (?,?,?,?,?,?,?,?)",
            (
                evento.ts.astimezone(UTC).isoformat(),
                evento.tipo,
                evento.canal,
                evento.nombre_camara,
                evento.origen,
                json.dumps(evento.detalle, ensure_ascii=False),
                int(foto_ok),
                int(telegram_ok),
            ),
        )
        self._con.commit()
        return cur.lastrowid or 0

    def listar(self) -> list[dict]:
        cur = self._con.execute(
            "SELECT id, ts_utc, tipo, canal, camara, origen, detalle, foto_ok, telegram_ok"
            " FROM eventos ORDER BY id"
        )
        columnas = [d[0] for d in cur.description]
        return [dict(zip(columnas, fila, strict=True)) for fila in cur.fetchall()]

    def exportar_csv(self, ruta: Path) -> None:
        filas = self.listar()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "ts_utc",
                    "tipo",
                    "canal",
                    "camara",
                    "origen",
                    "detalle",
                    "foto_ok",
                    "telegram_ok",
                ],
            )
            escritor.writeheader()
            escritor.writerows(filas)

    def exportar_json(self, ruta: Path, simulados: bool) -> None:
        """JSON para el visor del sitio docs/. ``simulados`` es obligatorio."""
        eventos = [
            {
                "id": f["id"],
                "ts_utc": f["ts_utc"],
                "tipo": f["tipo"],
                "canal": f["canal"],
                "camara": f["camara"],
                "origen": f["origen"],
                "foto_ok": bool(f["foto_ok"]),
                "telegram_ok": bool(f["telegram_ok"]),
            }
            for f in self.listar()
        ]
        datos = {
            "generado_en": datetime.now(UTC).isoformat(),
            "simulados": simulados,
            "eventos": eventos,
        }
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def cerrar(self) -> None:
        self._con.close()
