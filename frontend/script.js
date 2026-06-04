const API = "/api";

let sesionActiva = false;
let maximoInicial = null;
let temporizador = null;

// ── Zapato compacto ──────────────────────────────────────

function colorBarra(valor) {
  if (valor >= 10) return "alta";
  if (valor >= 7) return "media";
  return "baja";
}

function mostrarZapatoCompacto(conteo) {
  if (!conteo) return;
  if (!maximoInicial) maximoInicial = [...conteo];

  const etiquetas = ["A","2","3","4","5","6","7","8","9","10"];
  const totalCartas = conteo.reduce((a,b) => a+b, 0);
  const contenedor = document.getElementById("shoe-display");
  contenedor.innerHTML = "";

  etiquetas.forEach((etq, i) => {
    const cantidad = conteo[i];
    const maximo = maximoInicial[i] || 1;
    const ancho = Math.max((cantidad / maximo) * 100, 3);
    const porcentaje = totalCartas > 0 ? (cantidad / totalCartas) * 100 : 0;
    const clase = colorBarra(i + 1);

    const mini = document.createElement("div");
    mini.className = "shoe-mini";
    mini.innerHTML = `
      <div class="etq">${etq}</div>
      <div class="barra ${clase}" style="width:${ancho}%"></div>
      <div class="cnt">${cantidad}</div>
      <div class="pct">${porcentaje.toFixed(0)}%</div>
    `;
    contenedor.appendChild(mini);
  });

  document.getElementById("shoe-total").textContent = totalCartas;
}

// ── Resultados ───────────────────────────────────────────

function mostrarResultados(datos) {
  document.getElementById("results-section").classList.remove("hidden");

  document.getElementById("res-cartas").textContent = datos.mano.cartas.join(", ");
  document.getElementById("res-total").textContent = datos.mano.total;
  document.getElementById("res-suave").classList.toggle("hidden", !datos.mano.es_suave);

  const tbody = document.querySelector("#tabla-probs tbody");
  tbody.innerHTML = "";

  const maxProb = datos.tabla.length > 0 ? datos.tabla[0].probabilidad : 100;

  datos.tabla.forEach((fila, idx) => {
    const tr = document.createElement("tr");
    tr.className = fila.pasado ? "pasado" : "";
    if (idx === 0) tr.classList.add("top");

    const clsBarra = fila.pasado ? "mal" : "ok";
    const wBarra = (fila.probabilidad / maxProb) * 70;
    const resultado = fila.pasado ? "SÍ" : fila.nuevo_total;

    tr.innerHTML = `
      <td><span class="barra-prob ${clsBarra}" style="width:${wBarra}px"></span>${fila.carta}</td>
      <td>${fila.probabilidad.toFixed(1)}%</td>
      <td>${fila.pasado ? "-" : fila.nuevo_total}</td>
      <td>${resultado}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("res-pasarse").textContent = datos.probabilidad_pasarse.toFixed(1) + "%";
  document.getElementById("res-no-pasarse").textContent = (100 - datos.probabilidad_pasarse).toFixed(1) + "%";
  document.getElementById("res-carta-top").textContent = datos.carta_mas_probable;

  mostrarZapatoCompacto(datos.zapato.conteo);
}

// ── API calls ────────────────────────────────────────────

async function apiConfigurar() {
  const mazos = parseInt(document.getElementById("cfg-decks").value);
  const resp = await fetch(API + "/configurar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cantidad_mazos: mazos }),
  });
  const datos = await resp.json();
  if (resp.ok) {
    sesionActiva = true;
    maximoInicial = null;
    document.getElementById("config-status").textContent = "✔ Listo";
    document.getElementById("config-status").style.color = "var(--green)";
    document.getElementById("shoe-section").classList.remove("hidden");
    mostrarZapatoCompacto(datos.conteo);
    actualizarAutomatico();
  } else {
    document.getElementById("config-status").textContent = "✖ Error";
    document.getElementById("config-status").style.color = "var(--red)";
  }
}

async function apiProbabilidades() {
  if (!sesionActiva) return;

  const misCartas = document.getElementById("input-mis").value.trim();
  if (!misCartas) {
    document.getElementById("results-section").classList.add("hidden");
    return;
  }

  const cartasOtros = document.getElementById("input-otros").value.trim();

  const resp = await fetch(API + "/probabilidades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mis_cartas: misCartas, cartas_otros: cartasOtros }),
  });
  const datos = await resp.json();
  if (resp.ok) mostrarResultados(datos);
}

async function apiActualizar() {
  if (!sesionActiva) return;

  const misCartas = document.getElementById("input-mis").value.trim();
  const cartasOtros = document.getElementById("input-otros").value.trim();

  if (!misCartas) return;

  const resp = await fetch(API + "/actualizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mis_cartas: misCartas, cartas_otros: cartasOtros }),
  });
  const datos = await resp.json();
  if (resp.ok) {
    document.getElementById("update-status").textContent = "✔ " + datos.mensaje;
    document.getElementById("update-status").style.color = "var(--green)";
    maximoInicial = null;
    mostrarZapatoCompacto(datos.conteo);
    actualizarAutomatico();
  } else {
    document.getElementById("update-status").textContent = "✖ Error";
    document.getElementById("update-status").style.color = "var(--red)";
  }
}

// ── Auto-update con debounce ─────────────────────────────

function actualizarAutomatico() {
  clearTimeout(temporizador);
  temporizador = setTimeout(apiProbabilidades, 400);
}

// ── Eventos ──────────────────────────────────────────────

document.getElementById("btn-config").addEventListener("click", apiConfigurar);
document.getElementById("btn-actualizar").addEventListener("click", apiActualizar);

document.getElementById("input-mis").addEventListener("input", actualizarAutomatico);
document.getElementById("input-otros").addEventListener("input", actualizarAutomatico);
