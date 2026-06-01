const API = "/api";

let estadoZapato = null;
let maximoInicial = null;

const palos = ["spades", "hearts", "diamonds", "clubs"];
let indicePalo = 0;

function siguientePalo() {
  const palo = palos[indicePalo % 4];
  indicePalo++;
  return palo;
}

function simboloPalo(palo) {
  return { spades: "\u2660", hearts: "\u2665", diamonds: "\u2666", clubs: "\u2663" }[palo];
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

function figuraDecorativa(rango) {
  const r = rango.trim().toUpperCase();
  if (r === "J" || r === "JACK" || r === "JOTA") return "\u265E";
  if (r === "Q" || r === "QUEEN" || r === "REINA") return "\u265B";
  if (r === "K" || r === "KING" || r === "REY") return "\u265A";
  return null;
}

function crearElementoCarta(rango, palo) {
  const carta = document.createElement("div");
  carta.className = "playing-card " + colorPalo(palo);
  const simbolo = simboloPalo(palo);
  const rs = rangoCorto(rango);
  const figura = figuraDecorativa(rango);

  let centro;
  if (figura) {
    centro = `<div class="center-figure"><span>${figura}</span></div>`;
  } else {
    centro = `<div class="center-suit">${simbolo}</div>`;
  }

  carta.innerHTML = `
    <div class="corner-top"><span>${rs}</span><span class="suit-icon">${simbolo}</span></div>
    ${centro}
    <div class="corner-bot"><span>${rs}</span><span class="suit-icon">${simbolo}</span></div>
  `;
  return carta;
}

function mostrarCartas(contenedorId, textoCartas) {
  const previsualizacion = document.getElementById(contenedorId);
  previsualizacion.innerHTML = "";
  const cartas = textoCartas.split(",").map(c => c.trim()).filter(Boolean);
  if (cartas.length === 0) return;
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

function barColor(value) {
  if (value >= 10) return "high";
  if (value >= 7) return "neutral";
  return "low";
}

function mostrarZapato(datos) {
  if (!datos || !datos.restantes) return;
  estadoZapato = datos;

  if (!maximoInicial) {
    maximoInicial = {};
    const orden = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
    orden.forEach(etiqueta => {
      maximoInicial[etiqueta] = datos.por_etiqueta[etiqueta];
    });
  }

  const contenedor = document.getElementById("shoe-display");
  contenedor.innerHTML = "";
  const totalCartas = datos.total_restante;
  const orden = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

  orden.forEach(etiqueta => {
    const cantidad = datos.por_etiqueta[etiqueta];
    const maximo = maximoInicial[etiqueta] || 1;
    const porcentaje = totalCartas > 0 ? (cantidad / totalCartas) * 100 : 0;
    const ancho = (cantidad / maximo) * 100;

    const fila = document.createElement("div");
    fila.className = "shoe-row";
    fila.innerHTML = `
      <span class="shoe-label">${etiqueta}</span>
      <div class="shoe-bar-outer">
        <div class="shoe-bar-inner ${barColor(parseInt(etiqueta) || 1)}" style="width:${Math.max(ancho, 1)}%"></div>
        <span class="shoe-bar-count">${cantidad}</span>
      </div>
      <span class="shoe-bar-pct">${porcentaje.toFixed(1)}%</span>
    `;
    contenedor.appendChild(fila);
  });

  document.getElementById("shoe-total").textContent = totalCartas;
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
  const porcentajes = Object.values(datos.crupier.distribucion_final);
  const maxPorcentaje = Math.max(...porcentajes, 1);
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
    document.getElementById("config-status").textContent = "\u2714 Configurada";
    document.getElementById("config-status").style.color = "var(--green)";

    maximoInicial = null;
    document.getElementById("shoe-section").classList.remove("hidden");
    document.getElementById("calc-section").classList.remove("hidden");

    mostrarZapato(datos.zapato);
  } else {
    document.getElementById("config-status").textContent = "\u2716 Error";
    document.getElementById("config-status").style.color = "var(--red)";
  }
}

async function calcularJugada() {
  const cartasJugador = document.getElementById("input-player").value;
  const cartaCrupier = document.getElementById("input-dealer").value.trim();
  const cartasOtros = document.getElementById("input-others").value;

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
      cartas_otros: cartasOtros,
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
    document.getElementById("resolve-status").textContent = "\u2714 Zapato actualizado";
    document.getElementById("resolve-status").style.color = "var(--green)";
    mostrarZapato(datos.zapato);
  } else {
    document.getElementById("resolve-status").textContent = "\u2716 Error";
    document.getElementById("resolve-status").style.color = "var(--red)";
  }
}

document.getElementById("btn-config").addEventListener("click", configurarPartida);
document.getElementById("btn-calculate").addEventListener("click", calcularJugada);
document.getElementById("btn-resolve").addEventListener("click", resolverMano);

document.getElementById("input-player").addEventListener("input", function () {
  mostrarCartas("player-preview", this.value);
});

document.getElementById("input-others").addEventListener("input", function () {
  mostrarCartas("others-preview", this.value);
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
