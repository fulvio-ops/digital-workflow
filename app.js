
/* DW app.js - robust loader (supports payload.items or array) */
(() => {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const state = {
    items: [],
    filtered: [],
    category: "tutte",
    q: ""
  };

  function norm(s){ return (s||"").toString().trim(); }
  function lower(s){ return norm(s).toLowerCase(); }

  function deriveCategoria(item){
    const cat = lower(item.categoria || item.category);
    if (cat) return cat;
    // derive from tags
    const tags = (item.tags || item.tag || []);
    if (Array.isArray(tags) && tags.length) return lower(tags[0]);
    const txt = lower((item.titolo||item.title||"") + " " + (item.descrizione||item.description||""));
    const rules = [
      ["notion", ["notion"]],
      ["canva", ["canva"]],
      ["clickup", ["clickup"]],
      ["riunioni", ["meeting","riunione","riunioni","calendar","zoom","teams"]],
      ["ia", ["ai "," ia","chatgpt","openai","gpt","gemini","claude","copilot","llm","sora","anthropic"]],
      ["automazioni", ["automation","automazione","workflow","zapier","make.com","integromat","n8n","ifttt"]],
      ["strumenti", ["tool","strumento","app","software","estensione","plugin"]],
      ["produttività", ["productivity","produttività","organizzazione","focus","todo","task","time blocking","pomodoro","kanban"]],
    ]
    for (const [c, kws] of rules){
      for (const k of kws){
        if (txt.includes(k)) return c;
      }
    }
    return "strumenti";
  }

  function fmtDate(iso){
    try{
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "";
      return d.toLocaleDateString("it-IT", { day:"2-digit", month:"long", year:"numeric" });
    }catch(e){ return ""; }
  }

  function safeUrl(u){
    try{ return u ? new URL(u).toString() : ""; } catch(e){ return ""; }
  }

  function render(){
    const listEl = $("#lista");
    const featEl = $("#featured");
    if (!listEl) return;

    const q = lower(state.q);
    const cat = lower(state.category);

    let items = state.items.map(it => ({...it, _cat: deriveCategoria(it)}));

    if (cat && cat !== "tutte") items = items.filter(it => it._cat === cat);
    if (q) items = items.filter(it => {
      const txt = lower((it.titolo||it.title||"") + " " + (it.descrizione||it.description||"") + " " + (it.fonte||it.source||""));
      return txt.includes(q);
    });

    // Featured: first item overall (not filtered) OR first filtered if filter active
    const feat = (cat !== "tutte" || q) ? items[0] : state.items[0];
    if (featEl){
      if (feat){
        featEl.innerHTML = cardHTML(feat, true);
      } else {
        featEl.innerHTML = `<div class="card empty">Nessun contenuto disponibile.</div>`;
      }
    }

    // Latest list
    if (!items.length){
      listEl.innerHTML = `<div class="card empty">Nessuna notizia trovata.</div>`;
      return;
    }
    listEl.innerHTML = items.slice(0, 30).map(it => cardHTML(it, false)).join("");
  }

  function cardHTML(it, featured){
    const title = norm(it.titolo || it.title);
    const desc  = norm(it.descrizione || it.description);
    const fonte = norm(it.fonte || it.source || "Digital Workflow");
    const date  = fmtDate(it.data || it.date || it.published || "");
    const link  = safeUrl(it.link || it.url || "");
    const cat   = deriveCategoria(it);
    const img   = safeUrl(it.image || it.img || it.thumbnail || "");

    const badge = `<span class="badge">${escapeHTML(capitalize(cat))}</span>`;
    const meta  = `<div class="meta">${escapeHTML(fonte)}${date ? " · " + escapeHTML(date) : ""}</div>`;
    const aOpen = link ? `<a class="title" href="${link}" target="_blank" rel="noopener noreferrer">${escapeHTML(title || "Senza titolo")}</a>` :
                         `<div class="title">${escapeHTML(title || "Senza titolo")}</div>`;
    const descHtml = desc ? `<div class="desc">${escapeHTML(desc)}</div>` : "";
    const imgHtml = img
      ? `<img class="thumb" src="${img}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'; this.parentElement.classList.add('noimg');">`
      : `<div class="thumb-fallback" aria-hidden="true"></div>`;

    return `
      <article class="card ${featured ? "featured" : ""} ${img ? "" : "noimg"}">
        ${imgHtml}
        <div class="content">
          <div class="topline">${badge}${meta}</div>
          ${aOpen}
          ${descHtml}
          ${link ? `<div class="link"><a href="${link}" target="_blank" rel="noopener noreferrer">Leggi alla fonte</a></div>` : ""}
        </div>
      </article>
    `;
  }

  function escapeHTML(s){
    return (s||"").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function capitalize(s){ s = norm(s); return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

  async function load(){
    const url = "data/articoli.json?nocache=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    const items = Array.isArray(data) ? data : (data.items || data.Items || []);
    state.items = items;
    wire();
    render();
  }

  function wire(){
    // search
    const q = $("#q");
    const btnCerca = $("#btnCerca");
    const btnReset = $("#btnReset");
    if (q){
      q.addEventListener("input", () => { state.q = q.value; render(); });
    }
    btnCerca?.addEventListener("click", () => { state.q = q?.value || ""; render(); });
    btnReset?.addEventListener("click", () => {
      state.q = "";
      if (q) q.value = "";
      state.category = "tutte";
      $$(".chip").forEach(c => c.classList.toggle("active", c.dataset.cat === "tutte"));
      render();
    });

    // category chips
    $$(".chip").forEach(chip => {
      chip.addEventListener("click", () => {
        state.category = chip.dataset.cat || "tutte";
        $$(".chip").forEach(c => c.classList.toggle("active", c === chip));
        render();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    load().catch(err => {
      console.error(err);
      const listEl = document.querySelector("#lista");
      if (listEl) listEl.innerHTML = `<div class="card empty">Errore nel caricamento delle notizie. Riprova tra poco.</div>`;
    });
  });
})();
