"""Tests del registro en SQLite y la exportacion a CSV / JSON."""

import csv
import sqlite3
from datetime import UTC, datetime

from camara_telegram.almacen.registro import RegistroEventos
from camara_telegram.modelos import EventoCamara


def evento(ts: datetime | None = None) -> EventoCamara:
    return EventoCamara(
        tipo="VideoMotion",
        activo=True,
        canal="1",
        origen="simulador",
        nombre_camara="Camara demo",
        ts=ts or datetime(2026, 10, 20, 13, 0, 0, tzinfo=UTC),
        detalle={"action": "Start"},
    )


def test_guardar_y_listar_eventos(tmp_path):
    reg = RegistroEventos(tmp_path / "eventos.db")
    reg.guardar(evento(), foto_ok=True, telegram_ok=True)

    filas = reg.listar()
    assert len(filas) == 1
    assert filas[0]["tipo"] == "VideoMotion"
    assert filas[0]["telegram_ok"] == 1


def test_exportar_csv_escribe_encabezado_y_filas(tmp_path):
    reg = RegistroEventos(tmp_path / "eventos.db")
    reg.guardar(evento(), foto_ok=True, telegram_ok=True)
    salida = tmp_path / "eventos.csv"

    reg.exportar_csv(salida)

    with salida.open(newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 1
    assert filas[0]["tipo"] == "VideoMotion"
    assert "ts_utc" in filas[0]


def test_exportar_json_para_el_sitio_docs(tmp_path):
    reg = RegistroEventos(tmp_path / "eventos.db")
    reg.guardar(evento(), foto_ok=True, telegram_ok=False)
    salida = tmp_path / "eventos-ejemplo.json"

    reg.exportar_json(salida, simulados=True)

    import json

    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert datos["simulados"] is True
    assert len(datos["eventos"]) == 1
    assert datos["eventos"][0]["telegram_ok"] is False


def test_la_base_se_crea_en_directorio_inexistente(tmp_path):
    reg = RegistroEventos(tmp_path / "sub" / "dir" / "eventos.db")
    reg.guardar(evento(), foto_ok=True, telegram_ok=True)
    with sqlite3.connect(tmp_path / "sub" / "dir" / "eventos.db") as con:
        assert con.execute("select count(*) from eventos").fetchone()[0] == 1
