from django.test import SimpleTestCase
from board.templatetags.cwl_grid import build_grid


class CwlGridTests(SimpleTestCase):
    def test_mirror_only_zero_and_nonparticipants(self):
        def war(key, attacks):
            return dict(war_id=key,kind='CWL',month='2026-11',end=key,date_label='02.11',opponent='Rivals',attack_rows=attacks)
        players=[dict(name='A',town_hall=18, wars=[war('1',[dict(stars=3,mirror=False)]),war('2',[dict(stars=2,mirror=True)])]),dict(name='B',town_hall=17,wars=[war('1',[dict(stars=0,mirror=True)])])]
        rows=build_grid(players)['rows']
        self.assertEqual([c['stars'] for c in rows[0]['cells']],[0,2])
        self.assertEqual(rows[1]['cells'][0]['stars'],0)
        self.assertIsNone(rows[1]['cells'][1])
        self.assertFalse(rows[0]['cells'][0]['attacked'])
        self.assertTrue(rows[1]['cells'][0]['attacked'])
        from django.template.loader import render_to_string
        html=render_to_string('board/cwl_grid_content.html',build_grid(players))
        self.assertIn('Нет сохранённой атаки по зеркалу"></span>',html)
        self.assertIn('0 ★ по зеркалу">0</span>',html)
