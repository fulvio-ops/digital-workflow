// Digital Workflow - client
function formatDate(d){
  try{
    return new Date(d).toLocaleDateString('it-IT',{year:'numeric',month:'long',day:'numeric'});
  }catch(e){ return ''; }
}

let ALL_ITEMS = [];
let FILTERED = [];
let PAGE = 1;
const PER_PAGE = 10;
let ACTIVE_TOPIC = 'tutte';
let ACTIVE_Q = '';

function norm(s){ return (s||'').toString().toLowerCase(); }

function applyFilters(){
  const q = norm(ACTIVE_Q);
  FILTERED = ALL_ITEMS.filter(a=>{
    const topicOk = (ACTIVE_TOPIC==='tutte') || norm(a.categoria)===norm(ACTIVE_TOPIC);
    const qOk = !q || (norm(a.titolo).includes(q) || norm(a.descrizione).includes(q) || norm(a.fonte).includes(q));
    return topicOk && qOk;
  });
  PAGE = 1;
  renderTop();
  renderLatest(true);
  renderMostRead();
}

function imgTag(url){
  if(!url) return '';
  return `<img class="thumb" src="${url}" alt="" loading="lazy" referrerpolicy="no-referrer">`;
}

function card(a){
  const badge = a.categoria ? a.categoria : 'Selezione';
  return `
  <article class="card">
    ${imgTag(a.image)}
    <div class="card-body">
      <div class="meta">
        <span class="badge">${badge}</span>
        <span class="dot">•</span>
        <span class="fonte">${a.fonte||''}</span>
        <span class="dot">•</span>
        <time datetime="${a.data||''}">${formatDate(a.data)}</time>
      </div>
      <h3 class="title">${a.titolo||''}</h3>
      <p class="desc">${a.descrizione||''}</p>
      <a class="link" href="${a.link}" target="_blank" rel="noopener noreferrer">Leggi alla fonte</a>
    </div>
  </article>`;
}

function renderTop(){
  const w = document.getElementById('top-stories');
  if(!w) return;
  const items = FILTERED.slice(0,1);
  w.innerHTML = items.map(card).join('') || '<div class="empty">Nessuna notizia per questo filtro.</div>';
}

function renderLatest(reset){
  const w = document.getElementById('latest-list');
  if(!w) return;
  const start = 1; // after top
  const slice = FILTERED.slice(start, start + PAGE*PER_PAGE);
  if(reset) w.innerHTML = '';
  w.innerHTML = slice.map(card).join('');
  const btn = document.getElementById('load-more');
  if(btn){
    btn.style.display = (start + PAGE*PER_PAGE < FILTERED.length) ? 'inline-flex' : 'none';
  }
}

function renderMostRead(){
  const w = document.getElementById('most-read');
  if(!w) return;
  const items = FILTERED.slice(1,4);
  w.innerHTML = items.map(a=>`
    <a class="mini" href="${a.link}" target="_blank" rel="noopener noreferrer">
      <div class="mini-title">${a.titolo||''}</div>
      <div class="mini-meta">${a.fonte||''} • ${formatDate(a.data)}</div>
    </a>
  `).join('') || '<div class="empty">—</div>';
}

function renderIA(){
  fetch('data/ia.json?_='+Date.now()).then(r=>r.json()).then(data=>{
    const items = data.items || [];
    const byModel = {};
    for(const it of items){ byModel[it.modello]=it; }
    const map = {
      'chatgpt':'ia-chatgpt',
      'copilot':'ia-copilot',
      'gemini':'ia-gemini',
      'claude':'ia-claude',
      'altri':'ia-altri',
      'miia':'ia-miia'
    };
    Object.entries(map).forEach(([model,id])=>{
      const el = document.getElementById(id);
      if(!el) return;
      const it = byModel[model];
      if(!it){ el.innerHTML = '<div class="empty">—</div>'; return; }
      el.innerHTML = `
        ${imgTag(it.image)}
        <div class="mini-title">${it.titolo||''}</div>
        <a class="link" href="${it.link}" target="_blank" rel="noopener noreferrer">Leggi alla fonte</a>
      `;
    });
  }).catch(()=>{});
}

function wireUI(){
  const q = document.getElementById('q');
  const btnSearch = document.getElementById('btn-search');
  const btnClear = document.getElementById('btn-clear');

  if(q){
    q.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ ACTIVE_Q=q.value; applyFilters(); }});
  }
  if(btnSearch){
    btnSearch.addEventListener('click', ()=>{ ACTIVE_Q = q ? q.value : ''; applyFilters(); });
  }
  if(btnClear){
    btnClear.addEventListener('click', ()=>{
      ACTIVE_Q = '';
      ACTIVE_TOPIC = 'tutte';
      if(q) q.value = '';
      document.querySelectorAll('nav.topics button').forEach(b=>b.classList.remove('active'));
      const first = document.querySelector('nav.topics button[data-topic="tutte"]');
      if(first) first.classList.add('active');
      applyFilters();
    });
  }
  document.querySelectorAll('nav.topics button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('nav.topics button').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      ACTIVE_TOPIC = btn.getAttribute('data-topic') || 'tutte';
      applyFilters();
    });
  });

  const load = document.getElementById('load-more');
  if(load){
    load.addEventListener('click', ()=>{
      PAGE += 1;
      renderLatest(false);
    });
  }
}

fetch('data/articoli.json?_='+Date.now()).then(r=>r.json()).then(data=>{
  ALL_ITEMS = (data.items || []).map((a,idx)=>({
    ...a,
    _id: idx+1,
    data: a.data || data.last_updated
  }));
  // sort newest
  ALL_ITEMS.sort((a,b)=>new Date(b.data)-new Date(a.data));
  FILTERED = [...ALL_ITEMS];
  wireUI();
  renderIA();
  applyFilters();
}).catch(()=>{});
