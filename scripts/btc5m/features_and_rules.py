import os
DATA=os.environ.get('PM_DATA_DIR','/tmp')   # where the day files live
import json, collections, sys
def features(day):
    d=json.load(open(f'{DATA}/pm5m_fills_{day}.json')); outc={k.lower():v for k,v in json.load(open(f'{DATA}/pm5m_outcomes_{day}.json')).items() if v is not None}
    day0=(min(t[5] for t in d)//86400)*86400; day1=day0+86400
    W={}
    for w,cid,side,size,price,ts,oi in d:
        a=W.setdefault(w,{'fills':0,'usd':0.0,'ts':set(),'orders':{},'mk':collections.defaultdict(set),'pnl':0.0,'cov':0.0,'sell':0.0})
        a['fills']+=1; a['usd']+=size*price; a['ts'].add(ts)
        o=a['orders'].setdefault((cid,side,ts,oi),[0.0,0.0]); o[0]+=size; o[1]+=size*price
        a['mk'][cid].add((side,oi))
        r=outc.get(cid.lower())
        if r is not None:
            win=1.0 if oi==r else 0.0; a['pnl']+=(win-price)*size if side=='BUY' else (price-win)*size; a['cov']+=size*price
        if side=='SELL': a['sell']+=size*price
    F={}
    for w,a in W.items():
        ts=sorted(a['ts'])
        gaps=[(ts[i+1]-ts[i],ts[i],ts[i+1]) for i in range(len(ts)-1)]+[((ts[0]-day0)+(day1-ts[-1]),ts[-1],ts[0]+86400)]
        g,gs,ge=max(gaps); span=86400-g; avail=max(span/300,1)
        hrs=set(t//3600 for t in ts)
        buys=[(k,v) for k,v in a['orders'].items() if k[1]=='BUY']
        exact=sum(1 for k,v in buys if v[1]>=1 and abs(v[1]-round(v[1]))<0.0051)/max(len(buys),1)
        two=sum(1 for m in a['mk'].values() if ('BUY',0) in m and ('BUY',1) in m)/len(a['mk'])
        F[w]={'fills':a['fills'],'orders':len(a['orders']),'usd':a['usd'],'gap':g/3600,'gap_start_h':((gs-day0)%86400)/3600,'gap_end_h':((ge-day0)%86400)/3600,'span_h':span/3600,'windows':len(a['mk']),'dens':min(len(a['mk'])/avail,1.0),'hourcov':min(len(hrs)/max(span/3600,1),1),'exact':exact,'two':two,'pnl':a['pnl'],'cov':a['cov'],'sellsh':a['sell']/a['usd'] if a['usd'] else 0}
    json.dump(F,open(f'{DATA}/pm_wallet_features2_{day}.json','w')); return F
two=lambda f: f['two']>=0.4 and f['windows']>=5
sched=lambda f: f['dens']>=0.5 and f['span_h']>=4 and f['exact']<0.2
RULES={
 'report': lambda f: f['fills']>=300 or (f['fills']>=100 and f['hourcov']*f['span_h']>=16),
 'sleep-gap': lambda f: f['fills']>=300 or (f['fills']>=30 and f['gap']<6) or two(f),
 'pure-sleep': lambda f: f['gap']<6,
 'sleep+density, no fills': lambda f: f['gap']<6 or sched(f) or two(f),
 'combined': lambda f: f['fills']>=300 or (f['fills']>=30 and f['gap']<6) or two(f) or sched(f),
 'heavy=bots': lambda f: f['fills']>=30,
}
if __name__=='__main__':
    for day in sys.argv[1:]:
        F=features(day); tot=sum(f['usd'] for f in F.values()); cov=sum(f['cov'] for f in F.values())
        print(f"\n{day}: wallets {len(F):,} taker $ {tot:,.0f} outcome coverage {100*cov/tot:.0f}%")
        print(f"  {'rule':26s} {'bot $':>6s} {'bot w':>6s} {'botPnL':>7s} {'humPnL':>7s}")
        for name,fn in RULES.items():
            b=[f for f in F.values() if fn(f)]; h=[f for f in F.values() if not fn(f)]
            bu=sum(f['usd'] for f in b); bc=sum(f['cov'] for f in b); hc=sum(f['cov'] for f in h)
            print(f"  {name:26s} {100*bu/tot:5.1f}% {len(b):6d} {100*sum(f['pnl'] for f in b)/bc:+6.2f}% {100*sum(f['pnl'] for f in h)/hc:+6.2f}%")
        S=[f for f in F.values() if f['fills']>=30 and f['gap']>=6 and f['gap_end_h']<=14 and f['gap_start_h']>=20]
        print(f"  US-stock-hours sleepers with 30+ fills: {len(S)} wallets, {100*sum(f['usd'] for f in S)/tot:.1f}% of $; of which dense (>=0.5) share-typed: {100*sum(f['usd'] for f in S if f['dens']>=0.5 and f['exact']<0.2)/tot:.1f}% of $")
