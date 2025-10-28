# Digital Workflow — v5 (editoriale soft)
- Hero con immagine (assets/img/hero.svg)
- Card morbide, tipografia Inter + Lora
- Sezione IA (6 modelli) e rassegna “In evidenza / Ultime”
- Auto-update via GitHub Actions (scripts/update.py, scripts/update_ia.py, .github/workflows/update.yml)

## DNS (IONOS → Netlify)
A ( @ ) → 75.2.60.5
CNAME ( www ) → il-tuo-sito.netlify.app

## Config
- data/feed_sources.json → whitelist feed + keyword (max_items=24)
- data/ia_sources.json → feed + keyword per modello
