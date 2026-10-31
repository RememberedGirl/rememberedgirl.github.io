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


def build_public(data, all_players, histories):
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
            attack_rows = [dict(stars=a['stars'], destruction=a['destruction'], own_th=a['attacker_th'], target_th=a['defender_th'], target_name=a['defender_name'], contribution=a['clan_stars']) for a in mine]
            date = war.get('end_time') or ''
            history.append(dict(kind=war['kind'], end=date, month=date[:7], date_label=date[:10], opponent=war['opponent'], state=war['state'], ended=ended, attacks=len(mine), allowed=allowed, stars=sum(a['stars'] or 0 for a in mine), clan_stars=sum(a['clan_stars'] for a in mine), attack_rows=attack_rows))
        history.sort(key=lambda w: w['end'], reverse=True)
        stats = {}
        for kind in ('CW', 'CWL'):
            selected = [w for w in history if w['kind'] == kind and w['ended']]
            total_attacks = sum(w['attacks'] for w in selected)
            attended = sum(w['attacks'] > 0 for w in selected)
            stars = sum(w['stars'] for w in selected)
            stats[kind] = dict(wars=len(selected), attended=attended, missed=len(selected)-attended, attacks=total_attacks, stars=stars, clan_stars=sum(w['clan_stars'] for w in selected), average=round(stars/total_attacks, 1) if total_attacks else 0, attendance_rate=round(100*attended/len(selected)) if selected else 0, success=sum(a['stars'] is not None and a['stars'] >= 2 for w in selected for a in w['attack_rows']))
        records.append(dict(slug=slugs[row['tag']], name=row['name'], active=bool(row['active']), town_hall=p.get('town_hall') or (histories.get(row['tag']) or [{}])[0].get('town_hall') or 0, league=p.get('current_league_level'), days=p.get('observed_days'), first_seen=(row.get('first_seen') or '')[:10], stats=stats, wars=history, development=histories.get(row['tag'], [])))
    return dict(version=1, clan_name='Blushing snow', generated=generated.strftime('%d.%m.%Y, %H:%M МСК'), season=season, players=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--db', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent/'data/clan.json')
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    from clan_html_dashboard import read_dashboard
    db = (args.db or args.source/'clan_analytics.db').resolve()
    data = read_dashboard(db)
    with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        players = [dict(r) for r in conn.execute('SELECT tag,name,active,first_seen FROM players')]
        columns = {r[1] for r in conn.execute('PRAGMA table_info(snapshots)')}
        league = 'ranked_league_name' if 'ranked_league_name' in columns else 'NULL'
        histories = defaultdict(list)
        for r in conn.execute(f'SELECT tag,snapshot_date,town_hall,{league} AS league FROM snapshots ORDER BY snapshot_date DESC'):
            histories[r['tag']].append(dict(date=r['snapshot_date'], town_hall=r['town_hall'], league=r['league']))
    payload = build_public(data, players, histories)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    print(f'Публичный снимок: {args.output} · Игроков: {len(payload["players"])}')


if __name__ == '__main__':
    main()
