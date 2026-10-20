// Visor de docs/data/eventos-ejemplo.json — eventos simulados por `generar-datos`.
(async function () {
  const visor = document.getElementById("visor");
  try {
    const resp = await fetch("data/eventos-ejemplo.json");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const datos = await resp.json();
    const eventos = datos.eventos || [];

    const resumen = document.createElement("p");
    resumen.className = "visor-resumen";
    const porTipo = {};
    for (const e of eventos) porTipo[e.tipo] = (porTipo[e.tipo] || 0) + 1;
    resumen.innerHTML =
      "<span>Total: <strong>" + eventos.length + "</strong></span>" +
      Object.entries(porTipo)
        .map(([t, n]) => "<span>" + t + ": <strong>" + n + "</strong></span>")
        .join("");

    const tabla = document.createElement("table");
    tabla.innerHTML =
      "<thead><tr><th>Hora (UTC)</th><th>Tipo</th><th>Cámara</th><th>Foto</th><th>Telegram</th></tr></thead>";
    const cuerpo = document.createElement("tbody");
    for (const e of eventos) {
      const tr = document.createElement("tr");
      const hora = (e.ts_utc || "").replace("T", " ").slice(0, 19);
      tr.innerHTML =
        "<td>" + hora + "</td><td>" + e.tipo + "</td><td>" + (e.camara || "") +
        "</td><td>" + (e.foto_ok ? "sí" : "—") + "</td><td>" +
        (e.telegram_ok ? "sí" : "—") + "</td>";
      cuerpo.appendChild(tr);
    }
    tabla.appendChild(cuerpo);

    visor.textContent = "";
    visor.appendChild(resumen);
    visor.appendChild(tabla);
  } catch (e) {
    visor.innerHTML =
      '<p class="visor-estado">No se pudo cargar data/eventos-ejemplo.json. ' +
      "Generalo con <code>camara-a-telegram generar-datos</code>.</p>";
  }
})();
