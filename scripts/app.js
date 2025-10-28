// Popola la griglia con gli articoli dal JSON
fetch('data/articoli.json?_=' + Date.now())
  .then(r => r.json())
  .then(data => {
    const container = document.getElementById('articoli-container');
    container.innerHTML = '';
    (data.items || []).forEach(a => {
      const card = document.createElement('article');
      card.className = 'card';
      card.innerHTML = `
        <span class="badge">Fonte: ${a.fonte || '—'}</span>
        <h3>${a.titolo}</h3>
        <p>${a.descrizione}</p>
        <a class="btn btn-primary" href="${a.link}" target="_blank" rel="noopener nofollow">Leggi alla fonte</a>
      `;
      container.appendChild(card);
    });
    const updatedEl = document.getElementById('last-updated');
    if (updatedEl && data.last_updated){
      updatedEl.textContent = new Date(data.last_updated).toLocaleString('it-IT');
    }
  })
  .catch(err => console.error('Errore nel caricamento degli articoli:', err));
