const API = "/api";

let maximoInicial = null;

// ── Zapato visual ─────────────────────────────────────────

function colorBarra(valorCarta) {
  if (valorCarta >= 10) return "alta";
  if (valorCarta >= 7) return "media";
  return "baja";
}

function mostrarZapato(conteo) {
  if (!conteo) return;

  const totalCartas = conteo.reduce((a, b) => a + b, 0);
  if (!maximoInicial) {
    maximoInicial = [...conteo];
  }

  const etiquetas = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
  const contenedor = document.getElementById("shoe-display");
  contenedor.innerHTML = "";

  etiquetas.forEach((etq, i) => {
    const cantidad = conteo[i];
    const maximo = maximoInicial[i] || 1;
    const ancho = Math.max((cantidad / maximo) * 100, 1);
    const porcentaje = totalCartas > 0 ? (cantidad / totalCartas) * 100 : 0;

    const valorCarta = i + 1;
    const claseColor = colorBarra(valorCarta);

    const fila = document.createElement("div");
    fila.className = "shoe-row";
    fila.innerHTML = `
      <span class="shoe-label">${etq}</span>
      <div class="shoe-bar-outer">
        <div class="shoe-bar-inner ${claseColor}" style="width:${ancho}%"></div>
        <span class="shoe-bar-count">${cantidad}</span>
      </div>
      <span class="shoe-bar-pct">${porcentaje.toFixed(1)}%</span>
    `;
    contenedor.appendChild(fila);
  });

  document.getElementById("shoe-total").textContent = totalCartas;
}

// ── Resultados ────────────────────────────────────────────

function mostrarResultados(datos) {
  const seccion = document.getElementById("results-section");
  seccion.classList.remove("hidden");

  // Resumen mano
  document.getElementById("res-cartas").textContent = datos.mano.cartas.join(", ");
  document.getElementById("res-total").textContent = datos.mano.total;
  document.getElementById("res-suave").classList.toggle("hidden", !datos.mano.es_suave);

  // Numeros grandes
  document.getElementById("res-pasarse").textContent = datos.probabilidad_pasarse.toFixed(1) + "%";
  document.getElementById("res-no-pasarse").textContent = (100 - datos.probabilidad_pasarse).toFixed(1) + "%";
  document.getElementById("res-carta-top").textContent = datos.carta_mas_probable;

  // Tabla
  const tbody = document.querySelector("#tabla-probs tbody");
  tbody.innerHTML = "";

  const maxProb = datos.tabla.length > 0 ? datos.tabla[0].probabilidad : 100;

  datos.tabla.forEach((fila, idx) => {
    const tr = document.createElement("tr");
    tr.className = fila.pasado ? "fila-pasado" : "fila-ok";
    if (idx === 0) tr.classList.add("fila-top");

    const barraColor = fila.pasado ? "mal" : "ok";
    const anchoBarra = (fila.probabilidad / maxProb) * 100;

    const resultadoTexto = fila.pasado
      ? "PASADO"
      : "Total " + fila.nuevo_total;

    tr.innerHTML = `
      <td><span class="prob-barra ${barraColor}" style="width:${anchoBarra * 0.6}px"></span>${fila.carta}</td>
      <td>${fila.probabilidad.toFixed(2)}%</td>
      <td>${fila.pasado ? "-" : fila.nuevo_total}</td>
      <td>${resultadoTexto}</td>
    `;
    tbody.appendChild(tr);
  });

  // Zapato
  mostrarZapato(datos.zapato.conteo);
}

// ── Peticiones a la API ───────────────────────────────────

async function configurar() {
  const mazos = parseInt(document.getElementById("cfg-decks").value);

  const resp = await fetch(API + "/configurar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cantidad_mazos: mazos }),
  });
  const datos = await resp.json();

  if (resp.ok) {
    document.getElementById("config-status").textContent = "✔ Listo";
    document.getElementById("config-status").style.color = "var(--green)";
    maximoInicial = null;

    document.getElementById("shoe-section").classList.remove("hidden");
    document.getElementById("calc-section").classList.remove("hidden");

    mostrarZapato(datos.conteo);
  } else {
    document.getElementById("config-status").textContent = "✖ Error";
    document.getElementById("config-status").style.color = "var(--red)";
  }
}

async function calcular() {
  const misCartas = document.getElementById("input-mis").value.trim();
  const cartasOtros = document.getElementById("input-otros").value.trim();

  if (!misCartas) {
    alert("Ingresa tus cartas.");
    return;
  }

  const resp = await fetch(API + "/probabilidades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mis_cartas: misCartas,
      cartas_otros: cartasOtros,
    }),
  });
  const datos = await resp.json();

  if (resp.ok) {
    mostrarResultados(datos);
  } else {
    alert("Error: " + (datos.detail || "Revisa el formato de las cartas"));
  }
}

async function actualizar() {
  const misCartas = document.getElementById("input-mis").value.trim();
  const cartasOtros = document.getElementById("input-otros").value.trim();

  if (!misCartas) {
    alert("Ingresa tus cartas para actualizar.");
    return;
  }

  const resp = await fetch(API + "/actualizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mis_cartas: misCartas,
      cartas_otros: cartasOtros,
    }),
  });
  const datos = await resp.json();

  if (resp.ok) {
    document.getElementById("update-status").textContent = "✔ " + datos.mensaje;
    document.getElementById("update-status").style.color = "var(--green)";
    mostrarZapato(datos.conteo);
  } else {
    document.getElementById("update-status").textContent = "✖ Error";
    document.getElementById("update-status").style.color = "var(--red)";
  }
}

// ── Eventos ───────────────────────────────────────────────

document.getElementById("btn-config").addEventListener("click", configurar);
document.getElementById("btn-calc").addEventListener("click", calcular);
document.getElementById("btn-actualizar").addEventListener("click", actualizar);
