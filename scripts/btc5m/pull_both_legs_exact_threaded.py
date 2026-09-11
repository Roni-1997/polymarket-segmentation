"""Resumable puller for Polymarket BTC 5m markets: taker legs and both legs, with transaction hashes.
Pages by offset up to 10,000 records per query; if a market has more, splits its time range with the
data-api's `start`/`end` timestamp filters (inclusive) and pages each slice, halving slices that still hit the cap.
Writes /tmp/pm5m_taker_tx_<day>.json, /tmp/pm5m_both_tx_<day>.json, /tmp/pm5m_outcomes_<day>.json."""
import json, urllib.request, time, sys, os, datetime
UA={'user-agent':'curl/8'}; SLEEP=0.12; CAP=10000
def get(url, tries=12):
    err=''
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60))
        except Exception as e:
            err=str(e)[:80]
            if 'HTTP Error 400' in err: return None
            time.sleep(min(60,3*(i+1)))
    print('GIVEUP',url[:140],err,flush=True); return None
def outcomes(day):
    p=f'/tmp/pm5m_outcomes_{day}.json'
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
    """Exact, no dedup: newest page first; if full, complete the boundary second with a [lo,lo] slice, then walk
    backwards in adjacent inclusive time slices sized to ~800 records so offsets stay small. A slice that hits the
    offset cap is discarded and retried at half width."""
    first=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=1000&offset=0{param}')
    if not first: return []
    if len(first)<1000: return first
    ts=[int(t['timestamp']) for t in first]; hi=max(ts); lo=min(ts)
    out=[t for t in first if int(t['timestamp'])>lo]          # keep only complete seconds from the first page
    edge,cap=page(cid,param,f'&start={lo}&end={lo}')          # the boundary second, complete
    out.extend(edge); stats['sliced']+=1
    dens=1000/max(hi-lo,1); width=max(1,int(800/dens)); end=lo-1; empty=0
    while True:
        st=end-width+1
        sl,cap=page(cid,param,f'&start={st}&end={end}')
        stats['slices']+=1
        if cap:
            if width>1: width=max(1,width//2); continue
            # a single second over the cap: keep what we have (cannot be split further)
        out.extend(sl)
        if sl:
            empty=0; d=len(sl)/width; width=max(1,min(600,int(800/max(d,0.01))))
        else:
            empty+=width; width=min(600,width*2)
            if empty>=600:
                tail,cap=page(cid,param,f'&end={st-1}')      # everything older than the quiet stretch (listing-day fills)
                if not cap: out.extend(tail); break
                empty=0                                       # dense older history after all: keep slicing
        end=st-1
    return out
from concurrent.futures import ThreadPoolExecutor
import threading
T=int(os.environ.get('THREADS','6'))
for day in sys.argv[1:]:
    t0=time.time(); cids=list(outcomes(day))
    for mode,param in (('taker','&takerOnly=true'),('both','&takerOnly=false')):
        outp=f'/tmp/pm5m_{mode}_tx_{day}.json'
        if os.path.exists(outp): print(day,mode,'exists',flush=True); continue
        stats={'sliced':0,'slices':0}; lock=threading.Lock(); rows=[]
        def work(cid):
            r=[rec(t) for t in pull_market(cid,param,stats)]
            with lock: rows.extend(r)
        with ThreadPoolExecutor(max_workers=T) as ex: list(ex.map(work,cids))
        json.dump(rows,open(outp,'w'))
        print(day,mode,'records',len(rows),'markets sliced',stats['sliced'],'slices',stats['slices'],'secs',int(time.time()-t0),'threads',T,flush=True)
