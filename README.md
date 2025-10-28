# Digital Workflow — Rassegna stampa (v4)
Sito statico in italiano, stile **rassegna stampa**. Contenuti aggiornati **in automatico** via GitHub Actions:

- `data/articoli.json` → notizie generali da feed whitelist (filtrate per keyword).
- `data/ia.json` → 1 articolo per ciascun modello IA (ChatGPT, Gemini, Copilot, Claude, MIIA, Altri) da feed e keyword dedicate.

## Struttura
```
/index.html
/assets/css/style.css
/scripts/app.js
/scripts/update.py
/scripts/update_ia.py
/data/feed_sources.json
/data/ia_sources.json
/data/articoli.json
/data/ia.json
/.github/workflows/update.yml
```

## Come aggiornare le fonti/keyword
- **Generale:** modifica `data/feed_sources.json` (feeds, keywords, max_items).
- **IA (6 sezioni):** modifica `data/ia_sources.json` (feeds comuni e keyword per modello).

## Come funziona l’auto-update
1. GitHub Actions (vedi `.github/workflows/update.yml`) gira ogni giorno alle 06:00 UTC.
2. Esegue `scripts/update.py` e `scripts/update_ia.py`.
3. Scrive `data/articoli.json` e `data/ia.json` con i nuovi contenuti.
4. Fa commit automatico → Netlify rileva il commit e **ripubblica** il sito.

## Note legali
Il sito mostra **titoli e sintesi originali** con **link alla fonte**.  
Non ripubblichiamo integralmente testi o immagini.  
I contenuti originali restano dei rispettivi autori/editori.


## Fonti personalizzate (v4.1)
Aggiornate le whitelist dei feed con: Punto Informatico, Wired.it, HDblog, ZeusNews, Il Sole 24 Ore/Tech, Wired.com, Tom’s Hardware, ZDNet, Geek.com.
