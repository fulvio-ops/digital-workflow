const NEWS_CONTAINER = document.getElementById("news");
const FILTERS = document.querySelectorAll(".filters button");

let ALL_ITEMS = [];
let CURRENT_FILTER = "tutte";

async function loadArticoli() {
  const res = await fetch("data/articoli.json?nocache=" + Date.now());
  const data = await res.json();

  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  return [];
}

function getCategoria(item) {
  return (item.categoria || "tutte").toLowerCase();
}

function render(items) {
  if (!NEWS_CONTAINER) return;

  NEWS_CONTAINER.innerHTML = "";

  if (!items.length) {
    NEWS_CONTAINER.innerHTML = "<p>Nessuna notizia disponibile.</p>";
    return;
  }

  items.forEach(item => {
    const card = document.createElement("article");
    card.className = "card";

    const img = item.image
      ? `<img src="${item.image}" loading="lazy" alt="">`
      : "";

    card.innerHTML = `
      ${img}
      <h3>${item.titolo}</h3>
      <p>${item.descrizione}</p>
      <a href="${item.link}" target="_blank" rel="noopener">Leggi alla fonte</a>
    `;

    NEWS_CONTAINER.appendChild(card);
  });
}

function applyFilter() {
  const filtered = CURRENT_FILTER === "tutte"
    ? ALL_ITEMS
    : ALL_ITEMS.filter(item => getCategoria(item) === CURRENT_FILTER);

  render(filtered);
}

FILTERS.forEach(btn => {
  btn.addEventListener("click", () => {
    FILTERS.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    CURRENT_FILTER = btn.dataset.cat;
    applyFilter();
  });
});

(async function init() {
  try {
    ALL_ITEMS = await loadArticoli();
    applyFilter();
  } catch (e) {
    console.error("Errore caricamento news", e);
    if (NEWS_CONTAINER) {
      NEWS_CONTAINER.innerHTML = "<p>Errore nel caricamento delle notizie.</p>";
    }
  }
})();
