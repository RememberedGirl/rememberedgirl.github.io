"""Run locally beside the collector. Export only an explicit public whitelist."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo

ENDED = {'warEnded', 'warEndedIncomplete'}


def build_public(data, all_players, histories, clan_name='Blushing snow'):
    slugs = {p['tag']: hashlib.sha256(p['tag'].encode()).hexdigest()[:16] for p in all_players}
    war_map = {w['war_id']: w for w in data['wars']}
    members = defaultdict(list)
    attacks = defaultdict(list)
    for member in data['members']:
        members[member['player_tag']].append(member)
    for attack in data['attacks']:
        attacks[attack['attacker_tag'], attack['war_id']].append(attack)
    current = {p['tag']: p for p in data['players']}
    generated = datetime.fromisoformat(data['generated']).astimezone(ZoneInfo('Europe/Moscow'))
    season = generated.strftime('%Y-%m')
    raid_map = {r['raid_id']: r for r in data.get('raids', [])}
    raid_members = defaultdict(list)
    for member in data.get('raid_members', []):
        raid_members[member['player_tag']].append(member)
    from datetime import timezone
    def moment(value):
        try:
            dt = datetime.fromisoformat(value.replace('Z','+00:00'))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (AttributeError, ValueError):
            return None
    def army_color(value):
        scale = data.get('army_scale') or {}
        lo, mid, hi = (scale.get(key) for key in ('minimum','middle','maximum'))
        if value is None or None in (lo,mid,hi):
            return None
        lower = value <= mid
        start,end = ((255,255,255),(255,31,119)) if lower else ((255,31,119),(92,0,227))
        a,b = (lo,mid) if lower else (mid,hi)
        ratio = max(0,min(1,(value-a)/(b-a))) if b>a else 0
        return 'rgb('+','.join(str(round(x+(y-x)*ratio)) for x,y in zip(start,end))+')'
    # CoC Clan Games seasons start on the 22nd, not on the first of the month.
    games_month = generated.month if generated.day >= 22 else generated.month-1
    games_year = generated.year if games_month else generated.year-1
    games_season = f'{games_year:04d}-{games_month or 12:02d}'
    records = []
    for row in all_players:
        p = current.get(row['tag'], row)
        history = []
        for member in members[row['tag']]:
            war = war_map.get(member['war_id'])
            if not war:
                continue
            mine = sorted(attacks[row['tag'], war['war_id']], key=lambda a: a['attack_order'])
            ended = war['state'] in ENDED
            allowed = member.get('attacks_allowed') or war.get('attacks_per_member') or 2
            attack_rows = [dict(stars=a['stars'], destruction=a['destruction'], own_th=a['attacker_th'], target_th=a['defender_th'], target_name=a['defender_name'], contribution=a['clan_stars'], mirror=a.get('mirror')) for a in mine]
            date = war.get('end_time') or ''
            history.append(dict(war_id=hashlib.sha256(war['war_id'].encode()).hexdigest()[:16], kind=war['kind'], end=date, month=date[:7], date_label=date[:10], opponent=war['opponent'], state=war['state'], ended=ended, attacks=len(mine), allowed=allowed, stars=sum(a['stars'] or 0 for a in mine), clan_stars=sum(a['clan_stars'] for a in mine), attack_rows=attack_rows))
        history.sort(key=lambda w: w['end'], reverse=True)
        stats = {}
        for kind in ('CW', 'CWL'):
            selected = [w for w in history if w['kind'] == kind and w['ended']]
            total_attacks = sum(w['attacks'] for w in selected)
            attended = sum(w['attacks'] > 0 for w in selected)
            stars = sum(w['stars'] for w in selected)
            stats[kind] = dict(wars=len(selected), attended=attended, missed=len(selected)-attended, attacks=total_attacks, stars=stars, clan_stars=sum(w['clan_stars'] for w in selected), average=round(stars/total_attacks, 1) if total_attacks else 0, attendance_rate=round(100*attended/len(selected)) if selected else 0, success=sum(a['stars'] is not None and a['stars'] >= 2 for w in selected for a in w['attack_rows']))
        games = (data.get('clan_games') or {}).get('players', {}).get(row['tag'])
        game_seasons = (games or {}).get('seasons', {})
        games_public = dict(current_season=games_season, current=game_seasons.get(games_season, 0) if games and games.get('gained') is not None else None,
                            total=(games or {}).get('gained'), seasons=[dict(season=k,points=v) for k,v in sorted(game_seasons.items(),reverse=True)])
        raid_history = []
        for member in raid_members[row['tag']]:
            raid = raid_map.get(member['raid_id'])
            end = moment((raid or {}).get('end_time'))
            first = moment(row.get('first_seen'))
            if not raid or not end or not first or end < first:
                continue
            raid_history.append(dict(start=raid.get('start_time'),end=raid['end_time'],date_label=(raid.get('start_time') or '')[:10],
                                     attacks=member.get('attacks') or 0,loot=member.get('capital_resources_looted') or 0,
                                     allowed=(member.get('attack_limit') or 0)+(member.get('bonus_attack_limit') or 0)))
        raid_history.sort(key=lambda r:r['start'] or '',reverse=True)
        latest_raid = max(data.get('raids', []),key=lambda r:r.get('start_time') or '',default=None)
        latest = next((r for r in raid_history if latest_raid and r['start']==latest_raid.get('start_time')),None)
        raids_public = dict(total_loot=sum(r['loot'] for r in raid_history),total_attacks=sum(r['attacks'] for r in raid_history),
                            count=len(raid_history),latest=latest,history=raid_history)
        army = (data.get('armies') or {}).get(row['tag'])
        army_public = None
        if army:
            boosted = (army.get('boosts') or {}).get('with_both')
            army_public = dict(weight=army['weight'],with_potions=boosted,updated=(army.get('collected_at') or '')[:16].replace('T',' '),
                               color=army_color(army['weight']),potion_color=army_color(boosted))
        records.append(dict(games=games_public,raids=raids_public,army=army_public,role=row.get('role'),slug=slugs[row['tag']], name=row['name'], active=bool(row['active']), town_hall=p.get('town_hall') or (histories.get(row['tag']) or [{}])[0].get('town_hall') or 0, league=p.get('current_league_level'), days=p.get('observed_days'), first_seen=(row.get('first_seen') or '')[:10], stats=stats, wars=history, development=histories.get(row['tag'], [])))
    return dict(version=1, clan_name=clan_name, generated=generated.strftime('%d.%m.%Y, %H:%M МСК'), season=season, players=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--db', type=Path)
    parser.add_argument('--clan-name', default='Blushing snow')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent/'data/clan.json')
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    from clan_html_dashboard import read_dashboard
    db = (args.db or args.source/'clan_analytics.db').resolve()
    data = read_dashboard(db)
    with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        players = [dict(r) for r in conn.execute('SELECT p.tag,p.name,p.active,p.first_seen,s.role FROM players p LEFT JOIN snapshots s ON s.tag=p.tag AND s.snapshot_date=(SELECT MAX(snapshot_date) FROM snapshots WHERE tag=p.tag)')]
        columns = {r[1] for r in conn.execute('PRAGMA table_info(snapshots)')}
        league = 'ranked_league_name' if 'ranked_league_name' in columns else 'NULL'
        donated = 'donations' if 'donations' in columns else 'NULL'
        received = 'donations_received' if 'donations_received' in columns else 'NULL'
        histories = defaultdict(list)
        for r in conn.execute(f'SELECT tag,snapshot_date,town_hall,{league} AS league,{donated} AS donated,{received} AS received FROM snapshots ORDER BY snapshot_date DESC'):
            histories[r['tag']].append(dict(date=r['snapshot_date'], town_hall=r['town_hall'], league=r['league'], donated=r['donated'], received=r['received']))
    payload = build_public(data, players, histories, args.clan_name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    print(f'Публичный снимок: {args.output} · Игроков: {len(payload["players"])}')


if __name__ == '__main__':
    main()
