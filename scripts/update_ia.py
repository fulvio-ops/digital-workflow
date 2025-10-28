#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, time, re, pathlib, sys
from datetime import datetime, timezone
try:
    import feedparser
except ImportError:
    print("Manca feedparser. Installa con: pip install feedparser", file=sys.stderr); sys.exit(1)
try:
    from bs4 import BeautifulSoup
    HAVE_BS = True
except Exception:
    HAVE_BS = False

BASE = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE.parent / "data"
SOURCES = DATA_DIR / "ia_sources.json"
OUT = DATA_DIR / "ia.json"

def clean_text(s, max_len=220):
    txt = s or ""
    if HAVE_BS:
        try:
            txt = BeautifulSoup(txt, "html.parser").get_text(" ", strip=True)
        except Exception:
            pass
    txt = re.sub(r"\\s+", " ", txt).strip()
    if len(txt) > max_len:
        txt = txt[:max_len].rsplit(" ", 1)[0] + "…"
    return txt

def fetch(feeds):
    rows = []
    for url in feeds:
        d = feedparser.parse(url)
        fonte = d.feed.get("title", "Fonte")
        for e in d.entries:
            link = (getattr(e, "link", "") or "").strip()
            title = clean_text(getattr(e, "title", ""))
            summary = clean_text(getattr(e, "summary", "") or getattr(e, "description", ""))
            ts_struct = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = time.mktime(ts_struct) if ts_struct else time.time()
            if not (title or summary): continue
            rows.append({"ts": int(ts), "titolo": title or "Senza titolo", "descrizione": summary or "Scopri di più alla fonte.", "link": link, "fonte": fonte})
    return rows

def main():
    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    feeds = cfg.get("feeds", [])
    per_model = cfg.get("models", {})
    rows = fetch(feeds)

    result = []
    for model, params in per_model.items():
        kw = [k.lower() for k in params.get("keywords", [])]
        candidates = []
        for r in rows:
            text = (r["titolo"] + " " + r["descrizione"]).lower()
            if not kw or any(k in text for k in kw):
                candidates.append(r)
        if candidates:
            best = sorted(candidates, key=lambda x: x["ts"], reverse=True)[0]
            best_copy = best.copy()
            best_copy["data"] = datetime.fromtimestamp(best_copy.pop("ts"), tz=timezone.utc).isoformat()
            best_copy["modello"] = model
            result.append(best_copy)

    payload = {"last_updated": datetime.now(timezone.utc).isoformat(), "items": result}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Aggiornati {len(result)} modelli IA → {OUT}")

if __name__ == "__main__":
    main()
