from django import template
register = template.Library()


def build_grid(players):
    wars = {w['war_id']: w for p in players for w in p.get('wars', []) if w['kind'] == 'CWL' and w.get('war_id')}
    if not wars:
        return dict(rows=[], wars=[])
    month = max(w.get('month', '') for w in wars.values())
    ordered = sorted(((key, w) for key, w in wars.items() if w.get('month') == month), key=lambda item: (item[1]['end'], item[0]))
    rows = []
    for p in sorted(players, key=lambda p: (-(p.get('town_hall') or 0), p['name'].casefold())):
        participation = {w.get('war_id'): w for w in p.get('wars', [])}
        cells = []
        for key, war in ordered:
            member = participation.get(key)
            if member is None:
                cells.append(None)
                continue
            mirror = [a for a in member.get('attack_rows', []) if a.get('mirror') in (True, 1)]
            stars = max((a.get('stars') or 0 for a in mirror), default=0)
            cells.append(dict(stars=stars, title=war['opponent'] + ' · ' + war['date_label'] + ' · ' + str(stars) + ' ★ по зеркалу'))
        if any(c is not None for c in cells):
            rows.append(dict(player=p, cells=cells))
    return dict(rows=rows, wars=[dict(number=i+1, opponent=w['opponent'], date=w['date_label']) for i, (_, w) in enumerate(ordered)], month=month)


@register.inclusion_tag('board/cwl_grid_content.html')
def cwl_grid(players):
    return build_grid(players)
