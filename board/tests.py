import io
import json
from pathlib import Path
import tempfile
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from import_snapshot import build_public


def sample():
    wars = [dict(war_id='past', kind='CWL', state='warEndedIncomplete', end_time='2026-10-20T20:00:00+03:00', opponent='Rivals'), dict(war_id='prep', kind='CWL', state='preparation', end_time='2026-11-01T20:00:00+03:00', opponent='Next')]
    players = [dict(tag='#A', name='<script>alert(1)</script>', active=1, first_seen='2026-10-01', town_hall=13, observed_days=30, current_league_level=10), dict(tag='#B', name='Former', active=0, first_seen='2026-10-01')]
    attacks = [dict(attacker_tag='#A', war_id='past', attack_order=1, stars=2, destruction=80, attacker_th=13, defender_th=14, defender_name='Enemy', clan_stars=1)]
    members = [dict(player_tag='#A', war_id='past', attacks_allowed=1), dict(player_tag='#B', war_id='past', attacks_allowed=1), dict(player_tag='#A', war_id='prep', attacks_allowed=1)]
    return build_public(dict(generated='2026-10-31T12:00:00+00:00', wars=wars, members=members, attacks=attacks, players=players[:1], raw_json='PRIVATE'), players, {})


class PublicSiteTests(SimpleTestCase):
    def test_stats_use_completed_wars_and_actual_attacks(self):
        a, b = sample()['players']
        self.assertEqual(a['stats']['CWL']['wars'], 1)
        self.assertEqual(a['stats']['CWL']['missed'], 0)
        self.assertEqual(a['stats']['CWL']['clan_stars'], 1)
        self.assertEqual(a['stats']['CWL']['stars'], 2)
        self.assertEqual(a['stats']['CWL']['success'], 1)
        self.assertEqual(b['stats']['CWL']['missed'], 1)
        self.assertFalse(b['active'])
        self.assertEqual(len(a['wars']), 2)

    def test_public_snapshot_is_whitelisted_and_slugs_are_stable(self):
        data = sample()
        serialized = json.dumps(data)
        self.assertNotIn('#A', serialized)
        self.assertNotIn('raw_json', serialized)
        self.assertNotIn('PRIVATE', serialized)
        self.assertEqual(data['players'][0]['slug'], sample()['players'][0]['slug'])
        self.assertTrue(all(p['slug'].isalnum() for p in data['players']))

    def test_django_pages_and_static_export_are_escaped_and_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root/'snapshot.json'
            data = sample()
            snapshot.write_text(json.dumps(data))
            with override_settings(PUBLIC_SNAPSHOT=snapshot):
                response = self.client.get('/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
                self.assertEqual(self.client.get('/index.html').status_code, 200)
                self.assertEqual(self.client.get('/players/missing/').status_code, 404)
                slug = data['players'][0]['slug']
                response = self.client.get(f'/players/{slug}/')
                self.assertEqual(response.status_code, 200)
                call_command('export_site', output=str(root/'public'), stdout=io.StringIO())
                html = (root/'public/players'/slug/'index.html').read_text()
                self.assertIn('../../assets/board/site.css', html)
                self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
                self.assertEqual(self.client.get('/berserk/').status_code, 200)
                self.assertEqual(self.client.get(f'/berserk/players/{slug}/').status_code, 200)
                alternative = (root/'public/berserk/index.html').read_text()
                self.assertIn('Один против', alternative)
                self.assertIn('../assets/board/berserk.css', alternative)
                self.assertIn('Посмотреть другой дизайн', alternative)
                self.assertNotIn('Один против', (root/'public/index.html').read_text())
                self.assertTrue((root/'public/.nojekyll').is_file())
                self.assertTrue((root/'public/assets/board/site.js').is_file())
                self.assertFalse(list((root/'public').rglob('*.db')))
                self.assertFalse(list((root/'public').rglob('*.json')))

    def test_other_clan_has_independent_sorted_roster(self):
        from board.views import other_clan_context
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'data/clans').mkdir(parents=True)
            (root/'board/static/board').mkdir(parents=True)
            (root/'board/static/board/masters.css').write_text('body{}')
            players = [dict(name='Low', town_hall=8, league=20, role='member'), dict(name='<script>bad</script>', town_hall=13, league=2, role='leader'), dict(name='High', town_hall=13, league=3, role='member')]
            payload = dict(name='Masters of War', tag='#2PQQ2RJ0R', level=8, description='', war_league='Gold League II', generated='today', players=players)
            (root/'data/clans/2PQQ2RJ0R.json').write_text(json.dumps(payload))
            with override_settings(BASE_DIR=root):
                ctx = other_clan_context()
                roster = sum(ctx['roster_columns'], [])
                self.assertEqual([p['name'] for p in roster], ['High','<script>bad</script>','Low'])
                self.assertEqual([p['number'] for p in roster], [1,2,3])
                self.assertEqual(ctx['composition'],[dict(th=13,count=2),dict(th=8,count=1)])
                response = self.client.get('/2PQQ2RJ0R/')
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'&lt;script&gt;bad&lt;/script&gt;')

    def test_profile_activities_respect_clan_games_season_and_raid_membership(self):
        person=dict(tag='#A',name='Player',active=1,first_seen='2026-10-20T12:00:00+03:00',town_hall=8)
        data=dict(generated='2026-11-01T12:00:00+03:00',wars=[],members=[],attacks=[],players=[person],
                  clan_games=dict(players={'#A':dict(gained=10000,seasons={'2026-10':6400},total=259999)}),
                  raids=[dict(raid_id='old',start_time='2026-10-10T07:00:00Z',end_time='2026-10-13T07:00:00Z'),dict(raid_id='new',start_time='2026-10-30T07:00:00Z',end_time='2026-11-02T07:00:00Z')],
                  raid_members=[dict(player_tag='#A',raid_id='old',attacks=6,capital_resources_looted=50000),dict(player_tag='#A',raid_id='new',attacks=5,capital_resources_looted=10000)],
                  armies={'#A':dict(weight=1132,collected_at='2026-11-01T12:00:00+03:00',boosts=dict(with_both=8730))},army_scale=dict(minimum=1132,middle=4502,maximum=8730))
        profile=build_public(data,[person],{},'Masters of War')['players'][0]
        self.assertEqual(profile['games']['current_season'],'2026-10')
        self.assertEqual(profile['games']['current'],6400)
        self.assertEqual(profile['games']['total'],10000)
        self.assertEqual(profile['raids']['total_loot'],10000)
        self.assertEqual(profile['raids']['total_attacks'],5)
        self.assertEqual(profile['raids']['latest']['loot'],10000)
        self.assertEqual(profile['army']['color'],'rgb(255,255,255)')
        self.assertEqual(profile['army']['potion_color'],'rgb(92,0,227)')
        self.assertNotIn('259999',json.dumps(profile))
        data['clan_games']['players']['#A']['gained']=None
        data['armies']={}
        profile=build_public(data,[person],{})['players'][0]
        self.assertIsNone(profile['games']['current'])
        self.assertIsNone(profile['games']['total'])
        self.assertIsNone(profile['army'])
