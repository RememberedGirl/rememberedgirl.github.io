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
    rivals=[c for c in data['columns'] if not c.get('own')]
    minimum_strength=min(c['strength'] for c in data['columns'])
    maximum_strength=max(c['strength'] for c in data['columns'])
    for column in data['columns']:
        column['difficulty']=min(7,1+sum(c['strength']<column['strength'] for c in rivals))
        ratio=(column['strength']-minimum_strength)/(maximum_strength-minimum_strength) if maximum_strength>minimum_strength else 0
        column['strength_percent']=round(100*max(0,min(1,ratio)),2)
        column['star_maximum']=maximum
        column['star_percent']=round(100*(column.get('total_stars') or 0)/maximum,2) if maximum else 0
    rows=[]
    for index in range(30):
        cells=[]
        for column in data['columns']:
            m=column['members'][index] if index<len(column['members']) else None
            cells.append(dict(member=m,own=column.get('own',False),played=column['played'],name=column['name'],number=index+1))
        rows.append(cells)
    return dict(opponents=data,rows=rows,asset_root=asset_root)
