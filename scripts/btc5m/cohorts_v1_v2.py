"""Seven-cohort classification of Polymarket BTC 5m wallets, following Roni-1997/polymarket-segmentation.
Grid: maker share (>=70% high, 30-70% mid, <30% low) x cadence (fills per active day: >=100 fast, 10-100 systematic, <10 retail).
Retail = any maker share at <10 fills/day. Touched volume = maker side + taker side. Single day => cadence = fills that day.
Proxy-wallet level (no owner aggregation). PnL to settlement per leg: BUY pays 1 if outcome wins; SELL the reverse."""
import json, sys, collections
def load(day):
    tk=json.load(open(f'/tmp/pm5m_taker_tx_{day}.json')); both=json.load(open(f'/tmp/pm5m_both_tx_{day}.json'))
    outc={k.lower():v for k,v in json.load(open(f'/tmp/pm5m_outcomes_{day}.json')).items() if v is not None}
    key=lambda r:(r[7],r[0],r[2],round(r[3],6),round(r[4],6),r[6])
    tset=set(key(r) for r in tk)
    legs=[]  # (wallet, role, usd, pnl, cid, side, oi, ts)
    for r in both:
        w,cid,side,size,price,ts,oi,tx=r; role='taker' if key(r) in tset else 'maker'
        res=outc.get(cid); win=None if res is None else (1.0 if oi==res else 0.0)
        pnl=None if win is None else ((win-price)*size if side=='BUY' else (price-win)*size)
        legs.append((w,role,size*price,pnl,cid,side,oi,ts))
    return legs
def cohort(maker_share,fills):
    if fills<10: return 'Retail'
    cad='fast' if fills>=100 else 'systematic'
    band='high' if maker_share>=0.7 else 'mid' if maker_share>=0.3 else 'low'
    return {('high','fast'):'Pro-MM',('mid','fast'):'Hybrid-bot',('low','fast'):'Fast-taker',('high','systematic'):'Mid-MM',('mid','systematic'):'Systematic-mixed',('low','systematic'):'Systematic-taker'}[(band,cad)]
PERSONA={'Pro-MM':'MMs','Mid-MM':'MMs','Hybrid-bot':'Bots+Algo','Fast-taker':'Bots+Algo','Systematic-mixed':'Bots+Algo','Systematic-taker':'Bots+Algo','Retail':'Retail'}
ORDER=['Pro-MM','Fast-taker','Hybrid-bot','Systematic-taker','Mid-MM','Systematic-mixed','Retail']
def run(day):
    legs=load(day)
    W=collections.defaultdict(lambda:{'fills':0,'mk':0.0,'tk':0.0,'pnl':0.0,'cov':0.0,'pnl_t':0.0,'cov_t':0.0,'pnl_m':0.0,'cov_m':0.0})
    for w,role,usd,pnl,cid,side,oi,ts in legs:
        a=W[w]; a['fills']+=1; a['mk' if role=='maker' else 'tk']+=usd
        if pnl is not None:
            a['pnl']+=pnl; a['cov']+=usd
            if role=='taker': a['pnl_t']+=pnl; a['cov_t']+=usd
            else: a['pnl_m']+=pnl; a['cov_m']+=usd
    for w,a in W.items():
        tot=a['mk']+a['tk']; a['ms']=a['mk']/tot if tot else 0; a['cohort']=cohort(a['ms'],a['fills'])
    touched=sum(a['mk']+a['tk'] for a in W.values()); mk=sum(a['mk'] for a in W.values()); tk=sum(a['tk'] for a in W.values())
    n_t=sum(1 for l in legs if l[1]=='taker'); n_m=len(legs)-n_t
    print(f"\n{day}: legs {len(legs):,} (taker {n_t:,}, maker {n_m:,}), wallets {len(W):,}, touched ${touched/1e6:.2f}M, single-counted ${touched/2e6:.2f}M (taker $ {tk/1e6:.2f}M, maker $ {mk/1e6:.2f}M)")
    print(f"  {'cohort':17s} {'wallets':>7s} {'%touched':>8s} {'%maker side':>11s} {'%taker side':>11s} {'$/fill':>7s} {'PnL/$ all':>9s} {'PnL/$ taker':>11s} {'PnL/$ maker':>11s} {'PnL $':>9s}")
    rows={}
    for c in ORDER:
        ws=[a for a in W.values() if a['cohort']==c]
        if not ws: continue
        t=sum(a['mk']+a['tk'] for a in ws); m=sum(a['mk'] for a in ws); k=sum(a['tk'] for a in ws); f=sum(a['fills'] for a in ws)
        p=sum(a['pnl'] for a in ws); cv=sum(a['cov'] for a in ws); pt=sum(a['pnl_t'] for a in ws); ct=sum(a['cov_t'] for a in ws); pm=sum(a['pnl_m'] for a in ws); cm=sum(a['cov_m'] for a in ws)
        rows[c]=dict(wallets=len(ws),touched=100*t/touched,maker=100*m/mk,taker=100*k/tk,per_fill=t/f,pnl=100*p/cv if cv else 0,pnl_t=100*pt/ct if ct else 0,pnl_m=100*pm/cm if cm else 0,pnl_usd=p)
        r=rows[c]; print(f"  {c:17s} {r['wallets']:7d} {r['touched']:7.1f}% {r['maker']:10.1f}% {r['taker']:10.1f}% {r['per_fill']:7.0f} {r['pnl']:+8.2f}% {r['pnl_t']:+10.2f}% {r['pnl_m']:+10.2f}% {r['pnl_usd']:+9,.0f}")
    print(f"  {'persona':17s} {'wallets':>7s} {'%touched':>8s} {'%maker side':>11s} {'%taker side':>11s} {'PnL $':>9s}")
    for p in ('MMs','Bots+Algo','Retail'):
        cs=[c for c in ORDER if PERSONA[c]==p and c in rows]
        print(f"  {p:17s} {sum(rows[c]['wallets'] for c in cs):7d} {sum(rows[c]['touched'] for c in cs):7.1f}% {sum(rows[c]['maker'] for c in cs):10.1f}% {sum(rows[c]['taker'] for c in cs):10.1f}% {sum(rows[c]['pnl_usd'] for c in cs):+9,.0f}")
    json.dump({'day':day,'rows':rows,'touched':touched,'maker':mk,'taker':tk,'wallets':len(W)},open(f'/tmp/pm_cohorts_{day}.json','w'))
    return W
if __name__=='__main__':
    for d in sys.argv[1:]: run(d)

# ---------------- v2: same two axes, sharper operation-mode axis, plus directionality ----------------
def features_v2(legs, day0):
    """legs: (wallet, role, usd, pnl, cid, side, oi, ts). Orders = (wallet, cid, side, second). Buy orders only for the dollar test."""
    W=collections.defaultdict(lambda:{'fills':0,'mk':0.0,'tk':0.0,'pnl':0.0,'cov':0.0,'ts':set(),'orders':{},'mkts':collections.defaultdict(set),'sell':0.0,'pnl_t':0.0,'cov_t':0.0,'pnl_m':0.0,'cov_m':0.0})
    for w,role,usd,pnl,cid,side,oi,ts in legs:
        a=W[w]; a['fills']+=1; a['mk' if role=='maker' else 'tk']+=usd; a['ts'].add(ts)
        o=a['orders'].setdefault((cid,side,ts,oi),0.0); a['orders'][(cid,side,ts,oi)]=o+usd
        a['mkts'][cid].add((side,oi))
        if side=='SELL': a['sell']+=usd
        if pnl is not None:
            a['pnl']+=pnl; a['cov']+=usd
            if role=='taker': a['pnl_t']+=pnl; a['cov_t']+=usd
            else: a['pnl_m']+=pnl; a['cov_m']+=usd
    F={}
    for w,a in W.items():
        ts=sorted(a['ts']); day1=day0+86400
        gaps=[ts[i+1]-ts[i] for i in range(len(ts)-1)]+[(ts[0]-day0)+(day1-ts[-1])]
        gap=max(gaps)/3600; span=24-gap; hours=len(set(t//3600 for t in ts))
        n_orders=len(a['orders']); windows=len(a['mkts'])
        buys=[(k,v) for k,v in a['orders'].items() if k[1]=='BUY']
        exact=sum(1 for k,v in buys if v>=1 and abs(v-round(v))<0.0051)/max(len(buys),1)
        two=sum(1 for m in a['mkts'].values() if ('BUY',0) in m and ('BUY',1) in m)/windows
        dens=min(windows/max(span*12,1),1.0)
        tot=a['mk']+a['tk']; ms=a['mk']/tot if tot else 0
        F[w]=dict(fills=a['fills'],orders=n_orders,mk=a['mk'],tk=a['tk'],ms=ms,gap=gap,span=span,hours=hours,windows=windows,exact=exact,two=two,dens=dens,sellsh=a['sell']/tot if tot else 0,pnl=a['pnl'],cov=a['cov'],pnl_t=a['pnl_t'],cov_t=a['cov_t'],pnl_m=a['pnl_m'],cov_m=a['cov_m'])
    return F
def cohort_v2(f):
    if f['orders']<10: return 'Retail'
    unattended = f['gap']<6 or f['hours']>=16                      # runs through the day
    partday_machine = (f['two']>=0.4 and f['windows']>=5) or (f['dens']>=0.5 and f['span']>=4 and f['exact']<0.2)
    machine = unattended or partday_machine
    neutral = f['two']>=0.4 and f['windows']>=5
    if f['ms']>=0.7: return 'Pro-MM' if machine else 'Part-time MM'
    if machine: return 'Neutral bot' if neutral else 'Directional bot'
    return 'Session trader'
ORDER2=['Pro-MM','Part-time MM','Neutral bot','Directional bot','Session trader','Retail']
PERSONA2={'Pro-MM':'MMs','Part-time MM':'MMs','Neutral bot':'Machines','Directional bot':'Machines','Session trader':'People','Retail':'People'}
def run_v2(day):
    legs=load(day); day0=(min(l[7] for l in legs)//86400)*86400
    F=features_v2(legs,day0)
    for w,f in F.items(): f['c1']=cohort(f['ms'],f['fills']); f['c2']=cohort_v2(f)
    touched=sum(f['mk']+f['tk'] for f in F.values()); mk=sum(f['mk'] for f in F.values()); tk=sum(f['tk'] for f in F.values())
    print(f"\n{day} v2: wallets {len(F):,}, touched ${touched/1e6:.2f}M")
    print(f"  {'cohort v2':16s} {'wallets':>7s} {'%touched':>8s} {'%maker':>7s} {'%taker':>7s} {'PnL/$':>7s} {'PnL $':>9s} {'exact$':>7s} {'sells':>6s} {'hours':>6s}")
    import statistics as st
    rows={}
    for c in ORDER2:
        fs=[f for f in F.values() if f['c2']==c]
        if not fs: continue
        t=sum(f['mk']+f['tk'] for f in fs); m=sum(f['mk'] for f in fs); k=sum(f['tk'] for f in fs); p=sum(f['pnl'] for f in fs); cv=sum(f['cov'] for f in fs)
        rows[c]=dict(wallets=len(fs),touched=100*t/touched,maker=100*m/mk,taker=100*k/tk,pnl=100*p/cv if cv else 0,pnl_usd=p,exact=100*st.median(f['exact'] for f in fs),sells=100*sum(f['sellsh']*(f['mk']+f['tk']) for f in fs)/t,hours=st.median(f['hours'] for f in fs))
        r=rows[c]; print(f"  {c:16s} {r['wallets']:7d} {r['touched']:7.1f}% {r['maker']:6.1f}% {r['taker']:6.1f}% {r['pnl']:+6.2f}% {r['pnl_usd']:+9,.0f} {r['exact']:6.0f}% {r['sells']:5.0f}% {r['hours']:6.0f}")
    for p in ('MMs','Machines','People'):
        cs=[c for c in ORDER2 if PERSONA2[c]==p and c in rows]
        print(f"  {p:16s} {sum(rows[c]['wallets'] for c in cs):7d} {sum(rows[c]['touched'] for c in cs):7.1f}% {sum(rows[c]['maker'] for c in cs):6.1f}% {sum(rows[c]['taker'] for c in cs):6.1f}% {'':7s} {sum(rows[c]['pnl_usd'] for c in cs):+9,.0f}")
    # crosswalk v1 -> v2 by touched $
    print('  crosswalk (share of touched $): v1 cohort -> v2 cohorts')
    for c1 in ORDER:
        fs=[f for f in F.values() if f['c1']==c1]
        if not fs: continue
        t=sum(f['mk']+f['tk'] for f in fs); parts=collections.defaultdict(float)
        for f in fs: parts[f['c2']]+=f['mk']+f['tk']
        print(f"    {c1:17s} {100*t/touched:5.1f}%  -> "+', '.join(f"{c2} {100*v/t:.0f}%" for c2,v in sorted(parts.items(),key=lambda x:-x[1])))
    json.dump({'day':day,'rows':rows},open(f'/tmp/pm_cohorts_v2_{day}.json','w'))
    return F
