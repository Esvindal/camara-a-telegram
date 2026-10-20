"""Destino opcional Google Sheets (extra ``sheets``, detras de bandera).

NO VERIFICADO en este entorno: requiere una cuenta de servicio real con la
planilla compartida. Se incluye como gancho documentado; queda marcado como
"a verificar en dispositivo/credenciales" en el README.
"""

import logging
from datetime import datetime

log = logging.getLogger(__name__)


class SheetsDestino:
    """Agrega una fila por evento a una planilla de Google Sheets."""

    def __init__(self, credenciales_json: str, planilla: str, solapa: str = "eventos") -> None:
        try:
            import gspread
        except ImportError as e:
            raise RuntimeError(
                "el destino Sheets requiere el extra: pip install 'camara-a-telegram[sheets]'"
            ) from e
        self._hoja = gspread.service_account(credenciales_json).open(planilla).worksheet(solapa)

    def registrar(self, tipo: str, camara: str, ts: datetime, telegram_ok: bool) -> None:
        self._hoja.append_row(
            [ts.isoformat(), tipo, camara, "si" if telegram_ok else "no"],
            value_input_option="USER_ENTERED",
        )
