#!/usr/bin/env python3
# genera data/ia.json (1 articolo per modello)
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

def main():
    cfg = json.loads((DATA / "ia_sources.json").read_text(encoding="utf-8"))

    rows = []
    for url in cfg.get("feeds", []):
        d = feedparser.parse(url)
        fonte = clean(getattr(d.feed, "title", "") or url, 60) or url
        for e in getattr(d, "entries", [])[:60]:
            link = getattr(e, "link", "") or ""
            title = clean(getattr(e, "title", ""))
            desc = clean(getattr(e, "summary", "") or getattr(e, "description", ""))
            ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = int(time.mktime(ts)) if ts else int(time.time())
            if not (title or desc):
                continue
            rows.append({"ts": ts, "titolo": title, "descrizione": desc, "link": link, "fonte": fonte})

    items = []
    for model, params in cfg.get("models", {}).items():
        kw = [k.lower() for k in params.get("keywords", [])]
        cand = []
        for r in rows:
            txt = (r["titolo"] + " " + r["descrizione"]).lower()
            if (not kw) or any(k in txt for k in kw):
                cand.append(r)
        if not cand:
            continue
        best = sorted(cand, key=lambda x: x["ts"], reverse=True)[0]
        best = dict(best)
        best["data"] = datetime.fromtimestamp(best.pop("ts"), tz=timezone.utc).isoformat()
        best["modello"] = model
        items.append(best)

    payload = {"last_updated": datetime.now(tz=timezone.utc).isoformat(), "items": items}
    (DATA / "ia.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK IA:", len(items))

if __name__ == "__main__":
    main()
