#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggiorna data/articoli.json raccogliendo articoli in italiano da feed RSS whitelist.
- Filtra per keyword italiane (titolo+descrizione)
- Deduplica per link
- Troncatura descrizione (sintesi breve)
- Scrive last_updated in UTC ISO
Da usare in locale o con GitHub Actions.
"""
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
data_dir = BASE / "data"
sources_path = data_dir / "feed_sources.json"
out_path = data_dir / "articoli.json"

def clean_text(html_or_text: str, max_len=220) -> str:
    txt = html_or_text or ""
    if HAVE_BS:
        try:
            soup = BeautifulSoup(txt, "html.parser")
            txt = soup.get_text(" ", strip=True)
        except Exception:
            pass
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > max_len:
        cut = txt[:max_len].rsplit(" ", 1)[0] + "…"
        return cut
    return txt

def normalize(s: str) -> str:
    return (s or "").strip()

def fetch_feeds(feeds: list) -> list:
    items = []
    for url in feeds:
        d = feedparser.parse(url)
        feed_title = d.feed.get("title", "Fonte")
        for e in d.entries:
            link = normalize(getattr(e, "link", ""))
            title = clean_text(getattr(e, "title", ""))
            summary = clean_text(getattr(e, "summary", "") or getattr(e, "description", ""))
            published_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = time.mktime(published_parsed) if published_parsed else time.time()
            items.append({
                "ts": int(ts),
                "titolo": title or "Senza titolo",
                "descrizione": summary or "Scopri di più alla fonte.",
                "link": link,
                "fonte": feed_title
            })
    return items

def main():
    cfg = json.loads(sources_path.read_text(encoding="utf-8"))
    feeds = cfg.get("feeds", [])
    keywords = [k.lower() for k in cfg.get("keywords", [])]
    max_items = int(cfg.get("max_items", 12))

    raw_items = fetch_feeds(feeds)

    def match_keywords(item):
        text = (item["titolo"] + " " + item["descrizione"]).lower()
        return any(k in text for k in keywords) if keywords else True

    items = [i for i in raw_items if match_keywords(i)]

    # Deduplica per link (mantieni il più recente)
    dedup = {}
    for it in items:
        key = it["link"] or it["titolo"]
        if key not in dedup or it["ts"] > dedup[key]["ts"]:
            dedup[key] = it

    # Ordina per data desc e limita
    final_items = sorted(dedup.values(), key=lambda x: x["ts"], reverse=True)[:max_items]
    for it in final_items:
        it.pop("ts", None)

    payload = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "items": final_items
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Aggiornati {len(final_items)} articoli in {out_path}")

if __name__ == "__main__":
    main()
