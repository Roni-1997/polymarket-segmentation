"""Resumable puller for Polymarket BTC 5m markets: taker legs and both legs, with transaction hashes.
Pages by offset up to 10,000 records per query; if a market has more, splits its time range with the
data-api's `start`/`end` timestamp filters (inclusive) and pages each slice, halving slices that still hit the cap.
Writes <PM_DATA_DIR>/pm5m_taker_tx_<day>.json, /tmp/pm5m_both_tx_<day>.json, /tmp/pm5m_outcomes_<day>.json."""
import os
DATA=os.environ.get('PM_DATA_DIR','/tmp')   # where the day files live
import json, urllib.request, time, sys, os, datetime
UA={'user-agent':'curl/8'}; SLEEP=0.12; CAP=10000
import threading, random
RATE=float(os.environ.get('RATE','4'))          # requests per second for this process, all threads together
_lock=threading.Lock(); _next=[time.time()]
def _acquire():
    with _lock:
        now=time.time(); t=max(_next[0], now); _next[0]=t+1.0/RATE
    wait=t-time.time()
    if wait>0: time.sleep(wait)
STATS={'429':0}
def get(url, tries=15):
    err=''
    for i in range(tries):
        _acquire()
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=90))
        except urllib.error.HTTPError as e:
            if e.code==400: return None
            if e.code==429:
                STATS['429']+=1; ra=e.headers.get('Retry-After'); base=float(ra) if ra and ra.replace('.','',1).isdigit() else 0
                time.sleep(max(base,1.0)*min(8,1+i)+random.random()); continue
            err=f'HTTP {e.code}'; time.sleep(min(60,3*(i+1)))
        except Exception as e:
            err=str(e)[:80]; time.sleep(min(60,3*(i+1)))
    print('GIVEUP',url[:140],err,flush=True); return None
def outcomes(day):
    p=f'{DATA}/pm5m_outcomes_{day}.json'
    if os.path.exists(p): return json.load(open(p))
    nxt=(datetime.date.fromisoformat(day)+datetime.timedelta(days=1)).isoformat(); out={}; off=0
    while True:
        ev=get(f'https://gamma-api.polymarket.com/events?series_id=10684&limit=100&offset={off}&end_date_min={day}T00:00:00Z&end_date_max={nxt}T00:00:00Z&closed=true')
        if ev is None: break
        for e in ev:
            for m in e.get('markets',[]):
                cid=m.get('conditionId')
                try: pr=[float(x) for x in json.loads(m.get('outcomePrices') or '[]')]
                except Exception: pr=[]
                if cid: out[cid.lower()]=pr.index(max(pr)) if len(pr)==2 and max(pr)>=0.99 else None
        if len(ev)<100: break
        off+=100
    json.dump(out,open(p,'w')); return out
def rec(t): return [t['proxyWallet'].lower(),t['conditionId'].lower(),t['side'],float(t['size']),float(t['price']),int(t['timestamp']),int(t['outcomeIndex']),t['transactionHash']]
def page(cid,param,extra=''):
    """returns (rows, hit_cap)"""
    rows=[]; off=0
    while True:
        tr=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=1000&offset={off}{param}{extra}')
        if tr is None: return rows, off>=CAP
        rows.extend(tr)
        if len(tr)<1000: return rows, False
        off+=1000
        if off>=CAP: return rows, True
        time.sleep(SLEEP)
def pull_market(cid,param,stats):
    """Exact, no dedup, ~1000 records per request: page newest-first in chunks of up to 10k (the offset cap);
    after each capped chunk, drop the partial oldest second and restart an inclusive `end=<that second>` chunk."""
    out=[]; extra=''
    while True:
        chunk,cap=page(cid,param,extra)
        stats['slices']+=1
        if not cap: out.extend(chunk); return out
        lo=min(int(t['timestamp']) for t in chunk)
        kept=[t for t in chunk if int(t['timestamp'])>lo]
        if not kept:                      # a single second holds 10k+ records: keep the partial second (cannot split further)
            out.extend(chunk); return out
        out.extend(kept); extra=f'&end={lo}'; stats['sliced']+=1
from concurrent.futures import ThreadPoolExecutor
import threading
T=int(os.environ.get('THREADS','6'))
import re as _re
if len(sys.argv)<2 or not all(_re.fullmatch(r'\d{4}-\d{2}-\d{2}',a) for a in sys.argv[1:]):
    print('usage: python3 '+sys.argv[0].split('/')[-1]+' YYYY-MM-DD [YYYY-MM-DD ...]   (env: PM_DATA_DIR, RATE, THREADS)'); sys.exit(1)
for day in sys.argv[1:]:
    t0=time.time(); cids=list(outcomes(day))
    for mode,param in (('taker','&takerOnly=true'),('both','&takerOnly=false')):
        outp=f'{DATA}/pm5m_{mode}_tx_{day}.json'
        if os.path.exists(outp): print(day,mode,'exists',flush=True); continue
        stats={'sliced':0,'slices':0}; lock=threading.Lock(); rows=[]
        def work(cid):
            r=[rec(t) for t in pull_market(cid,param,stats)]
            with lock: rows.extend(r)
        with ThreadPoolExecutor(max_workers=T) as ex: list(ex.map(work,cids))
        json.dump(rows,open(outp,'w'))
        print(day,mode,'records',len(rows),'markets sliced',stats['sliced'],'slices',stats['slices'],'secs',int(time.time()-t0),'threads',T,'rate',RATE,'429s',STATS['429'],flush=True); STATS['429']=0
