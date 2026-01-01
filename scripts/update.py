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

TOPIC_RULES = [
  ("notion",      [r"\bnotion\b"]),
  ("canva",       [r"\bcanva\b"]),
  ("clickup",     [r"\bclickup\b"]),
  ("automazioni", [r"\bzapier\b", r"\bmake\.com\b", r"\bintegromat\b", r"\bn8n\b", r"\bautomation\b", r"\bautomazione\b", r"\bworkflow\b", r"\bintegrazion"]),
  ("riunioni",    [r"\bmeeting\b", r"\briunion", r"\bzoom\b", r"\bteams\b", r"\bgoogle meet\b", r"\bcalendar\b", r"\bagenda\b"]),
  ("ia",          [r"\bai\b", r"\bia\b", r"\bllm\b", r"\bchatgpt\b", r"\bopenai\b", r"\bgpt\b", r"\bgemini\b", r"\bclaude\b", r"\bdeepseek\b", r"\bmistral\b"]),
  ("strumenti",   [r"\btool\b", r"\bapp\b", r"\bsoftware\b", r"\bplugin\b", r"\bestension\b", r"\bchrome\b", r"\bwidget\b"]),
  ("produttività",[r"\bproductivity\b", r"\bproduttivit", r"\bfocus\b", r"\btime management\b", r"\bgestione del tempo\b", r"\borganizzazion"])
]

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

def load_cfg():
    return json.loads((DATA / "feed_sources.json").read_text(encoding="utf-8"))

def guess_image(entry):
    # 1) media:content / media_thumbnail
    for key in ("media_content", "media_thumbnail"):
        v = getattr(entry, key, None)
        if isinstance(v, list) and v:
            url = v[0].get("url") or v[0].get("href")
            if url and url.startswith("http"):
                return url
    # 2) enclosures
    enclosures = getattr(entry, "enclosures", None)
    if isinstance(enclosures, list):
        for e in enclosures:
            url = e.get("href") or e.get("url")
            typ = (e.get("type") or "").lower()
            if url and url.startswith("http") and ("image" in typ or re.search(r"\.(png|jpg|jpeg|webp|gif)(\?|$)", url, re.I)):
                return url
    # 3) links rel=enclosure
    links = getattr(entry, "links", None)
    if isinstance(links, list):
        for l in links:
            if (l.get("rel") == "enclosure") and l.get("href") and l["href"].startswith("http"):
                typ = (l.get("type") or "").lower()
                if ("image" in typ) or re.search(r"\.(png|jpg|jpeg|webp|gif)(\?|$)", l["href"], re.I):
                    return l["href"]
    # 4) try find <img src=...> in summary
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
    # Optional: LibreTranslate public endpoint. If unavailable, keep original.
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

def classify(title, desc):
    txt = (title + " " + desc).lower()
    for topic, patterns in TOPIC_RULES:
        for p in patterns:
            if re.search(p, txt, re.I):
                return topic
    return "strumenti"

def parse_feeds(cfg):
    rows = []
    for url in cfg.get("feeds", []):
        d = feedparser.parse(url)
        fonte = clean(getattr(d.feed, "title", "") or url, 80) or url
        for e in getattr(d, "entries", [])[:60]:
            link = getattr(e, "link", "") or ""
            title = clean(getattr(e, "title", ""))
            desc = clean(getattr(e, "summary", "") or getattr(e, "description", ""))
            ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = int(time.mktime(ts)) if ts else int(time.time())
            if not (title or desc):
                continue
            image = guess_image(e)
            title, desc = translate_if_needed(title, desc)
            categoria = classify(title, desc)
            rows.append({"ts": ts, "titolo": title, "descrizione": desc, "link": link, "fonte": fonte, "image": image, "categoria": categoria})
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
