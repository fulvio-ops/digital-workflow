# Digital Workflow — IONOS v5
- Grafica v5 (hero + card), auto-update via GitHub Actions, deploy FTP su IONOS.

## Setup rapido
1) Carica tutto nel repo GitHub.
2) In Settings → Secrets → Actions crea:
   - FTP_SERVER = accesso.ionos.it (o quello del tuo piano)
   - FTP_USER = utente FTP
   - FTP_PASS = password FTP
3) Se la root web non è `/htdocs/`, cambia `server-dir` nel workflow.
4) Actions → Run workflow per pubblicare.
