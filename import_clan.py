"""Collect a separate public clan roster; never modifies the primary clan database."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--tag', default='#2PQQ2RJ0R')
    args = parser.parse_args()
    import requests
    from dotenv import load_dotenv
    load_dotenv(args.source/'clashofclans.env', override=True)
    token = os.getenv('COC_TOKEN', '').strip()
    if not token:
        raise SystemExit('Не задан COC_TOKEN в clashofclans.env')
    tag = '#'+args.tag.strip().lstrip('#').upper()
    with requests.Session() as session:
        session.headers.update(Authorization='Bearer '+token, Accept='application/json')
        def get(path):
            r = session.get('https://api.clashofclans.com/v1'+path, timeout=(10,35))
            if r.status_code != 200:
                raise SystemExit(f'CoC API HTTP {r.status_code}; публичный снимок не изменён')
            return r.json()
        path = '/clans/'+quote(tag, safe='')
        clan = get(path)
        members = get(path+'/members').get('items', [])
    if not members:
        raise SystemExit('Пустой состав; публичный снимок не изменён')
    catalog = json.loads((args.source/'data/ranked_league_levels.json').read_text())
    leagues = {row['id']: row for row in catalog}
    players = []
    for m in members:
        tier = leagues.get((m.get('leagueTier') or {}).get('id'), {})
        players.append(dict(name=m.get('name','Без имени'), town_hall=m.get('townHallLevel'), league=tier.get('level'), league_name=tier.get('name'), role=m.get('role'), trophies=m.get('trophies'), donations=m.get('donations'), received=m.get('donationsReceived')))
    players.sort(key=lambda p: (-(p['town_hall'] or 0), -(p['league'] or 0), p['name'].casefold()))
    result = dict(tag=tag, name=clan['name'], level=clan.get('clanLevel'), description=clan.get('description',''), war_league=(clan.get('warLeague') or {}).get('name'), generated=datetime.now(ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y, %H:%M МСК'), players=players)
    target = Path(__file__).resolve().parent/'data/clans'/(tag[1:]+'.json')
    target.parent.mkdir(exist_ok=True)
    temp = target.with_suffix('.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');temp.replace(target)
    print(f'Клан: {clan["name"]} · Игроков: {len(players)} · {result["generated"]}')


if __name__ == '__main__':
    main()
