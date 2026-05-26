const API = "/api";

let shoeState = null;

const suits = ["spades", "hearts", "diamonds", "clubs"];
let suitIndex = 0;

function nextSuit() {
  const s = suits[suitIndex % 4];
  suitIndex++;
  return s;
}

function suitSymbol(suit) {
  return { spades: "♠", hearts: "♥", diamonds: "♦", clubs: "♣" }[suit];
}

function suitColor(suit) {
  return (suit === "hearts" || suit === "diamonds") ? "red" : "black";
}

function rankShort(rank) {
  const r = rank.trim().toUpperCase();
  if (r === "10") return "10";
  if (r.length > 1) return r.charAt(0);
  return r;
}

function createCardElement(rank, suit) {
  const card = document.createElement("div");
  card.className = "playing-card " + suitColor(suit);
  const sym = suitSymbol(suit);
  const rs = rankShort(rank);

  card.innerHTML = `
    <div class="corner-top"><span>${rs}</span><span class="suit-icon">${sym}</span></div>
    <div class="center-suit">${sym}</div>
    <div class="corner-bot"><span>${rs}</span><span class="suit-icon">${sym}</span></div>
  `;
  return card;
}

function renderPlayerCards(cardsStr) {
  const preview = document.getElementById("player-preview");
  preview.innerHTML = "";
  suitIndex = 0;
  const cards = cardsStr.split(",").map(c => c.trim()).filter(Boolean);
  cards.forEach(c => {
    const suit = nextSuit();
    preview.appendChild(createCardElement(c, suit));
  });
}

function renderDealerCard(cardStr) {
  const preview = document.getElementById("dealer-preview");
  preview.innerHTML = "";
  const c = cardStr.trim();
  if (!c) return;
  preview.appendChild(createCardElement(c, "spades"));
}

function renderShoe(data) {
  if (!data || !data.remaining) return;
  shoeState = data;
  const container = document.getElementById("shoe-display");
  container.innerHTML = "";
  const order = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
  order.forEach(label => {
    const cnt = data.by_label[label];
    const div = document.createElement("div");
    div.className = "shoe-card";
    div.innerHTML = `<span class="label">${label}</span><span class="count">${cnt}</span>`;
    container.appendChild(div);
  });
  document.getElementById("shoe-total").textContent = data.total_remaining;
}

function renderResults(data) {
  const section = document.getElementById("results-section");
  section.classList.remove("hidden");

  document.getElementById("res-player-cards").textContent = data.jugador.cartas.join(", ");
  document.getElementById("res-player-total").textContent = data.jugador.total;

  const softBadge = document.getElementById("res-player-soft");
  softBadge.classList.toggle("hidden", !data.jugador.es_suave);

  const bjBadge = document.getElementById("res-player-bj");
  bjBadge.classList.toggle("hidden", !data.jugador.es_blackjack);

  document.getElementById("res-dealer-card").textContent = data.crupier.carta_visible;

  const evGrid = document.getElementById("ev-results");
  evGrid.innerHTML = "";
  for (const [action, info] of Object.entries(data.acciones)) {
    const card = document.createElement("div");
    card.className = "ev-card";
    if (info.recomendada) card.classList.add("recommended");
    const ev = info.valor_esperado;
    if (ev > 0.001) card.classList.add("ev-positive");
    else if (ev < -0.001) card.classList.add("ev-negative");
    else card.classList.add("ev-neutral");
    card.innerHTML = `
      <div class="action-name">${action}</div>
      <div class="action-ev">${ev >= 0 ? "+" : ""}${ev.toFixed(4)}</div>
    `;
    evGrid.appendChild(card);
  }

  const distGrid = document.getElementById("dealer-dist");
  distGrid.innerHTML = "";
  const maxPct = Math.max(...Object.values(data.crupier.distribucion_final), 1);
  for (const [label, pct] of Object.entries(data.crupier.distribucion_final)) {
    const wrap = document.createElement("div");
    wrap.className = "dist-bar-wrap";
    wrap.innerHTML = `
      <div class="dist-label">${label}</div>
      <div class="dist-bar" style="width:${Math.max((pct / maxPct) * 100, 2)}%"></div>
      <div class="dist-pct">${pct.toFixed(1)}%</div>
    `;
    distGrid.appendChild(wrap);
  }

  renderShoe(data.zapato);
}

async function configure() {
  const payload = {
    num_decks: parseInt(document.getElementById("cfg-decks").value),
    dealer_stands_soft_17: document.getElementById("cfg-s17").value === "stand",
    double_any_two: document.getElementById("cfg-double").value === "any",
    double_9_10_11_only: document.getElementById("cfg-double").value === "9_11",
    double_10_11_only: document.getElementById("cfg-double").value === "10_11",
    double_after_split: document.getElementById("cfg-das").value === "yes",
    max_splits: parseInt(document.getElementById("cfg-splits").value),
    late_surrender: document.getElementById("cfg-surrender").value === "late",
    blackjack_pays: parseFloat(document.getElementById("cfg-bjpay").value),
    resplit_aces: true,
  };

  const res = await fetch(API + "/configurar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (res.ok) {
    document.getElementById("config-status").textContent = "✔ Configurada";
    document.getElementById("config-status").style.color = "var(--green)";

    document.getElementById("shoe-section").classList.remove("hidden");
    document.getElementById("calc-section").classList.remove("hidden");

    renderShoe(data.zapato);
  } else {
    document.getElementById("config-status").textContent = "✖ Error";
    document.getElementById("config-status").style.color = "var(--red)";
  }
}

async function calculate() {
  const playerCards = document.getElementById("input-player").value;
  const dealerCard = document.getElementById("input-dealer").value.trim();

  if (!playerCards || !dealerCard) {
    alert("Ingresa tus cartas y la carta del crupier.");
    return;
  }

  const res = await fetch(API + "/calcular", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_cards: playerCards, dealer_upcard: dealerCard }),
  });
  const data = await res.json();

  if (res.ok) {
    renderResults(data);
  } else {
    alert("Error: " + (data.detail || "Verifica el formato de las cartas"));
  }
}

async function resolveHand() {
  const cards = document.getElementById("input-resolve").value;
  if (!cards.trim()) return;

  const res = await fetch(API + "/actualizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cards_to_remove: cards }),
  });
  const data = await res.json();

  if (res.ok) {
    document.getElementById("resolve-status").textContent = "✔ Zapato actualizado";
    document.getElementById("resolve-status").style.color = "var(--green)";
    renderShoe(data.zapato);
  } else {
    document.getElementById("resolve-status").textContent = "✖ Error";
    document.getElementById("resolve-status").style.color = "var(--red)";
  }
}

document.getElementById("btn-config").addEventListener("click", configure);
document.getElementById("btn-calculate").addEventListener("click", calculate);
document.getElementById("btn-resolve").addEventListener("click", resolveHand);

document.getElementById("input-player").addEventListener("input", function () {
  renderPlayerCards(this.value);
});

document.getElementById("input-dealer").addEventListener("input", function () {
  renderDealerCard(this.value);
});

document.querySelectorAll(".chip-btn").forEach(btn => {
  btn.addEventListener("click", function () {
    const dealerInput = document.getElementById("input-dealer");
    dealerInput.value = this.dataset.card;
    renderDealerCard(this.dataset.card);
    document.querySelectorAll(".chip-btn").forEach(b => b.classList.remove("sel"));
    this.classList.add("sel");
  });
});
