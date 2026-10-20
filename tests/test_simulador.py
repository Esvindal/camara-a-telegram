"""Tests del simulador de eventos y de las imagenes de ejemplo."""

import io

from PIL import Image

from camara_telegram.fuentes.simulador import Simulador


def test_el_simulador_emite_eventos_activos(tmp_path):
    sim = Simulador(intervalo=0, semilla=1, carpeta_fotos=tmp_path)
    eventos = []

    for evento in sim.iterar_eventos(max_eventos=5):
        eventos.append(evento)

    assert len(eventos) == 5
    assert all(e.activo for e in eventos)
    assert all(e.origen == "simulador" for e in eventos)


def test_el_simulador_genera_un_snapshot_jpeg_valido(tmp_path):
    sim = Simulador(intervalo=0, semilla=1, carpeta_fotos=tmp_path)

    foto = sim.snapshot("1")

    imagen = Image.open(io.BytesIO(foto))
    assert imagen.format == "JPEG"
    assert imagen.size[0] > 0
