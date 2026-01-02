/* Digital Workflow — app.js (per il tuo index.html con #top-stories, #latest-list, #most-read, IA panels) */

let ALL_ITEMS = [];
let FILTERED_ITEMS = [];
let CURRENT_TOPIC = "tutte";
let CURRENT_QUERY = "";
let LATEST_PAGE = 0;
const LATEST_PAGE_SIZE = 12;

const elTop = document.getElementById("top-stories");
const elLatest = document.getElementById("latest-list");
const elMostRead = document.getElementById("most-read");
const btnLoadMore = document.getElementById("load-more");
const inputQ = document.getElementById("q");

function safeText(x) { return String(x ?? "").trim(); }
function norm(x) { return safeText(x).toLowerCase(); }

function parseItems(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  return [];
}

function inferTopic(item) {
  const base = (safeText(item.titolo) + " " + safeText(item.descrizione)).toLowerCase();
  if (/(notion)/.test(base)) return "notion";
  if (/(canva)/.test(base)) return "canva";
  if (/(clickup)/.test(base)) return "clickup";
  if (/(riunion|meeting)/.test(base)) return "riunioni";
  if (/(ai|ia|gpt|openai|gemini|claude|copilot|llm|mistral|llama|anthropic)/.test(base)) return "ia";
  if (/(zapier|make\.com|n8n|automaz|integraz|workflow)/.test(base)) return "automazioni";
  if (/(produtt|focus|pomodoro|abitud|organizz|gestione tempo)/.test(base)) return "produttività";
  return "strumenti";
}

function getTopic(item) {
  const t = norm(item.categoria || "");
  return t || inferTopic(item);
}

function toDateLabel(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
}

function cardHTML(item, compact = false) {
  const titolo = safeText(item.titolo) || "(senza titolo)";
  const descr = safeText(item.descrizione);
  const fonte = safeText(item.fonte);
  const link = safeText(item.link);
  const img = safeText(item.image);
  const data = safeText(item.data);
  const topic = getTopic(item);

  const imgHtml = img ? `<div class="thumb"><img src="${img}" alt="" loading="lazy"></div>` : "";

  const meta = `
    <div class="meta">
      ${data ? `<span class="date">${toDateLabel(data)}</span>` : ""}
      ${fonte ? `<span class="source">${fonte}</span>` : ""}
      ${topic ? `<span class="topic">${topic}</span>` : ""}
    </div>
  `;

  const p = compact ? "" : (descr ? `<p>${descr}</p>` : "");

  return `
    <a class="item ${compact ? "compact" : ""}" href="${link}" target="_blank" rel="noopener">
      ${imgHtml}
      <div class="content">
        ${meta}
        <h3>${titolo}</h3>
        ${p}
      </div>
    </a>
  `;
}

function renderTop(items) {
  if (!elTop) return;
  elTop.innerHTML = items.slice(0, 6).map(i => cardHTML(i, false)).join("");
}

function renderLatest(items) {
  if (!elLatest) return;
  const end = (LATEST_PAGE + 1) * LATEST_PAGE_SIZE;
  const slice = items.slice(0, end);
  elLatest.innerHTML = slice.map(i => cardHTML(i, false)).join("");

  if (btnLoadMore) {
    btnLoadMore.style.display = (items.length > slice.length) ? "inline-block" : "none";
  }
}

function renderMostRead(items) {
  if (!elMostRead) return;
  const pick = [];
  const seen = new Set();
  for (const it of items) {
    const k = it.link || it.titolo;
    if (!k || seen.has(k)) continue;
    pick.push(it);
    seen.add(k);
    if (pick.length >= 6) break;
  }
  elMostRead.innerHTML = pick.map(i => cardHTML(i, true)).join("");
}

function applyFilters() {
  const q = norm(CURRENT_QUERY);
  const topic = norm(CURRENT_TOPIC);

  FILTERED_ITEMS = ALL_ITEMS.filter(it => {
    const t = getTopic(it);
    if (topic !== "tutte" && t !== topic) return false;

    if (q) {
      const text = (safeText(it.titolo) + " " + safeText(it.descrizione) + " " + safeText(it.fonte)).toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  });

  LATEST_PAGE = 0;
  renderTop(FILTERED_ITEMS);
  renderLatest(FILTERED_ITEMS);
  renderMostRead(FILTERED_ITEMS);
}

function bindTopics() {
  const btns = document.querySelectorAll(".topics .topic");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      CURRENT_TOPIC = btn.dataset.topic || "tutte";
      applyFilters();
    });
  });
}

// 🔒 fetch robusto: prova sia /data/... sia data/... (così funziona anche se finisci su sottopercorsi)
async function fetchJsonSmart(primary, fallback) {
  const tryFetch = async (u) => {
    const res = await fetch(u + (u.includes("?") ? "" : "?") + "nocache=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error(`${u} -> ${res.status}`);
    return res.json();
  };
  try {
    return await tryFetch(primary);
  } catch (_) {
    return await tryFetch(fallback);
  }
}

async function loadArticoli() {
  const data = await fetchJsonSmart("/data/articoli.json", "data/articoli.json");
  return parseItems(data);
}

async function loadIA() {
  try {
    const data = await fetchJsonSmart("/data/ia.json", "data/ia.json");
    return parseItems(data);
  } catch {
    return [];
  }
}

function renderIA(iaItems) {
  const slots = document.querySelectorAll(".ia-article[data-model]");
  if (!slots.length) return;

  const byModel = new Map();
  iaItems.forEach(it => {
    const m = norm(it.modello || "");
    if (m) byModel.set(m, it);
  });

  slots.forEach(slot => {
    const model = norm(slot.dataset.model || "");
    const it = byModel.get(model);

    if (!it) {
      slot.innerHTML = `<p class="muted">Nessuna novità recente.</p>`;
      return;
    }

    const titolo = safeText(it.titolo) || "(senza titolo)";
    const descr = safeText(it.descrizione);
    const fonte = safeText(it.fonte);
    const link = safeText(it.link);
    const img = safeText(it.image);

    slot.innerHTML = `
      <a class="ia-item" href="${link}" target="_blank" rel="noopener">
        ${img ? `<img src="${img}" alt="" loading="lazy">` : ""}
        <div>
          <div class="meta">${fonte ? `<span class="source">${fonte}</span>` : ""}</div>
          <h4>${titolo}</h4>
          ${descr ? `<p>${descr}</p>` : ""}
        </div>
      </a>
    `;
  });
}

/* Funzioni chiamate dal tuo HTML */
window.applySearch = function () {
  CURRENT_QUERY = inputQ ? inputQ.value : "";
  applyFilters();
};
window.resetSearch = function () {
  CURRENT_QUERY = "";
  if (inputQ) inputQ.value = "";
  applyFilters();
};
window.loadMore = function () {
  LATEST_PAGE += 1;
  renderLatest(FILTERED_ITEMS);
};

async function init() {
  try {
    if (elLatest) elLatest.innerHTML = `<p class="muted">Caricamento…</p>`;

    ALL_ITEMS = await loadArticoli();
    bindTopics();
    applyFilters();

    const iaItems = await loadIA();
    renderIA(iaItems);
  } catch (e) {
    console.error("[DW] Errore init:", e);
    if (elLatest) elLatest.innerHTML = `<p class="muted">Errore nel caricamento delle notizie.</p>`;
    if (btnLoadMore) btnLoadMore.style.display = "none";
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

