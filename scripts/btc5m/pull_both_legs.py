import json, urllib.request, time, sys
UA={'user-agent':'curl/8'}
def get(url, tries=10):
    err=''
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60))
        except Exception as e: err=str(e)[:80]; time.sleep(2*(i+1))
    print('GIVEUP',url[:140],err,flush=True); return None
def rec(t): return [t['proxyWallet'].lower(),t['conditionId'].lower(),t['side'],float(t['size']),float(t['price']),int(t['timestamp']),int(t['outcomeIndex']),t['transactionHash']]
for day in sys.argv[1:]:
    t0=time.time(); outc=json.load(open(f'/tmp/pm5m_outcomes_{day}.json')); cids=list(outc)
    for mode,param in (('taker','&takerOnly=true'),('both','&takerOnly=false')):
        rows=[]; maxoff=0; trunc=0
        for cid in cids:
            off=0
            while True:
                tr=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=1000&offset={off}{param}')
                if tr is None: break
                rows.extend(rec(t) for t in tr)
                if len(tr)<1000: break
                off+=1000; maxoff=max(maxoff,off)
                if off>=40000: trunc+=1; break
                time.sleep(0.1)
            time.sleep(0.1)
        json.dump(rows,open(f'/tmp/pm5m_{mode}_tx_{day}.json','w'))
        print(day,mode,'records',len(rows),'max offset',maxoff,'truncated',trunc,'secs',int(time.time()-t0),flush=True)
