"""Small SVG chart geometry based solely on saved daily observations."""
from datetime import date
import math


def development_chart(history, keys, title, stepped=False):
    rows = []
    for row in history:
        try:
            day = date.fromisoformat(row['date'][:10])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((day,row))
    rows.sort(key=lambda item:item[0])
    values = [row.get(key) for _,row in rows for key,_ in keys if isinstance(row.get(key),(int,float))]
    if not values:
        return dict(title=title,has_data=False)
    left,right,top,bottom = 48,544,18,202
    first,last = rows[0][0].toordinal(),rows[-1][0].toordinal()
    x = lambda day: round((left+right)/2 if first==last else left+(day.toordinal()-first)/(last-first)*(right-left),2)
    if stepped:
        lower,upper = max(1,min(values)-1),max(max(values),min(18,max(values)+1))
        tick_values = list(range(int(lower),int(upper)+1))
        if len(tick_values)>6:
            step=math.ceil((upper-lower)/5)
            tick_values=list(range(int(lower),int(upper)+1,step))
    else:
        lower=0
        maximum=max(values)
        raw=max(1,maximum/4)
        power=10**math.floor(math.log10(raw))
        step=next(factor*power for factor in (1,2,5,10) if factor*power>=raw)
        upper=max(step,math.ceil(maximum/step)*step)
        tick_values=list(range(0,int(upper)+1,int(step)))
    y=lambda value:round(bottom-(value-lower)/(upper-lower)*(bottom-top),2)
    series=[];reset_dates=set()
    for key,label in keys:
        paths=[];path=[];points=[];previous=None
        for day,row in rows:
            value=row.get(key)
            if not isinstance(value,(int,float)):
                if path:paths.append(' '.join(path))
                path=[];previous=None;continue
            xx,yy=x(day),y(value)
            if not stepped and previous and value<previous[1]:
                reset_dates.add(day)
                if path:paths.append(' '.join(path))
                path=[];previous=None
            if not path:path=[f'M {xx} {yy}']
            elif stepped:path.extend([f'L {xx} {y(previous[1])}',f'L {xx} {yy}'])
            else:path.append(f'L {xx} {yy}')
            points.append(dict(x=xx,y=yy,value=value,date=day.strftime('%d.%m.%Y')))
            previous=(day,value)
        if path:paths.append(' '.join(path))
        series.append(dict(key=key,label=label,paths=paths,points=points))
    days=sorted({day for day,_ in rows})
    indices=sorted({round(i*(len(days)-1)/min(3,len(days)-1)) for i in range(min(4,len(days)))}) if len(days)>1 else [0]
    return dict(title=title,has_data=True,series=series,
                y_ticks=[dict(y=y(value),label=f'{value:g}') for value in tick_values],
                x_ticks=[dict(x=x(days[i]),label=days[i].strftime('%d.%m')) for i in indices],
                resets=[dict(x=x(day),date=day.strftime('%d.%m.%Y')) for day in sorted(reset_dates)],
                single=len(days)==1)


def profile_charts(player):
    history=player.get('development') or []
    return [development_chart(history,[('town_hall','Ратуша')],'Уровень ратуши',stepped=True),
            development_chart(history,[('donated','Отдано'),('received','Получено')],'Отданные и полученные войска')]
