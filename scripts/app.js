function formatDate(d){
  try{
    const date = new Date(d);
    return date.toLocaleDateString('it-IT', { year:'numeric', month:'long', day:'numeric' });
  }catch(e){ return ''; }
}

// Today label
document.getElementById('today').textContent = formatDate(new Date());

let ALL_ITEMS = [];
let FILTERED = [];
let PAGE = 1;
const PER_PAGE = 10;
let ACTIVE_TOPIC = 'tutte';

fetch('data/articoli.json?_=' + Date.now())
  .then(r => r.json())
  .then(data => {
    ALL_ITEMS = (data.items || []).map((a, idx) => ({
      ...a, _id: idx+1, data: a.data || data.last_updated
    }));
    ALL_ITEMS.sort((a,b) => new Date(b.data) - new Date(a.data));
    FILTERED = [...ALL_ITEMS];
    renderTop();
    renderLatest();
    renderMostRead();
  })
  .catch(err => console.error('Errore nel caricamento dati:', err));

function renderTop(){
  const wrap = document.getElementById('top-stories');
  wrap.innerHTML = '';
  FILTERED.slice(0,4).forEach(a => {
    const el = document.createElement('article');
    el.className = 'item';
    el.innerHTML = `
      <div class="meta">
        <span class="badge">${a.categoria || 'Selezione'}</span>
        <span class="source">${a.fonte || 'Fonte'}</span>
        <span>${formatDate(a.data)}</span>
      </div>
      <h4>${a.titolo}</h4>
      <p>${a.descrizione}</p>
      <a class="link" href="${a.link}" target="_blank" rel="noopener nofollow">Leggi alla fonte</a>
    `;
    wrap.appendChild(el);
  });
}

function renderLatest(){
  const list = document.getElementById('latest-list');
  list.innerHTML = '';
  const start = 4;
  const slice = FILTERED.slice(start, start + PAGE*PER_PAGE);
  slice.forEach(a => {
    const el = document.createElement('article');
    el.className = 'item';
    el.innerHTML = `
      <div class="meta">
        <span class="badge">${a.categoria || 'Selezione'}</span>
        <span class="source">${a.fonte || 'Fonte'}</span>
        <span>${formatDate(a.data)}</span>
      </div>
      <h4>${a.titolo}</h4>
      <p>${a.descrizione}</p>
      <a class="link" href="${a.link}" target="_blank" rel="noopener nofollow">Leggi alla fonte</a>
    `;
    list.appendChild(el);
  });
}

function loadMore(){ PAGE += 1; renderLatest(); }
window.loadMore = loadMore;

function renderMostRead(){
  const list = document.getElementById('most-read');
  list.innerHTML = '';
  FILTERED.slice(0,6).forEach(a => {
    const el = document.createElement('div');
    el.className = 'item';
    el.innerHTML = `
      <h4>${a.titolo}</h4>
      <div class="meta">
        <span class="source">${a.fonte || 'Fonte'}</span>
        <span>${formatDate(a.data)}</span>
      </div>
      <a class="link" href="${a.link}" target="_blank" rel="noopener nofollow">Leggi</a>
    `;
    list.appendChild(el);
  });
}

document.querySelectorAll('.topic').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.topic').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    ACTIVE_TOPIC = btn.dataset.topic;
    applyFilters();
  });
});

function applyFilters(){
  const q = document.getElementById('q').value.trim().toLowerCase();
  FILTERED = ALL_ITEMS.filter(a => {
    const matchesTopic = ACTIVE_TOPIC === 'tutte' || (a.tags || []).includes(ACTIVE_TOPIC) || (a.categoria || '').toLowerCase() === ACTIVE_TOPIC;
    const matchesQuery = !q || (a.titolo + ' ' + a.descrizione + ' ' + (a.fonte||'')).toLowerCase().includes(q);
    return matchesTopic && matchesQuery;
  });
  PAGE = 1;
  renderTop();
  renderLatest();
  renderMostRead();
}
function applySearch(){ applyFilters(); }
function resetSearch(){ document.getElementById('q').value=''; applyFilters(); }
window.applySearch = applySearch;
window.resetSearch = resetSearch;

// ---- IA SECTION (6 sezioni, 1 articolo per ciascun modello) ----
fetch('data/ia.json?_=' + Date.now())
  .then(r => r.json())
  .then(data => {
    document.querySelectorAll('.ia-article').forEach(slot => {
      const model = slot.getAttribute('data-model');
      const item = (data.items || []).find(x => x.modello === model);
      if(!item){ slot.innerHTML = '<p class="muted">Nessun articolo disponibile.</p>'; return; }
      slot.innerHTML = `
        <div class="meta"><span class="source">${item.fonte || 'Fonte'}</span> · <span>${formatDate(item.data)}</span></div>
        <h4>${item.titolo}</h4>
        <p>${item.descrizione}</p>
        <a class="link" href="${item.link}" target="_blank" rel="noopener nofollow">Leggi alla fonte</a>
      `;
    });
  })
  .catch(err => console.error('Errore IA:', err));
