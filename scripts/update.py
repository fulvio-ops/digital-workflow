#!/usr/bin/env python3
# v5: genera data/articoli.json dai feed
import json,time,re,sys,pathlib
from datetime import datetime,timezone
import feedparser
try:
    from bs4 import BeautifulSoup; HAVE_BS=True
except Exception:
    HAVE_BS=False
BASE=pathlib.Path(__file__).resolve().parent; DATA=BASE.parent/'data'
CFG=json.loads((DATA/'feed_sources.json').read_text(encoding='utf-8'))
def clean(s,m=220):
    t=s or ''
    if HAVE_BS:
        try:t=BeautifulSoup(t,'html.parser').get_text(' ',strip=True)
        except Exception:pass
    t=re.sub(r'\s+',' ',t).strip(); 
    return (t[:m].rsplit(' ',1)[0]+'…') if len(t)>m else t
rows=[]
for u in CFG.get('feeds',[]):
    d=feedparser.parse(u); fonte=d.feed.get('title','Fonte')
    for e in d.entries:
        link=(getattr(e,'link','') or '').strip()
        title=clean(getattr(e,'title','')); desc=clean(getattr(e,'summary','') or getattr(e,'description',''))
        ts=getattr(e,'published_parsed',None) or getattr(e,'updated_parsed',None)
        ts=int(time.mktime(ts)) if ts else int(time.time())
        if not (title or desc): continue
        rows.append({'ts':ts,'titolo':title,'descrizione':desc,'link':link,'fonte':fonte})
kw=[k.lower() for k in CFG.get('keywords',[])]
def ok(i): 
    txt=(i['titolo']+' '+i['descrizione']).lower()
    return any(k in txt for k in kw) if kw else True
rows=[i for i in rows if ok(i)]
dedup={}
for it in rows:
    key=it['link'] or it['titolo']
    if key not in dedup or it['ts']>dedup[key]['ts']: dedup[key]=it
out=sorted(dedup.values(), key=lambda x:x['ts'], reverse=True)[:int(CFG.get('max_items',24))]
for it in out: it['data']=datetime.fromtimestamp(it.pop('ts'),tz=timezone.utc).isoformat()
DATA.joinpath('articoli.json').write_text(json.dumps({'last_updated':datetime.now(timezone.utc).isoformat(),'items':out}, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK articoli:', len(out))
