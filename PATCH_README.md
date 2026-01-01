# Patch: immagini + traduzione automatica
Questi file aggiornano i JSON includendo:
- `image`: URL immagine (dal feed; opzionale og:image)
- traduzione automatica in italiano di titolo+descrizione se lingua != IT

## Variabili ambiente (GitHub Actions -> Settings -> Secrets and variables)
- `FETCH_OG_IMAGE=1` per provare a prendere og:image (più lento/fragile)
- `LIBRETRANSLATE_URL` per cambiare endpoint LibreTranslate (default: https://libretranslate.de/translate)
- `LIBRETRANSLATE_API_KEY` se il tuo endpoint richiede chiave (opzionale)
