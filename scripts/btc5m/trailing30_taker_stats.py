"""Trailing-30-day aggregation of Polymarket BTC 5m taker fills: per-wallet cumulative PnL, cadence per active day,
profitability by persistence and size, and the combined-rule machine share day by day and pooled."""
import json, os, sys, collections, statistics as st
sys.path.insert(0,'/tmp'); from pm_features_day import features, RULES
days=json.load(open('/tmp/pm_trailing30_days.json'))
have=[d for d in days if os.path.exists(f'/tmp/pm5m_fills_{d}.json') and os.path.exists(f'/tmp/pm5m_outcomes_{d}.json')]
print(f'days available {len(have)}/{len(days)}: {have[0]} .. {have[-1]}')
comb=RULES['combined']
P=collections.defaultdict(lambda:{'pnl':0.0,'cov':0.0,'usd':0.0,'fills':0,'days':0,'bot_days':0,'first':None,'last':None})
daily=[]
for d in have:
    F=features(d); tot=sum(f['usd'] for f in F.values())
    bots=[f for f in F.values() if comb(f)]; bu=sum(f['usd'] for f in bots)
    prof=sum(1 for f in F.values() if f['pnl']>0.01); n=len(F)
    daily.append({'day':d,'taker_usd':tot,'wallets':n,'machine_share':100*bu/tot,'profitable_pct':100*prof/n,'human_pnl':100*sum(f['pnl'] for f in F.values() if not comb(f))/max(sum(f['cov'] for f in F.values() if not comb(f)),1),'machine_pnl':100*sum(f['pnl'] for f in bots)/max(sum(f['cov'] for f in bots),1)})
    for w,f in F.items():
        a=P[w]; a['pnl']+=f['pnl']; a['cov']+=f['cov']; a['usd']+=f['usd']; a['fills']+=f['fills']; a['days']+=1; a['bot_days']+=1 if comb(f) else 0
        a['first']=a['first'] or d; a['last']=d
tot=sum(a['usd'] for a in P.values())
print(f"\nwallets {len(P):,}  taker $ {tot/1e6:.1f}M over {len(have)} days  ({tot/len(have)/1e6:.2f}M/day)")
print("\nDaily machine share (combined rule) and profitable-wallet share:")
for r in daily: print(f"  {r['day']} taker ${r['taker_usd']/1e6:5.2f}M wallets {r['wallets']:6,} machines {r['machine_share']:5.1f}% (PnL {r['machine_pnl']:+5.2f}%) people PnL {r['human_pnl']:+5.2f}% profitable wallets {r['profitable_pct']:4.1f}%")
ms=[r['machine_share'] for r in daily]; print(f"  machine share: mean {st.mean(ms):.1f}%, min {min(ms):.1f}%, max {max(ms):.1f}%, $-weighted {100*sum(r['machine_share']*r['taker_usd'] for r in daily)/sum(r['taker_usd'] for r in daily)/100:.1f}%")
# wallet-level over the window
for w,a in P.items(): a['cad']=a['fills']/a['days']; a['modal_bot']=a['bot_days']*2>a['days']
prof=sum(1 for a in P.values() if a['pnl']>0.01)
print(f"\nCumulative over the window: {100*prof/len(P):.1f}% of wallets profitable; median PnL/$ {100*st.median(a['pnl']/a['cov'] for a in P.values() if a['cov']>0):+.2f}%")
print("By active days in the window:")
for lab,lo,hi in (('1',1,2),('2-4',2,5),('5-9',5,10),('10-19',10,20),('20+',20,99)):
    ws=[a for a in P.values() if lo<=a['days']<hi]
    if ws: print(f"  {lab:6s} wallets {len(ws):6,}  profitable {100*sum(1 for a in ws if a['pnl']>0.01)/len(ws):5.1f}%  median PnL/$ {100*st.median(a['pnl']/a['cov'] for a in ws if a['cov']>0):+6.2f}%  share of $ {100*sum(a['usd'] for a in ws)/tot:5.1f}%")
print("By cadence (fills per active day, segmentation bands):")
for lab,lo,hi in (('<10',0,10),('10-100',10,100),('100+',100,1e9)):
    ws=[a for a in P.values() if lo<=a['cad']<hi]
    print(f"  {lab:6s} wallets {len(ws):6,}  share of $ {100*sum(a['usd'] for a in ws)/tot:5.1f}%  profitable {100*sum(1 for a in ws if a['pnl']>0.01)/len(ws):5.1f}%  PnL/$ {100*sum(a['pnl'] for a in ws)/max(sum(a['cov'] for a in ws),1):+6.2f}%")
print("By total $ traded in the window:")
for lab,lo,hi in (('<$100',0,100),('$100-1k',100,1e3),('$1k-10k',1e3,1e4),('$10k-100k',1e4,1e5),('$100k-1M',1e5,1e6),('$1M+',1e6,1e12)):
    ws=[a for a in P.values() if lo<=a['usd']<hi]
    if ws: print(f"  {lab:10s} wallets {len(ws):6,}  profitable {100*sum(1 for a in ws if a['pnl']>0.01)/len(ws):5.1f}%  median PnL/$ {100*st.median(a['pnl']/a['cov'] for a in ws if a['cov']>0):+6.2f}%  share of $ {100*sum(a['usd'] for a in ws)/tot:5.1f}%")
mach=[a for a in P.values() if a['modal_bot']]; ppl=[a for a in P.values() if not a['modal_bot']]
print(f"\nModal class over the window: machines {len(mach):,} wallets, {100*sum(a['usd'] for a in mach)/tot:.1f}% of $, PnL {100*sum(a['pnl'] for a in mach)/sum(a['cov'] for a in mach):+.2f}%, {100*sum(1 for a in mach if a['pnl']>0.01)/len(mach):.1f}% profitable; people {len(ppl):,} wallets, {100*sum(a['usd'] for a in ppl)/tot:.1f}% of $, PnL {100*sum(a['pnl'] for a in ppl)/sum(a['cov'] for a in ppl):+.2f}%, {100*sum(1 for a in ppl if a['pnl']>0.01)/len(ppl):.1f}% profitable")
gains=sorted((a['pnl'] for a in P.values() if a['pnl']>0), reverse=True); k=max(1,len(P)//100)
print(f"Top 1% of wallets ({k}) take {100*sum(gains[:k])/sum(gains):.0f}% of gross gains; top 0.1% take {100*sum(gains[:max(1,len(P)//1000)])/sum(gains):.0f}%")
json.dump({'days':have,'daily':daily,'wallets':len(P),'taker_usd':tot},open('/tmp/pm_trailing30_summary.json','w'),indent=1)
