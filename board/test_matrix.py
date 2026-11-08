from unittest import TestCase
from board.matrix import attack_matrix


def player(name,th,attacks,active=True):
    return dict(name=name,slug=name,town_hall=th,active=active,wars=[dict(attack_rows=attacks)])


class AttackMatrixTests(TestCase):
    def test_stars_are_averaged_per_attack_and_zero_counts(self):
        matrix=attack_matrix([player('A',13,[dict(target_th=12,stars=3),dict(target_th=12,stars=0),dict(target_th=14,stars=2)]),player('B',12,[])])
        self.assertEqual(matrix['levels'],[12,13,14])
        self.assertEqual(matrix['rows'][0]['cells'][0]['average'],1.5)
        self.assertEqual(matrix['rows'][0]['cells'][0]['count'],2)
        self.assertEqual(matrix['rows'][0]['cells'][2]['average'],2)

    def test_all_current_players_and_only_known_targets(self):
        matrix=attack_matrix([player('Low',8,[]),player('High',13,[dict(target_th=12,stars=3),dict(target_th=None,stars=3),dict(target_th=11,stars=None)]),player('Left',18,[dict(target_th=18,stars=3)],False)])
        self.assertEqual(matrix['levels'],list(range(8,14)))
        self.assertEqual([p['name'] for p in matrix['rows']],['High','Low'])
        self.assertFalse(matrix['rows'][1]['cells'][0]['known'])

    def test_roster_without_attack_history_has_no_fabricated_zeros(self):
        matrix=attack_matrix([dict(name='New',town_hall=9)])
        self.assertEqual(matrix['levels'],[9])
        self.assertFalse(matrix['rows'][0]['cells'][0]['known'])
        self.assertTrue(matrix['rows'][0]['cells'][0]['own_th'])

    def test_each_player_current_th_has_exactly_one_marker_even_without_attacks(self):
        matrix=attack_matrix([player('A',18,[]),player('B',13,[dict(target_th=12,stars=2)])])
        self.assertIn(18,matrix['levels'])
        for row in matrix['rows']:
            own=[c for c in row['cells'] if c['own_th']]
            self.assertEqual(len(own),1)
            self.assertEqual(own[0]['th'],row['town_hall'])

    def test_columns_begin_at_current_roster_minimum_not_old_attack_targets(self):
        matrix=attack_matrix([player('Current',13,[dict(target_th=4,stars=3),dict(target_th=14,stars=2)]),player('Low',7,[]),player('Former',3,[],False)])
        self.assertEqual(matrix['levels'],list(range(7,15)))
        self.assertNotIn(4,matrix['levels'])
        cells={c['th']:c for c in matrix['rows'][0]['cells']}
        self.assertEqual(cells[14]['average'],2)

    def test_cwl_relative_uses_attacker_th_at_attack_time(self):
        p=dict(name='A',town_hall=15,wars=[
            dict(kind='CW',attack_rows=[dict(own_th=13,target_th=18,stars=3)]),
            dict(kind='CWL',attack_rows=[dict(own_th=13,target_th=12,stars=0),dict(own_th=14,target_th=13,stars=2),dict(own_th=13,target_th=14,stars=2),dict(target_th=15,stars=3)])])
        matrix=attack_matrix([p], 'cwl_relative')
        self.assertEqual(matrix['levels'],[-1,0,1])
        cells=matrix['rows'][0]['cells']
        self.assertEqual(cells[0]['average'],1)
        self.assertEqual(cells[0]['count'],2)
        self.assertEqual(cells[0]['color'],'78,0,4')
        self.assertFalse(cells[1]['known'])
        self.assertTrue(cells[1]['own_th'])
        self.assertEqual(cells[2]['color'],'65,185,110')

    def test_relative_ranking_ignores_lower_targets_and_breaks_ties_by_count(self):
        def ranked(name, own_stars, lower_stars=()):
            return dict(name=name,town_hall=13,wars=[dict(kind='CWL',attack_rows=[dict(own_th=13,target_th=14,stars=s) for s in own_stars]+[dict(own_th=13,target_th=12,stars=s) for s in lower_stars])])
        matrix=attack_matrix([ranked('LowOnly',[],[3]),ranked('Weak',[1],[3,3]),ranked('Good',[3]),ranked('Reliable',[3,3])], 'cwl_relative')
        self.assertEqual([r['name'] for r in matrix['rows']],['Reliable','Good','Weak','LowOnly'])
        self.assertEqual([r['number'] for r in matrix['rows']],[1,2,3,4])
        self.assertIsNone(matrix['rows'][-1]['ranking_average'])

    def test_relative_tables_have_25_players_without_duplicates(self):
        matrix=attack_matrix([dict(name=f'P{i:02}',town_hall=13) for i in range(50)],'cwl_relative')
        self.assertEqual([len(t) for t in matrix['tables']],[25,25])
        self.assertEqual([r['number'] for t in matrix['tables'] for r in t],list(range(1,51)))

    def test_skill_ranking_rewards_harder_targets_and_penalizes_farming(self):
        def fighter(name, targets):
            return dict(name=name,town_hall=13,wars=[dict(kind='CWL',attack_rows=[dict(own_th=13,target_th=13+delta,stars=stars) for delta,stars in targets])])
        matrix=attack_matrix([
            fighter('Farm',[(0,3)]+[(-3,3)]*6),
            fighter('Equal',[(0,3)]*7),
            fighter('Higher',[(1,3)]*7),
            fighter('LowerOnly',[(-1,3)]*7),
            fighter('NoData',[]),
            fighter('Mixed',[(0,3),(1,3),(-1,3)]),
        ],'cwl_relative')
        self.assertEqual([r['name'] for r in matrix['rows']],['Higher','Equal','Mixed','Farm','LowerOnly','NoData'])
        self.assertEqual(matrix['rows'][2]['skill_score'],2.5)
