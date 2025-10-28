# Digital Workflow (statico)
Sito statico in italiano che **seleziona e linka** articoli su produttività, strumenti digitali e automazioni.

- **Nessuna ripubblicazione integrale**: mostriamo solo titoli e sintesi originali.
- **Attribuzione**: ogni card riporta la *fonte* con link diretto.
- **Aggiornamento automatico**: uno script legge una whitelist di feed italiani e aggiorna `data/articoli.json`.

## Struttura
```
/index.html
/assets/css/style.css
/scripts/app.js
/scripts/update.py
/data/feed_sources.json
/data/articoli.json
/.github/workflows/update.yml
```

## Modifiche senza programmare
- Aggiungi/togli articoli modificando `data/articoli.json`.
- Cambia titoli/testi fissi in `index.html`.
- Colori e font in `assets/css/style.css`.

## Aggiornamento automatico
- In locale: `pip install feedparser beautifulsoup4` poi `python scripts/update.py`.
- Con GitHub Actions: il workflow gira ogni giorno alle 06:00 UTC e fa commit su `data/articoli.json`.

## Fonti (italiane) in whitelist
Modifica `data/feed_sources.json` per personalizzare:
- parole chiave
- feed
- numero massimo articoli

## Note legali
Questo progetto **non ripubblica** contenuti altrui: fornisce titoli, sintesi originali e il link alla fonte. Testi, immagini e marchi rimangono dei rispettivi autori/editori.
