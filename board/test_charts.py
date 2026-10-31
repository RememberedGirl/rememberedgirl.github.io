from unittest import TestCase
from board.charts import development_chart


class DevelopmentChartTests(TestCase):
    def test_town_hall_uses_steps_and_real_date_spacing(self):
        history=[dict(date='2026-10-01',town_hall=8),dict(date='2026-10-02',town_hall=8),dict(date='2026-10-11',town_hall=9)]
        chart=development_chart(history,[('town_hall','ТХ')],'TH',True)
        series=chart['series'][0]
        self.assertEqual([p['x'] for p in series['points']],[48,97.6,544])
        self.assertEqual(series['paths'][0].count('L '),4)
        self.assertFalse(chart['single'])

    def test_season_reset_and_unknown_values_break_lines(self):
        history=[dict(date='2026-10-01',donated=100),dict(date='2026-10-02',donated=120),dict(date='2026-10-03',donated=0),dict(date='2026-10-04',donated=None),dict(date='2026-10-05',donated=10)]
        chart=development_chart(history,[('donated','Отдано')],'Donation')
        self.assertEqual(len(chart['series'][0]['paths']),3)
        self.assertEqual(len(chart['series'][0]['points']),4)
        self.assertEqual(chart['resets'][0]['date'],'03.10.2026')
        self.assertEqual(chart['series'][0]['points'][2]['value'],0)

    def test_one_observation_is_a_point_and_unknown_is_not_zero(self):
        chart=development_chart([dict(date='2026-10-31',donated=0)],[('donated','Отдано')],'Donation')
        self.assertTrue(chart['single'])
        self.assertEqual(chart['series'][0]['points'][0]['x'],296)
        self.assertTrue(chart['has_data'])
        self.assertFalse(development_chart([dict(date='2026-10-31',donated=None)],[('donated','Отдано')],'Donation')['has_data'])
