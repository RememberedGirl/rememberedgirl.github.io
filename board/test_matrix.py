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
