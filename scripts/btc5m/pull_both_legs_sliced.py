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
    rows,cap=page(cid,param)
    if not cap: return rows
    # need slicing: find time range from what we have, then slice from the earliest known ts backwards
    ts=[int(t['timestamp']) for t in rows]; hi=max(ts); lo=min(ts)
    # the cap dropped the oldest records (results are newest first): fetch older slices ending at lo
    out={ (t['transactionHash'],t['proxyWallet'],t['side'],t['size'],t['price'],t['outcomeIndex']):t for t in rows }
    end=lo; width=60; stats['sliced']+=1
    for _ in range(400):
        start=end-width
        sl,cap2=page(cid,param,f'&start={start}&end={end}')
        if cap2 and width>1: width=max(1,width//2); continue   # slice too dense: halve and retry
        for t in sl: out[(t['transactionHash'],t['proxyWallet'],t['side'],t['size'],t['price'],t['outcomeIndex'])]=t
        stats['slices']+=1
        if not sl and width>=300: break      # walked past the start of trading (5 min of silence)
        if not sl: width=min(300,width*2)
        end=start-1
    return list(out.values())
for day in sys.argv[1:]:
    t0=time.time(); cids=list(outcomes(day))
    for mode,param in (('taker','&takerOnly=true'),('both','&takerOnly=false')):
        outp=f'/tmp/pm5m_{mode}_tx_{day}.json'
        if os.path.exists(outp): print(day,mode,'exists',flush=True); continue
        rows=[]; stats={'sliced':0,'slices':0}
        for cid in cids:
            rows.extend(rec(t) for t in pull_market(cid,param,stats)); time.sleep(SLEEP)
        json.dump(rows,open(outp,'w'))
        print(day,mode,'records',len(rows),'markets sliced',stats['sliced'],'slices',stats['slices'],'secs',int(time.time()-t0),flush=True)
