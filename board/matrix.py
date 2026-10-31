"""Average recorded attack stars per player and defender Town Hall."""
from collections import defaultdict


def attack_matrix(players):
    players=sorted((p for p in players if p.get('active',True)),key=lambda p:(-(p.get('town_hall') or 0),p['name'].casefold()))
    groups={};levels=set()
    for index,player in enumerate(players):
        cells=defaultdict(list)
        for war in player.get('wars',[]):
            for attack in war.get('attack_rows',[]):
                th,stars=attack.get('target_th'),attack.get('stars')
                if not isinstance(th,int) or th<1 or not isinstance(stars,(int,float)) or not 0<=stars<=3:
                    continue
                cells[th].append(stars);levels.add(th)
        groups[index]=cells
    levels=sorted(levels)
    colors=[(120,25,48),(230,75,75),(235,194,55),(65,185,110)]
    rows=[]
    for number,player in enumerate(players,1):
        cells=[]
        for th in levels:
            stars=groups[number-1].get(th,[])
            if not stars:
                cells.append(dict(known=False,th=th));continue
            average=sum(stars)/len(stars)
            lower=int(average);upper=min(3,lower+1);fraction=average-lower
            color=','.join(str(round(a+(b-a)*fraction)) for a,b in zip(colors[lower],colors[upper]))
            cells.append(dict(known=True,th=th,average=average,count=len(stars),color=color))
        rows.append(dict(number=number,name=player['name'],slug=player.get('slug'),town_hall=player.get('town_hall'),cells=cells))
    return dict(levels=levels,rows=rows)
