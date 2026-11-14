"""Explainable review ranking; incomplete observations are not zero activity."""
WEIGHTS = {'CWL':35,'CW':25,'raids':15,'games':10,'donations':10,'average':5}


def removal_ranking(players):
    rows=[]
    for p in players:
        if not p['active']:
            continue
        s=p.get('removal') or {}
        penalties={}
        cells={}
        for key in ['CWL','CW','raids','games']:
            v=s.get(key,{})
            total=v.get('total',0)
            cells[key]=f'{v.get("missed",0)} / {total}' if total else '—'
            if total:
                penalties[key]=v['missed']/total
        v=s.get('donations',{})
        cells['donations']=f'{v["changes"]} / {v["comparisons"]}' if v.get('known') else '—'
        if v.get('known'):
            penalties['donations']=1 if v['changes']/v['comparisons']<=0.2 else 0
        avg=s.get('average',{})
        value=avg.get('value')
        cells['average']=f'{value:.2f} ★ · {avg.get("attacks",0)} атак' if value is not None else '—'
        if value is not None:
            penalties['average']=1 if value<2.5 else 0
        weight=sum(WEIGHTS[k] for k in penalties)
        score=100*sum(WEIGHTS[k]*v for k,v in penalties.items())/weight if weight else None
        reasons=[]
        labels={'CWL':'Пропуски ЛВК','CW':'Пропуски КВ','raids':'Пропуски рейдов','games':'Нет участия в играх','donations':'Редко меняются подкрепления','average':'Средние звёзды ниже 2,5'}
        reasons=[labels[k] for k,v in penalties.items() if v>0]
        rows.append(dict(player=p,score=score,known=len(penalties),eligible=len(penalties)>=3,
                         cells=cells,reasons=', '.join(reasons) or 'Нет подтверждённых признаков'))
    ranked=sorted([r for r in rows if r['eligible'] and r['score']>0],key=lambda r:(-r['score'],-r['known'],r['player']['name'].casefold()))
    return dict(ranked=ranked,unknown=[r for r in rows if not r['eligible']])
