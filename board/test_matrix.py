from unittest import TestCase
from board.matrix import attack_matrix


def player(name,th,attacks,active=True):
    return dict(name=name,slug=name,town_hall=th,active=active,wars=[dict(attack_rows=attacks)])


class AttackMatrixTests(TestCase):
    def test_stars_are_averaged_per_attack_and_zero_counts(self):
        matrix=attack_matrix([player('A',13,[dict(target_th=12,stars=3),dict(target_th=12,stars=0),dict(target_th=14,stars=2)])])
        self.assertEqual(matrix['levels'],[12,14])
        self.assertEqual(matrix['rows'][0]['cells'][0]['average'],1.5)
        self.assertEqual(matrix['rows'][0]['cells'][0]['count'],2)
        self.assertEqual(matrix['rows'][0]['cells'][1]['average'],2)

    def test_all_current_players_and_only_known_targets(self):
        matrix=attack_matrix([player('Low',8,[]),player('High',13,[dict(target_th=12,stars=3),dict(target_th=None,stars=3),dict(target_th=11,stars=None)]),player('Left',18,[dict(target_th=18,stars=3)],False)])
        self.assertEqual(matrix['levels'],[12])
        self.assertEqual([p['name'] for p in matrix['rows']],['High','Low'])
        self.assertFalse(matrix['rows'][1]['cells'][0]['known'])

    def test_roster_without_attack_history_has_no_fabricated_zeros(self):
        matrix=attack_matrix([dict(name='New',town_hall=9)])
        self.assertEqual(matrix['levels'],[])
        self.assertEqual(matrix['rows'][0]['cells'],[])
