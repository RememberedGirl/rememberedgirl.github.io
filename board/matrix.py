"""Average recorded attack stars per player and defender Town Hall."""
from collections import defaultdict


def attack_matrix(players, mode="absolute"):
    relative = mode == "cwl_relative"
    players=sorted((p for p in players if p.get('active',True)),key=lambda p:(-(p.get('town_hall') or 0),p['name'].casefold()))
    groups={};levels=set()
    for index,player in enumerate(players):
        cells=defaultdict(list)
        for war in player.get('wars',[]):
            if relative and war.get('kind') != 'CWL':
                continue
            for attack in war.get('attack_rows',[]):
                th,stars=attack.get('target_th'),attack.get('stars')
                if not isinstance(th,int) or th<1 or not isinstance(stars,(int,float)) or not 0<=stars<=3:
                    continue
                if relative:
                    own = attack.get('own_th')
                    if not isinstance(own, int) or own < 1:
                        continue
                    th -= own
                cells[th].append(stars);levels.add(th)
        groups[index]=cells
    own_levels=[p['town_hall'] for p in players if isinstance(p.get('town_hall'),int) and p['town_hall']>0]
    if relative:
        own_levels = [0]
    levels.update(own_levels)
    minimum=min(levels) if relative else min(own_levels) if own_levels else min(levels,default=1)
    levels=list(range(minimum,max(levels)+1)) if levels else []
    colors=[(120,25,48),(230,75,75),(235,194,55),(65,185,110)]
    rows=[]
    for number,player in enumerate(players,1):
        cells=[]
        for th in levels:
            stars=groups[number-1].get(th,[])
            if not stars:
                cells.append(dict(known=False,th=th,own_th=th==(0 if relative else player.get('town_hall'))));continue
            average=sum(stars)/len(stars)
            lower=int(average);upper=min(3,lower+1);fraction=average-lower
            color=','.join(str(round(a+(b-a)*fraction)) for a,b in zip(colors[lower],colors[upper]))
            cells.append(dict(known=True,th=th,own_th=th==(0 if relative else player.get('town_hall')),average=average,count=len(stars),color=color))
        if relative:
            for cell in cells:
                if cell.get('known'):
                    average = cell['average']
                    palette = ([(78,0,4),(78,0,4),(230,75,75),(65,185,110)] if cell['th'] < 0 else [(78,0,4),(230,75,75),(235,194,55),(65,185,110)] if cell['th'] == 0 else [(230,75,75),(235,194,55),(65,185,110),(65,185,110)])
                    low = int(average); fraction = average-low
                    cell['color'] = ','.join(str(round(a+(b-a)*fraction)) for a,b in zip(palette[low],palette[min(3,low+1)]))
        rows.append(dict(number=number,name=player['name'],slug=player.get('slug'),town_hall=player.get('town_hall'),cells=cells))
    if relative:
        for row in rows:
            eligible = [cell for cell in row['cells'] if cell['known'] and cell['th'] >= 0]
            count = sum(cell['count'] for cell in eligible)
            row['ranking_attacks'] = count
            row['ranking_average'] = sum(cell['average'] * cell['count'] for cell in eligible) / count if count else None
            known = [cell for cell in row['cells'] if cell['known']]
            total = sum(cell['count'] for cell in known)
            # Equal TH has full weight; harder targets reward skill, easier targets count less.
            row['skill_score'] = sum(cell['average'] * cell['count'] * (0.25 if cell['th'] < 0 else 1 if cell['th'] == 0 else 1.25) for cell in known) / total if total else None
            row['lower_share'] = sum(cell['count'] for cell in known if cell['th'] < 0) / total if total else 0
        rows.sort(key=lambda row: (row['skill_score'] is None, -(row['skill_score'] or 0), row['lower_share'], -(row['ranking_average'] or 0), -row['ranking_attacks'], row['name'].casefold()))
        for number, row in enumerate(rows, 1):
            row['number'] = number
    tables = [rows[i:i+25] for i in range(0, len(rows), 25)] if relative else [rows]
    return dict(levels=levels,rows=rows,tables=tables,width=210+34*len(levels),relative=relative)
