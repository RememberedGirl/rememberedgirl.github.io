import json
import hashlib
from django.conf import settings
from django.http import Http404
from django.shortcuts import render


def load_data():
    if not settings.PUBLIC_SNAPSHOT.is_file():
        return dict(clan_name='Blushing snow', generated=None, players=[], season='')
    return json.loads(settings.PUBLIC_SNAPSHOT.read_text())


def context(data, root='', design='classic'):
    css = settings.BASE_DIR / 'board/static/board' / ('berserk.css' if design == 'berserk' else 'site.css')
    styles = css.read_bytes()
    if design == 'masters':
        styles += (settings.BASE_DIR/'board/static/board/masters.css').read_bytes()
    styles += (settings.BASE_DIR/'board/static/board/site.js').read_bytes()
    version = hashlib.sha256(styles).hexdigest()[:12]
    return dict(site=data, root=root, asset_root=root+('../' if design in ('berserk','masters') else ''), asset_version=version)


def rankings(players, kind):
    candidates = [p for p in players if p['active'] and p['stats'][kind]['wars']]
    return sorted(candidates, key=lambda p: (-p['stats'][kind]['clan_stars'], -p['stats'][kind]['attendance_rate'], -p['stats'][kind]['average'], p['name']))


def home_context(data, root='', design='classic'):
    ctx = context(data, root, design)
    active = sorted((p for p in data['players'] if p['active']), key=lambda p: (-p['town_hall'], p['name'].casefold()))
    ctx.update(players=active, archive=[p for p in data['players'] if not p['active']], cwl=rankings(active, 'CWL'), cw=rankings(active, 'CW'))
    return ctx


def home(request, design='classic'):
    template = 'board/berserk/home.html' if design == 'berserk' else 'board/home.html'
    return render(request, template, home_context(load_data(), design=design))


def player(request, slug, design='classic'):
    data = load_data()
    record = next((p for p in data['players'] if p['slug'] == slug), None)
    if record is None:
        raise Http404('Игрок не найден')
    template = 'board/berserk/player.html' if design == 'berserk' else 'board/player.html'
    return render(request, template, dict(context(data, '../../', design), player=record))


def other_clan_context():
    from collections import Counter
    path = settings.BASE_DIR / 'data/clans/2PQQ2RJ0R.json'
    if not path.is_file():
        raise Http404('Состав клана ещё не загружен')
    clan = json.loads(path.read_text())
    history_path = settings.BASE_DIR / 'data/clans/2PQQ2RJ0R-history.json'
    history = json.loads(history_path.read_text()) if history_path.is_file() else None
    if history:
        clan['players'] = [p for p in history['players'] if p['active']]
        clan['generated'] = history['generated']
    players = sorted(clan['players'], key=lambda p: (-(p['town_hall'] or 0), -(p['league'] or 0), p['name'].casefold()))
    for number, player in enumerate(players, 1):
        player['number'] = number
    counts = Counter(p['town_hall'] for p in players if p['town_hall'])
    split = (len(players)+1)//2
    style = settings.BASE_DIR / 'board/static/board/masters.css'
    return dict(clan=clan, history=history, roster_columns=[players[:split], players[split:]], composition=[dict(th=th,count=counts[th]) for th in sorted(counts,reverse=True)], top_th=max(counts,default=0), version=hashlib.sha256(style.read_bytes()).hexdigest()[:12])


def other_clan(request):
    return render(request, 'board/other_clan.html', other_clan_context())


def other_player(request, slug):
    data = other_clan_context()['history']
    record = next((p for p in (data or {}).get('players',[]) if p['slug']==slug),None)
    if record is None:
        raise Http404('Игрок не найден')
    return render(request,'board/masters_player.html',dict(context(data,'../../','masters'),player=record))
