#!/usr/bin/env python3
"""
DW IA updater
- Seleziona 1 articolo "migliore" per ciascun modello/categoria definita in data/ia_sources.json
- Estrae immagine (feed; opzionalmente og:image)
- Traduce automaticamente in italiano se necessario (via LibreTranslate, configurabile)
"""
from __future__ import annotations

import json
import os
import time
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE.parent / "data"

DEFAULT_LT_URL = "https://libretranslate.de/translate"
LT_URL = os.environ.get("LIBRETRANSLATE_URL", DEFAULT_LT_URL).strip()
LT_API_KEY = os.environ.get("LIBRETRANSLATE_API_KEY", "").strip()
FETCH_OG = os.environ.get("FETCH_OG_IMAGE", "0").strip() == "1"

UA = os.environ.get("DW_UA", "DigitalWorkflowBot/1.0 (+https://fugallo.it/)").strip()
HTTP_TIMEOUT = float(os.environ.get("DW_HTTP_TIMEOUT", "12"))


def clean_text(s: str, max_len: int = 220) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    try:
        t = BeautifulSoup(t, "html.parser").get_text(" ", strip=True)
    except Exception:
        pass
    t = " ".join(t.split())
    if len(t) > max_len:
        t = t[:max_len].rstrip()
    return t


def pick_best_image_from_entry(entry: Any) -> str:
    mc = entry.get("media_content") or entry.get("media:content")
    if isinstance(mc, list) and mc:
        for m in mc:
            url = (m.get("url") or "").strip()
            typ = (m.get("type") or "").lower()
            if url and (typ.startswith("image/") or url.lower().endswith((".jpg",".jpeg",".png",".webp",".gif"))):
                return url

    mt = entry.get("media_thumbnail") or entry.get("media:thumbnail")
    if isinstance(mt, list) and mt:
        for m in mt:
            url = (m.get("url") or "").strip()
            if url:
                return url

    for l in entry.get("links", []) or []:
        href = (l.get("href") or "").strip()
        ltype = (l.get("type") or "").lower()
        rel = (l.get("rel") or "").lower()
        if href and (ltype.startswith("image/") or rel == "enclosure" and href.lower().endswith((".jpg",".jpeg",".png",".webp",".gif"))):
            return href

    summary = entry.get("summary") or entry.get("description") or ""
    if summary and "<img" in summary.lower():
        try:
            soup = BeautifulSoup(summary, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return str(img.get("src")).strip()
        except Exception:
            pass

    return ""


def fetch_og_image(url: str) -> str:
    if not url:
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", attrs={"property": "og:image"}) or soup.find("meta", attrs={"name": "og:image"})
        if og and og.get("content"):
            return str(og.get("content")).strip()
    except Exception:
        return ""
    return ""


_translation_cache: Dict[Tuple[str, str], str] = {}


def detect_lang(text: str) -> str:
    txt = (text or "").strip()
    if not txt:
        return "it"
    try:
        return detect(txt)
    except LangDetectException:
        return "it"


def translate_to_it(text: str) -> str:
    txt = (text or "").strip()
    if not txt:
        return ""
    key = ("it", txt)
    if key in _translation_cache:
        return _translation_cache[key]

    payload = {"q": txt, "source": "auto", "target": "it", "format": "text"}
    if LT_API_KEY:
        payload["api_key"] = LT_API_KEY

    try:
        r = requests.post(LT_URL, data=payload, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            _translation_cache[key] = txt
            return txt
        data = r.json()
        out = (data.get("translatedText") or "").strip()
        if not out:
            out = txt
        _translation_cache[key] = out
        return out
    except Exception:
        _translation_cache[key] = txt
        return txt


def maybe_translate(title: str, desc: str) -> Tuple[str, str]:
    sample = (title + " " + desc).strip()
    lang = detect_lang(sample)
    if lang and lang.lower().startswith("it"):
        return title, desc
    t_it = translate_to_it(title) if title else ""
    d_it = translate_to_it(desc) if desc else ""
    return t_it or title, d_it or desc


def main() -> None:
    cfg = json.loads((DATA / "ia_sources.json").read_text(encoding="utf-8"))

    rows: List[Dict[str, Any]] = []
    for url in cfg.get("feeds", []):
        d = feedparser.parse(url)
        fonte = clean_text(getattr(d.feed, "title", "") or url, 60) or url
        for e in getattr(d, "entries", [])[:80]:
            link = (getattr(e, "link", "") or "").strip()
            title = clean_text(getattr(e, "title", "") or "")
            desc = clean_text(getattr(e, "summary", "") or getattr(e, "description", "") or "")
            ts_struct = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            ts = int(time.mktime(ts_struct)) if ts_struct else int(time.time())
            if not (title or desc):
                continue

            image = pick_best_image_from_entry(e)
            if (not image) and FETCH_OG:
                image = fetch_og_image(link)

            rows.append({"ts": ts, "titolo": title, "descrizione": desc, "link": link, "fonte": fonte, "image": image})

    items: List[Dict[str, Any]] = []
    for model, params in cfg.get("models", {}).items():
        kw = [k.lower() for k in params.get("keywords", [])]
        cand: List[Dict[str, Any]] = []
        for r in rows:
            txt = ((r.get("titolo") or "") + " " + (r.get("descrizione") or "")).lower()
            if (not kw) or any(k in txt for k in kw):
                cand.append(r)
        if not cand:
            continue

        best = sorted(cand, key=lambda x: int(x.get("ts", 0)), reverse=True)[0]
        best = dict(best)
        ts = int(best.pop("ts"))
        best["data"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        best["modello"] = model

        best["titolo"], best["descrizione"] = maybe_translate(best.get("titolo",""), best.get("descrizione",""))
        items.append(best)

    payload = {"last_updated": datetime.now(tz=timezone.utc).isoformat(), "items": items}
    (DATA / "ia.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK IA:", len(items), "FETCH_OG:", FETCH_OG, "LT:", LT_URL)


if __name__ == "__main__":
    main()
