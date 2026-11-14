"""Public inactivity signals from observed opportunities, never missing history."""
from datetime import datetime, timedelta


def inactivity_signals(data, player, history):
    now = datetime.fromisoformat(data['generated']).date()
    cutoff = (now-timedelta(days=30)).isoformat()
    tag = player['tag']
    first = player.get('first_seen','')[:10]
    ended = {w['war_id']:w for w in data['wars'] if w['state'] in ('warEnded','warEndedIncomplete')
             and cutoff <= (w.get('end_time') or '')[:10] <= now.isoformat()}
    hits = {}
    for a in data['attacks']:
        hits[(a['war_id'],a['attacker_tag'])] = hits.get((a['war_id'],a['attacker_tag']),0)+1
    signals = {}
    for kind in ['CWL','CW']:
        wars = [m for m in data['members'] if m['player_tag']==tag and m['war_id'] in ended
                and ended[m['war_id']]['kind']==kind]
        missed = sum(hits.get((m['war_id'],tag),0)==0 for m in wars)
        signals[kind] = dict(missed=missed,total=len(wars))
    attacks = [a['stars'] for a in data['attacks'] if a['war_id'] in ended
               and a['attacker_tag']==tag and a['stars'] is not None]
    signals['average'] = dict(value=sum(attacks)/len(attacks) if attacks else None,attacks=len(attacks))
    observed = data.get('membership',{}).get('daily_rosters',[])
    raids = []
    for raid in data.get('raids',[]):
        start,end = (raid.get('start_time') or '')[:10],(raid.get('end_time') or '')[:10]
        members = [m for m in data.get('raid_members',[]) if m['raid_id']==raid['raid_id']]
        present = any(start<=d['date']<=end and any(p['tag']==tag for p in d['roster']) for d in observed)
        if raid.get('state')=='ended' and cutoff<=end<=now.isoformat() and first<=start and present and members:
            raids.append(any(m['player_tag']==tag and (m.get('attacks') or 0)>0 for m in members))
    signals['raids'] = dict(missed=sum(not x for x in raids),total=len(raids))
    games = data.get('clan_games',{}).get('players',{}).get(tag,{})
    seasons = sorted({season for p in data.get('clan_games',{}).get('players',{}).values() for season in p.get('seasons',{})
                      if cutoff<=season+'-28'<=now.isoformat()})
    game_values = []
    for season in seasons:
        # Zero is meaningful only when observations span this actual games event.
        if first<=season+'-22' and games.get('first_seen','')[:10]<=season+'-22' and games.get('last_seen','')[:10]>=season+'-28' and games.get('samples',0)>=2:
            game_values.append(games.get('seasons',{}).get(season,0))
    signals['games'] = dict(missed=sum(v==0 for v in game_values),total=len(game_values))
    samples = sorted([h for h in history if cutoff<=h['date']<=now.isoformat()
                      and h.get('donated') is not None and h.get('received') is not None],key=lambda h:h['date'])
    comparisons = changes = 0
    for a,b in zip(samples,samples[1:]):
        # Seasonal counter resets are neither activity nor inactivity.
        if b['donated']<a['donated'] or b['received']<a['received']:
            continue
        comparisons += 1
        changes += (b['donated'],b['received']) != (a['donated'],a['received'])
    span = (datetime.fromisoformat(samples[-1]['date'])-datetime.fromisoformat(samples[0]['date'])).days if samples else 0
    signals['donations'] = dict(changes=changes,comparisons=comparisons,known=comparisons>=4 and span>=7)
    return signals
