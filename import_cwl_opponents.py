"""Export only clan names, TH levels and stars for the public opponent grid."""
import argparse,json,shutil
from pathlib import Path

def export(source,clan,filename):
    raw=json.loads((source/filename).read_text())
    teams={t['tag']:t for t in raw['opponents']}
    schedule=raw['schedule'];assigned={d['opponent_tag'] for d in schedule if d['opponent_tag']}
    pending=iter(t for t in raw['opponents'] if t['tag'] not in assigned)
    columns=[]
    for day in schedule:
        team=teams.get(day['opponent_tag']);unknown=team is None
        if unknown:team=next(pending)
        played=day['state'] in ('inWar','warEnded')
        members=day.get('members') or team['members']
        columns.append(dict(day=None if unknown else day['round'],name=team['name'],played=played,state=day['state'],members=[dict(th=m['town_hall'],stars=m.get('stars') if played else None) for m in members]))
    result=dict(season=raw['season'],collected_at=raw['collected_at'],columns=columns)
    output=Path(__file__).resolve().parent/'data/clans'/f'{clan}-opponents.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    folder=Path(__file__).resolve().parent/'board/static/board/images/town_halls';folder.mkdir(parents=True,exist_ok=True)
    for image in (source/'assets/town_halls').glob('*.webp'):shutil.copy2(image,folder/image.name)
    print(clan,'7 соперников,',sum(len(c['members']) for c in columns),'ратуш')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('.'));p.add_argument('--clan',required=True);p.add_argument('--input',required=True);a=p.parse_args();export(a.source,a.clan,a.input)
