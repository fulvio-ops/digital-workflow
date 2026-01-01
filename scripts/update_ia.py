#!/usr/bin/env python3
import json, time, pathlib, os, re
from datetime import datetime, timezone
import feedparser
from bs4 import BeautifulSoup

try:
    import requests
except Exception:
    requests = None

try:
    from langdetect import detect
except Exception:
    detect = None

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE.parent / "data"

UA = os.environ.get("DW_USER_AGENT", "DigitalWorkflowBot/1.0 (+https://fugallo.it/)")

def clean(s: str, m: int = 240) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    try:
        t = BeautifulSoup(t, "html.parser").get_text(" ", strip=True)
    except Exception:
        pass
    t = " ".join(t.split())
    return t[:m].rstrip()

def guess_image(entry):
    for key in ("media_content", "media_thumbnail"):
        v = getattr(entry, key, None)
        if isinstance(v, list) and v:
            url = v[0].get("url") or v[0].get("href")
            if url and url.startswith("http"):
                return url
    enclosures = getattr(entry, "enclosures", None)
    if isinstance(enclosures, list):
        for e in enclosures:
            url = e.get("href") or e.get("url")
            typ = (e.get("type") or "").lower()
            if url and url.startswith("http") and ("image" in typ or re.search(r"\.(png|jpg|jpeg|webp|gif)(\?|$)", url, re.I)):
                return url
    links = getattr(entry, "links", None)
    if isinstance(links, list):
        for l in links:
            if (l.get("rel") == "enclosure") and l.get("href") and l["href"].startswith("http"):
                typ = (l.get("type") or "").lower()
                if ("image" in typ) or re.search(r"\.(png|jpg|jpeg|webp|gif)(\?|$)", l["href"], re.I):
                    return l["href"]
    html = getattr(entry, "summary", "") or getattr(entry, "description", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if m:
        url = m.group(1)
        if url.startswith("//"):
            url = "https:" + url
        if url.startswith("http"):
            return url
    return ""

def translate_if_needed(title, desc):
    if not requests or not detect:
        return title, desc
    txt = (title + " " + desc).strip()
    if not txt:
        return title, desc
    try:
        lang = detect(txt)
    except Exception:
        return title, desc
    if lang in ("it", "it_IT"):
        return title, desc
    url = os.environ.get("LIBRETRANSLATE_URL", "https://libretranslate.de/translate")
    key = os.environ.get("LIBRETRANSLATE_API_KEY", "")
    def do_tr(s):
        if not s:
            return s
        payload = {"q": s, "source": "auto", "target": "it", "format": "text"}
        if key:
            payload["api_key"] = key
        r = requests.post(url, data=payload, headers={"User-Agent": UA}, timeout=15)
        if r.ok:
            return (r.json().get("translatedText") or s).strip()
        return s
    try:
        return do_tr(title), do_tr(desc)
    except Exception:
        return title, desc

def main():
    cfg = json.loads((DATA / "ia_sources.json").read_text(encoding="utf-8"))

    rows = []
    for url in cfg.get("feeds", []):
        d = feedparser.parse(url)
        fonte = clean(getattr(d.feed, "title", "") or url, 80) or url
        for e in getattr(d, "entries", [])[:80]:
            link = getattr(e, "link", "") or ""
            title = clean(getattr(e, "title", ""))
            desc = clean(getattr(e, "summary", "") or getattr(e, "description", ""))
            ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = int(time.mktime(ts)) if ts else int(time.time())
            if not (title or desc):
                continue
            image = guess_image(e)
            title, desc = translate_if_needed(title, desc)
            rows.append({"ts": ts, "titolo": title, "descrizione": desc, "link": link, "fonte": fonte, "image": image, "categoria": "ia"})
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
