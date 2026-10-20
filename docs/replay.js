// Replay de la corrida simulada: reproduce eventos REALES generados por la
// fuente `simulator` (docs/data/eventos-ejemplo.json) a través del pipeline,
// paso a paso. No es un video ni una recreación: son los datos reales de la
// corrida, animados. Marcado como "Simulado".
(function () {
  const pantalla = document.getElementById("replay-pantalla");
  if (!pantalla) return;

  const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function lineasDe(eventos) {
    const lineas = [
      "$ camara-a-telegram run --fuente simulator",
      "[boot] escuchando eventos… (simulator)",
      "",
    ];
    for (const e of eventos.slice(0, 4)) {
      const hora = (e.ts_utc || "").slice(11, 19);
      lineas.push("[" + hora + "Z] evento: " + e.tipo + " · " + e.camara);
      lineas.push("  ├─ snapshot … " + (e.foto_ok ? "ok (imagen generada)" : "falló"));
      lineas.push(
        "  ├─ telegram sendPhoto … " +
          (e.telegram_ok ? "ok (simulado en esta corrida)" : "falló")
      );
      lineas.push("  └─ sqlite: evento #" + e.id + " guardado");
    }
    lineas.push("");
    lineas.push("[fin] " + eventos.length + " eventos procesados en la corrida real");
    return lineas;
  }

  function mostrarTodo(lineas) {
    pantalla.textContent = lineas.join("\n");
  }

  function animar(lineas) {
    let i = 1; // la primera línea ya está en el HTML
    pantalla.textContent = lineas[0] + "\n";
    (function paso() {
      if (i >= lineas.length) {
        setTimeout(() => animar(lineas), 6000); // reinicia el ciclo
        return;
      }
      pantalla.textContent += lineas[i] + "\n";
      i++;
      const esEvento = lineas[i - 1].includes("evento:");
      setTimeout(paso, esEvento ? 900 : 260);
    })();
  }

  fetch("data/eventos-ejemplo.json")
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
    .then((d) => {
      const lineas = lineasDe(d.eventos || []);
      reducir ? mostrarTodo(lineas) : animar(lineas);
    })
    .catch(() => {
      pantalla.textContent += "(sin datos: corré `generar-datos` para regenerarlos)";
    });
})();
