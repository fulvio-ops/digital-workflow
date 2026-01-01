# DW Hotfix v1
Questo pacchetto risolve:
- Notizie non caricate per mismatch app.js (root vs scripts) e formato JSON (array vs {items})
- Filtri categorie vuoti: derivazione categoria robusta anche se manca nel JSON
- Logo/hero troppo grande: CSS che forza dimensioni e object-fit

## Come applicare
Carica e sovrascrivi:
- app.js (root)
- scripts/app.js
- assets/css/hotfix.css (poi aggiungi link in index.html)
- assets/img/hero.svg

In index.html aggiungi:
<link rel="stylesheet" href="assets/css/hotfix.css">
e assicurati che lo script punti a app.js (root) o scripts/app.js coerentemente.
