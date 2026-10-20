"""Tests del partidor de flujos multipart/x-mixed-replace."""

from camara_telegram.multipart import PartidorMultipart


def alimentar_todo(partidor: PartidorMultipart, datos: bytes, tam_chunk: int = 16):
    partes = []
    for i in range(0, len(datos), tam_chunk):
        partes.extend(partidor.alimentar(datos[i : i + tam_chunk]))
    partes.extend(partidor.cerrar())
    return partes


def test_parte_un_flujo_dahua_en_partes_con_headers_y_cuerpo(datos_dir):
    crudo = (datos_dir / "flujo_dahua.txt").read_bytes()
    partidor = PartidorMultipart(b"myboundary")

    partes = alimentar_todo(partidor, crudo)

    assert len(partes) == 4
    primera = partes[0]
    assert primera.headers["Content-Type"] == "text/plain"
    assert b"Code=VideoMotion" in primera.cuerpo


def test_tolera_chunks_que_cortan_a_mitad_de_linea(datos_dir):
    crudo = (datos_dir / "flujo_dahua.txt").read_bytes()
    partidor = PartidorMultipart(b"myboundary")

    partes = alimentar_todo(partidor, crudo, tam_chunk=7)

    assert len(partes) == 4


def test_el_marcador_de_cierre_no_genera_parte_vacia():
    partidor = PartidorMultipart(b"b")
    partes = alimentar_todo(partidor, b"--b\r\nX: 1\r\n\r\ncuerpo\r\n--b--\r\n")
    assert len(partes) == 1
    assert partes[0].cuerpo == b"cuerpo"


def test_descarta_basura_anterior_al_primer_boundary():
    partidor = PartidorMultipart(b"b")
    partes = alimentar_todo(partidor, b"HTTP/1.0 200 OK\r\n\r\n--b\r\nX: 1\r\n\r\nok\r\n--b--")
    assert len(partes) == 1
    assert partes[0].cuerpo == b"ok"
