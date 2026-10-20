# Guion del video — prueba real cámara → celular (30–45 s)

**Objetivo:** mostrar que el pipeline funciona de punta a punta con hardware
real. Una sola toma continua si es posible.

## Antes de grabar

- [ ] Cámara Dahua o Hikvision accesible desde la PC, con usuario de solo lectura.
- [ ] `.env` completo (`CAMARA_FUENTE`, `CAMARA_URL`, usuario/clave, token y chat id).
- [ ] Telegram abierto en el celular, chat con el bot visible.
- [ ] Terminal con el repo a la vista. Tipografía grande.
- [ ] `pip install -e .` ya corrido.

## Toma sugerida (única, sin cortes)

1. **(0–8 s) Pantalla de la PC.** Mostrar el `.env` con la clave tapada o
   pixelada, y correr:

   ```
   camara-a-telegram run --fuente dahua
   ```

   Se ve el log `escuchando eventos (fuente=dahua)`.

2. **(8–20 s) Disparar el evento.** Caminar frente a la cámara (o taparla)
   mientras el celular queda en cuadro, o mostrar la pantalla de la PC con el
   log `evento VideoMotion canal 1 procesado`.

3. **(20–30 s) El celular.** Enfocar la notificación de Telegram llegando con
   la foto del momento y el caption (tipo, cámara, hora UTC-3).

4. **(30–40 s) El registro.** Volver a la PC, `Ctrl+C` (cierre ordenado) y
   correr:

   ```
   camara-a-telegram exportar-csv
   ```

   Mostrar el CSV con la fila del evento recién registrada.

## Qué NO mostrar

- La contraseña de la cámara ni el token del bot (`.env` tapado).
- Direcciones IP públicas si las hubiera (usar la IP local, p. ej. `192.168.x.x`).
- Rostros de terceros ni patentes reales en las fotos.

## Dónde va

El archivo final (mp4, < 10 MB idealmente) se referencia en `docs/index.html`
en el hueco "Video de la prueba real" y en la ficha del servicio en
Workana/Upwork/Fiverr como "demo funcional de cámara a Telegram, código
abierto" — nunca como "proyecto de cliente".
