from django.test import SimpleTestCase
from board.removal import removal_ranking
from removal_export import inactivity_signals


class RemovalTests(SimpleTestCase):
    def test_unknown_and_departed_are_not_ranked(self):
        result=removal_ranking([dict(active=True,name='Unknown'),dict(active=False,name='Left')])
        self.assertEqual(result['ranked'],[])
        self.assertEqual(len(result['unknown']),1)
        self.assertIsNone(result['unknown'][0]['score'])

    def test_cwl_priority_and_strict_average_threshold(self):
        def player(name,cwl,cw,average):
            return dict(active=True,name=name,removal={'CWL':dict(missed=cwl,total=1),
                'CW':dict(missed=cw,total=1),'average':dict(value=average,attacks=2)})
        r=removal_ranking([player('cw',0,1,2.5),player('cwl',1,0,2.5),player('good',0,0,2.5)])
        self.assertEqual([x['player']['name'] for x in r['ranked']],['cwl','cw'])
        self.assertNotIn('Средние звёзды ниже 2,5',r['ranked'][0]['reasons'])

    def test_eligibility_dates_and_counter_resets(self):
        data=dict(generated='2026-11-14T12:00:00+03:00',wars=[
            dict(war_id='ended',kind='CWL',state='warEnded',end_time='2026-11-10'),
            dict(war_id='live',kind='CW',state='inWar',end_time='2026-11-14'),
            dict(war_id='old',kind='CW',state='warEnded',end_time='2026-09-10')],
            members=[dict(war_id=w,player_tag='p') for w in ['ended','live','old']],attacks=[],
            raids=[dict(raid_id='r',state='ended',start_time='2026-11-06',end_time='2026-11-09')],
            raid_members=[dict(raid_id='r',player_tag='other',attacks=6)],
            membership={'daily_rosters':[dict(date='2026-11-07',roster=[dict(tag='p')])]},clan_games={'players':{}})
        history=[dict(date=f'2026-11-{day:02}',donated=value,received=value) for day,value in [(1,10),(3,10),(5,10),(7,0),(9,0),(11,0)]]
        p=dict(tag='p',first_seen='2026-10-01')
        s=inactivity_signals(data,p,history)
        self.assertEqual(s['CWL'],dict(missed=1,total=1))
        self.assertEqual(s['CW']['total'],0)
        self.assertEqual(s['raids'],dict(missed=1,total=1))
        self.assertEqual(s['games']['total'],0)
        self.assertEqual(s['donations'],dict(changes=0,comparisons=4,known=True))
        data['membership']['daily_rosters']=[]
        self.assertEqual(inactivity_signals(data,p,history)['raids']['total'],0)
