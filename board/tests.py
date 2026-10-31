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
