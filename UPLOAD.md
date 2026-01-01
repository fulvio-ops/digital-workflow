# Upload su GitHub (importante per .github)
Per far funzionare l’aggiornamento automatico dei feed, GitHub deve vedere il file:
`.github/workflows/update.yml`

⚠️ Su macOS i file/cartelle che iniziano con punto (.) possono essere nascosti e rischi di NON caricarli se fai upload “a selezione”.

Metodo consigliato:
1) Scarica questo ZIP
2) Estrai tutto in una cartella
3) Carica su GitHub **trascinando l’intera cartella** (drag&drop) nella pagina “Upload files”
   - assicurati che venga caricato anche `.github/workflows/update.yml`
4) In repo: Settings → Actions → General → Workflow permissions → **Read and write permissions**
5) Actions → “Aggiorna articoli DW” → Run workflow

Check rapido:
- in `data/articoli.json` deve cambiare `last_updated`
