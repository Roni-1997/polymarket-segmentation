import json, urllib.request, time, sys, datetime
UA={'user-agent':'curl/8'}
def get(url, tries=10):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60))
        except Exception as e:
            err=str(e)[:80]; time.sleep(2*(i+1))
    print('GIVEUP',url[:120],err,flush=True); return None
for day in sys.argv[1:]:
    t0=time.time(); nxt=(datetime.date.fromisoformat(day)+datetime.timedelta(days=1)).isoformat()
    cids=[]; off=0
    while True:
        ev=get(f'https://gamma-api.polymarket.com/events?series_id=10684&limit=100&offset={off}&end_date_min={day}T00:00:00Z&end_date_max={nxt}T00:00:00Z&closed=true')
        if ev is None: break
        for e in ev:
            for m in e.get('markets',[]):
                cid=m.get('conditionId')
                try: prices=[float(x) for x in json.loads(m.get('outcomePrices') or '[]')]
                except Exception: prices=[]
                if cid: cids.append((cid.lower(), prices.index(max(prices)) if len(prices)==2 and max(prices)>=0.99 else None))
        if len(ev)<100: break
        off+=100
    print(day,'markets',len(cids),flush=True)
    rows=[]; trunc=0
    for cid,res in cids:
        off=0
        while True:
            tr=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=1000&offset={off}')
            if tr is None: break
            for t in tr:
                try: rows.append([t['proxyWallet'].lower(),cid,t['side'],float(t['size']),float(t['price']),int(t['timestamp']),int(t['outcomeIndex'])])
                except Exception: pass
            if len(tr)<1000: break
            off+=1000
            if off>=10000: trunc+=1; break
            time.sleep(0.12)
        time.sleep(0.12)
    json.dump(rows,open(f'/tmp/pm5m_fills_{day}.json','w'))
    json.dump({c:r for c,r in cids},open(f'/tmp/pm5m_outcomes_{day}.json','w'))
    print(day,'fills',len(rows),'truncated markets',trunc,'secs',int(time.time()-t0),flush=True)
