#!/usr/bin/env python3
# genera data/articoli.json dai feed
import json, time, pathlib
from datetime import datetime, timezone

import feedparser
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE.parent / "data"

def clean(s: str, m: int = 220) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    try:
        t = BeautifulSoup(t, "html.parser").get_text(" ", strip=True)
    except Exception:
        pass
    t = " ".join(t.split())
    return t[:m].rstrip()

def load_cfg():
    return json.loads((DATA / "feed_sources.json").read_text(encoding="utf-8"))

def parse_feeds(cfg):
    rows = []
    for url in cfg.get("feeds", []):
        d = feedparser.parse(url)
        fonte = clean(getattr(d.feed, "title", "") or url, 60) or url
        for e in getattr(d, "entries", [])[:40]:
            link = getattr(e, "link", "") or ""
            title = clean(getattr(e, "title", ""))
            desc = clean(getattr(e, "summary", "") or getattr(e, "description", ""))
            ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = int(time.mktime(ts)) if ts else int(time.time())
            if not (title or desc):
                continue
            rows.append({"ts": ts, "titolo": title, "descrizione": desc, "link": link, "fonte": fonte})
    return rows

def keyword_filter(rows, keywords):
    kw = [k.lower() for k in (keywords or [])]
    if not kw:
        return rows
    out = []
    for i in rows:
        txt = (i["titolo"] + " " + i["descrizione"]).lower()
        if any(k in txt for k in kw):
            out.append(i)
    return out

def dedup_and_sort(rows, max_items):
    dedup = {}
    for it in rows:
        key = it["link"] or it["titolo"]
        if key not in dedup or it["ts"] > dedup[key]["ts"]:
            dedup[key] = it
    out = sorted(dedup.values(), key=lambda x: x["ts"], reverse=True)[: int(max_items)]
    for it in out:
        it["data"] = datetime.fromtimestamp(it.pop("ts"), tz=timezone.utc).isoformat()
    return out

def main():
    cfg = load_cfg()
    rows = parse_feeds(cfg)
    rows = keyword_filter(rows, cfg.get("keywords", []))
    items = dedup_and_sort(rows, cfg.get("max_items", 24))
    payload = {"last_updated": datetime.now(tz=timezone.utc).isoformat(), "items": items}
    (DATA / "articoli.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK articoli:", len(items))

if __name__ == "__main__":
    main()
