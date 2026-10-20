"""CLI ``camara-a-telegram``: run / exportar-csv / generar-datos."""

import argparse
import logging
import sys
from pathlib import Path

from .almacen.registro import RegistroEventos
from .config import Config, ErrorConfig, cargar_config
from .destinos.consola import ConsolaDestino
from .destinos.telegram import TelegramDestino
from .fuentes.base import FuenteEventos
from .fuentes.simulador import Simulador
from .pipeline import Destino, Pipeline

log = logging.getLogger(__name__)


def _fuente(cfg: Config, args: argparse.Namespace) -> FuenteEventos:
    if args.fuente == "simulator":
        return Simulador(
            intervalo=args.intervalo,
            usar_webcam=cfg.usar_webcam,
            carpeta_fotos=Path("datos/fotos"),
        )
    if args.fuente == "dahua":
        from .fuentes.dahua import DahuaFuente

        return DahuaFuente(cfg.camara_url, cfg.camara_usuario, cfg.camara_clave)
    if args.fuente == "hikvision":
        from .fuentes.hikvision import HikvisionFuente

        return HikvisionFuente(cfg.camara_url, cfg.camara_usuario, cfg.camara_clave)
    raise ErrorConfig(f"fuente desconocida: {args.fuente}")


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = cargar_config()
    fuente = _fuente(cfg, args)

    destino: Destino
    if args.dry_run:
        destino = ConsolaDestino()
        log.info("modo --dry-run: no se llama a Telegram")
    else:
        if not cfg.telegram_token or not cfg.telegram_chat_id:
            raise ErrorConfig(
                "faltan TELEGRAM_TOKEN / TELEGRAM_CHAT_ID; usá --dry-run para probar sin bot"
            )
        destino = TelegramDestino(cfg.telegram_token, cfg.telegram_chat_id)

    registro = RegistroEventos(cfg.db_path)
    pipeline = Pipeline(
        fuente=fuente,
        destino=destino,
        registro=registro,
        enfriador_segundos=args.enfriamiento,
        max_eventos=args.max_eventos,
    )
    log.info("escuchando eventos (fuente=%s, enfriamiento=%ss)", args.fuente, args.enfriamiento)
    try:
        procesados = pipeline.correr()
    except KeyboardInterrupt:
        log.info("cierre ordenado por el usuario")
        procesados = -1
    finally:
        registro.cerrar()
    if procesados >= 0:
        log.info("fin: %d evento(s) procesados", procesados)
    return 0


def _cmd_exportar_csv(args: argparse.Namespace) -> int:
    reg = RegistroEventos(Path(args.db))
    try:
        reg.exportar_csv(Path(args.salida))
    finally:
        reg.cerrar()
    print(f"CSV exportado a {args.salida}")
    return 0


def _cmd_generar_datos(args: argparse.Namespace) -> int:
    """Corre el simulador en dry-run y vuelca el registro a JSON para docs/."""
    reg = RegistroEventos(Path(args.db))
    sim = Simulador(intervalo=0, semilla=42)
    destino = ConsolaDestino()
    pipe = Pipeline(fuente=sim, destino=destino, registro=reg, enfriador_segundos=0)
    pipe.correr(max_eventos=args.cantidad)
    reg.exportar_json(Path(args.salida), simulados=True)
    reg.cerrar()
    print(f"{args.cantidad} eventos simulados exportados a {args.salida}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="camara-a-telegram",
        description="Evento de camara IP -> foto en Telegram -> registro en SQLite/CSV",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    run = sub.add_parser("run", help="escuchar eventos y notificar")
    run.add_argument(
        "--fuente", choices=["simulator", "dahua", "hikvision"], default="simulator"
    )
    run.add_argument("--intervalo", type=float, default=5.0, help="seg entre eventos simulados")
    run.add_argument("--max-eventos", type=int, default=None)
    run.add_argument("--enfriamiento", type=float, default=60.0)
    run.add_argument("--dry-run", action="store_true", help="no llamar a Telegram")
    run.set_defaults(fn=_cmd_run)

    exp = sub.add_parser("exportar-csv", help="exportar el registro a CSV")
    exp.add_argument("--db", default="datos/eventos.db")
    exp.add_argument("--salida", default="datos/eventos.csv")
    exp.set_defaults(fn=_cmd_exportar_csv)

    gen = sub.add_parser("generar-datos", help="generar JSON de ejemplo para docs/")
    gen.add_argument("--db", default="datos/eventos.db")
    gen.add_argument("--salida", default="docs/data/eventos-ejemplo.json")
    gen.add_argument("--cantidad", type=int, default=20)
    gen.set_defaults(fn=_cmd_generar_datos)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = construir_parser().parse_args(argv)
    try:
        return int(args.fn(args))
    except ErrorConfig as e:
        log.error("%s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
