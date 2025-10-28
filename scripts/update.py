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
SOURCES = DATA_DIR / "feed_sources.json"
OUT = DATA_DIR / "articoli.json"

def clean_text(s, max_len=220):
    txt = s or ""
    if HAVE_BS:
        try:
            txt = BeautifulSoup(txt, "html.parser").get_text(" ", strip=True)
        except Exception:
            pass
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > max_len:
        txt = txt[:max_len].rsplit(" ", 1)[0] + "…"
    return txt

def fetch(feeds):
    items = []
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
            items.append({"ts": int(ts), "titolo": title or "Senza titolo", "descrizione": summary or "Scopri di più alla fonte.", "link": link, "fonte": fonte})
    return items

def main():
    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    feeds = cfg.get("feeds", [])
    keywords = [k.lower() for k in cfg.get("keywords", [])]
    max_items = int(cfg.get("max_items", 24))

    raw = fetch(feeds)

    def ok(i):
        text = (i["titolo"] + " " + i["descrizione"]).lower()
        return any(k in text for k in keywords) if keywords else True

    items = [i for i in raw if ok(i)]

    dedup = {}
    for it in items:
        key = it["link"] or it["titolo"]
        if key not in dedup or it["ts"] > dedup[key]["ts"]:
            dedup[key] = it

    final = sorted(dedup.values(), key=lambda x: x["ts"], reverse=True)[:max_items]
    for it in final:
        it["data"] = datetime.fromtimestamp(it.pop("ts"), tz=timezone.utc).isoformat()

    payload = {"last_updated": datetime.now(timezone.utc).isoformat(), "items": final}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Aggiornati {len(final)} articoli → {OUT}")

if __name__ == "__main__":
    main()
