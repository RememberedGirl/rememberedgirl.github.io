import json
from django import template
from django.conf import settings
register=template.Library()

@register.inclusion_tag('board/cwl_opponents.html')
def cwl_opponents(clan,asset_root=''):
    path=settings.BASE_DIR/'data/clans'/f'{clan}-opponents.json'
    if not path.is_file():return dict(opponents=None)
    data=json.loads(path.read_text())
    maximum=max((c.get('total_stars') or 0 for c in data['columns']),default=0)
    for column in data['columns']:
        column['strength']=sum(m.get('th') or 0 for m in column['members'])
    ordered_strengths=sorted({c['strength'] for c in data['columns']})
    for column in data['columns']:
        position=ordered_strengths.index(column['strength'])
        column['difficulty']=1+int(9*position/max(1,len(ordered_strengths)-1)+0.5)
        column['star_maximum']=maximum
        column['star_percent']=round(100*(column.get('total_stars') or 0)/maximum,2) if maximum else 0
    rows=[]
    for index in range(30):
        cells=[]
        for column in data['columns']:
            m=column['members'][index] if index<len(column['members']) else None
            cells.append(dict(member=m,played=column['played'],name=column['name'],number=index+1))
        rows.append(cells)
    return dict(opponents=data,rows=rows,asset_root=asset_root)
