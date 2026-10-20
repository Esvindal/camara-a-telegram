#!/usr/bin/env python3
"""Obtiene el chat id de Telegram a partir de getUpdates.

Uso:
    1. Crear el bot con @BotFather y guardar el token en TELEGRAM_TOKEN
       (variable de entorno o archivo .env junto a este repo).
    2. Mandarle /start (o cualquier mensaje) al bot desde tu Telegram.
    3. Correr:  python scripts/obtener_chat_id.py
    4. Copiar el "chat id" que imprime a TELEGRAM_CHAT_ID en .env.

Documentacion: https://core.telegram.org/bots/api#getupdates
"""

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("Falta TELEGRAM_TOKEN (en .env o variable de entorno).", file=sys.stderr)
        return 2

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        datos = httpx.get(url, timeout=20).json()
    except httpx.HTTPError as e:
        print(f"No se pudo llamar a la API de Telegram: {e}", file=sys.stderr)
        return 1
    if not datos.get("ok"):
        print(f"La API respondio error: {datos.get('description')}", file=sys.stderr)
        return 1

    chats: dict[int, str] = {}
    for update in datos.get("result", []):
        mensaje = update.get("message") or update.get("channel_post") or {}
        chat = mensaje.get("chat") or {}
        if "id" in chat:
            nombre = " ".join(
                p for p in (chat.get("first_name"), chat.get("title")) if p
            ) or chat.get("username", "?")
            chats[chat["id"]] = nombre

    if not chats:
        print("No hay mensajes todavia. Mandale /start al bot y volve a correr.")
        return 0
    print("Chats que le escribieron al bot:")
    for chat_id, nombre in chats.items():
        print(f"  chat id: {chat_id}   ({nombre})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
