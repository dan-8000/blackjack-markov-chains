const API = "/api";

let estadoZapato = null;

const palos = ["spades", "hearts", "diamonds", "clubs"];
let indicePalo = 0;

function siguientePalo() {
  const palo = palos[indicePalo % 4];
  indicePalo++;
  return palo;
}

function simboloPalo(palo) {
  return { spades: "♠", hearts: "♥", diamonds: "♦", clubs: "♣" }[palo];
}

function colorPalo(palo) {
  return palo === "hearts" || palo === "diamonds" ? "red" : "black";
}

function rangoCorto(rango) {
  const r = rango.trim().toUpperCase();
  if (r === "10") return "10";
  if (r.length > 1) return r.charAt(0);
  return r;
}

function crearElementoCarta(rango, palo) {
  const carta = document.createElement("div");
  carta.className = "playing-card " + colorPalo(palo);
  const simbolo = simboloPalo(palo);
  const rs = rangoCorto(rango);

  carta.innerHTML = `
    <div class="corner-top"><span>${rs}</span><span class="suit-icon">${simbolo}</span></div>
    <div class="center-suit">${simbolo}</div>
    <div class="corner-bot"><span>${rs}</span><span class="suit-icon">${simbolo}</span></div>
  `;
  return carta;
}

function mostrarCartasJugador(textoCartas) {
  const previsualizacion = document.getElementById("player-preview");
  previsualizacion.innerHTML = "";
  indicePalo = 0;
  const cartas = textoCartas.split(",").map(c => c.trim()).filter(Boolean);
  cartas.forEach(c => {
    const palo = siguientePalo();
    previsualizacion.appendChild(crearElementoCarta(c, palo));
  });
}

function mostrarCartaCrupier(textoCarta) {
  const previsualizacion = document.getElementById("dealer-preview");
  previsualizacion.innerHTML = "";
  const c = textoCarta.trim();
  if (!c) return;
  previsualizacion.appendChild(crearElementoCarta(c, "spades"));
}

function mostrarZapato(datos) {
  if (!datos || !datos.restantes) return;
  estadoZapato = datos;
  const contenedor = document.getElementById("shoe-display");
  contenedor.innerHTML = "";
  const orden = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
  orden.forEach(etiqueta => {
    const cantidad = datos.por_etiqueta[etiqueta];
    const div = document.createElement("div");
    div.className = "shoe-card";
    div.innerHTML = `<span class="label">${etiqueta}</span><span class="count">${cantidad}</span>`;
    contenedor.appendChild(div);
  });
  document.getElementById("shoe-total").textContent = datos.total_restante;
}

function mostrarResultados(datos) {
  const seccion = document.getElementById("results-section");
  seccion.classList.remove("hidden");

  document.getElementById("res-player-cards").textContent = datos.jugador.cartas.join(", ");
  document.getElementById("res-player-total").textContent = datos.jugador.total;

  const insigniaSuave = document.getElementById("res-player-soft");
  insigniaSuave.classList.toggle("hidden", !datos.jugador.es_suave);

  const insigniaBJ = document.getElementById("res-player-bj");
  insigniaBJ.classList.toggle("hidden", !datos.jugador.es_blackjack);

  document.getElementById("res-dealer-card").textContent = datos.crupier.carta_visible;

  const rejillaEV = document.getElementById("ev-results");
  rejillaEV.innerHTML = "";
  for (const [accion, info] of Object.entries(datos.acciones)) {
    const tarjeta = document.createElement("div");
    tarjeta.className = "ev-card";
    if (info.recomendada) tarjeta.classList.add("recommended");
    const ve = info.valor_esperado;
    if (ve > 0.001) tarjeta.classList.add("ev-positive");
    else if (ve < -0.001) tarjeta.classList.add("ev-negative");
    else tarjeta.classList.add("ev-neutral");
    tarjeta.innerHTML = `
      <div class="action-name">${accion}</div>
      <div class="action-ev">${ve >= 0 ? "+" : ""}${ve.toFixed(4)}</div>
    `;
    rejillaEV.appendChild(tarjeta);
  }

  const rejillaDist = document.getElementById("dealer-dist");
  rejillaDist.innerHTML = "";
  const maxPorcentaje = Math.max(...Object.values(datos.crupier.distribucion_final), 1);
  for (const [etiqueta, porcentaje] of Object.entries(datos.crupier.distribucion_final)) {
    const envoltura = document.createElement("div");
    envoltura.className = "dist-bar-wrap";
    envoltura.innerHTML = `
      <div class="dist-label">${etiqueta}</div>
      <div class="dist-bar" style="width:${Math.max((porcentaje / maxPorcentaje) * 100, 2)}%"></div>
      <div class="dist-pct">${porcentaje.toFixed(1)}%</div>
    `;
    rejillaDist.appendChild(envoltura);
  }

  mostrarZapato(datos.zapato);
}

async function configurarPartida() {
  const carga = {
    cantidad_mazos: parseInt(document.getElementById("cfg-decks").value),
    crupier_se_planta_suave_17: document.getElementById("cfg-s17").value === "stand",
    doblar_cualquier_par: document.getElementById("cfg-double").value === "any",
    doblar_solo_9_10_11: document.getElementById("cfg-double").value === "9_11",
    doblar_solo_10_11: document.getElementById("cfg-double").value === "10_11",
    doblar_tras_dividir: document.getElementById("cfg-das").value === "yes",
    maximas_divisiones: parseInt(document.getElementById("cfg-splits").value),
    rendicion_tardia: document.getElementById("cfg-surrender").value === "late",
    pago_blackjack: parseFloat(document.getElementById("cfg-bjpay").value),
    redividir_ases: true,
  };

  const respuesta = await fetch(API + "/configurar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(carga),
  });
  const datos = await respuesta.json();

  if (respuesta.ok) {
    document.getElementById("config-status").textContent = "✔ Configurada";
    document.getElementById("config-status").style.color = "var(--green)";

    document.getElementById("shoe-section").classList.remove("hidden");
    document.getElementById("calc-section").classList.remove("hidden");

    mostrarZapato(datos.zapato);
  } else {
    document.getElementById("config-status").textContent = "✖ Error";
    document.getElementById("config-status").style.color = "var(--red)";
  }
}

async function calcularJugada() {
  const cartasJugador = document.getElementById("input-player").value;
  const cartaCrupier = document.getElementById("input-dealer").value.trim();

  if (!cartasJugador || !cartaCrupier) {
    alert("Ingresa tus cartas y la carta del crupier.");
    return;
  }

  const respuesta = await fetch(API + "/calcular", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cartas_jugador: cartasJugador,
      carta_visible_crupier: cartaCrupier,
    }),
  });
  const datos = await respuesta.json();

  if (respuesta.ok) {
    mostrarResultados(datos);
  } else {
    alert("Error: " + (datos.detail || "Verifica el formato de las cartas"));
  }
}

async function resolverMano() {
  const cartas = document.getElementById("input-resolve").value;
  if (!cartas.trim()) return;

  const respuesta = await fetch(API + "/actualizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cartas_a_remover: cartas }),
  });
  const datos = await respuesta.json();

  if (respuesta.ok) {
    document.getElementById("resolve-status").textContent = "✔ Zapato actualizado";
    document.getElementById("resolve-status").style.color = "var(--green)";
    mostrarZapato(datos.zapato);
  } else {
    document.getElementById("resolve-status").textContent = "✖ Error";
    document.getElementById("resolve-status").style.color = "var(--red)";
  }
}

document.getElementById("btn-config").addEventListener("click", configurarPartida);
document.getElementById("btn-calculate").addEventListener("click", calcularJugada);
document.getElementById("btn-resolve").addEventListener("click", resolverMano);

document.getElementById("input-player").addEventListener("input", function () {
  mostrarCartasJugador(this.value);
});

document.getElementById("input-dealer").addEventListener("input", function () {
  mostrarCartaCrupier(this.value);
});

document.querySelectorAll(".chip-btn").forEach(boton => {
  boton.addEventListener("click", function () {
    const entradaCrupier = document.getElementById("input-dealer");
    entradaCrupier.value = this.dataset.card;
    mostrarCartaCrupier(this.dataset.card);
    document.querySelectorAll(".chip-btn").forEach(b => b.classList.remove("sel"));
    this.classList.add("sel");
  });
});
