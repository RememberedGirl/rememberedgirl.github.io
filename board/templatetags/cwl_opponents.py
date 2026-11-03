import json
from django import template
from django.conf import settings
register=template.Library()

@register.inclusion_tag('board/cwl_opponents.html')
def cwl_opponents(clan,asset_root=''):
    path=settings.BASE_DIR/'data/clans'/f'{clan}-opponents.json'
    if not path.is_file():return dict(opponents=None)
    data=json.loads(path.read_text())
    rows=[]
    for index in range(30):
        cells=[]
        for column in data['columns']:
            m=column['members'][index] if index<len(column['members']) else None
            cells.append(dict(member=m,played=column['played'],name=column['name'],number=index+1))
        rows.append(cells)
    return dict(opponents=data,rows=rows,asset_root=asset_root)
