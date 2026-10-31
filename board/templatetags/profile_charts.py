from django import template
from board.charts import profile_charts
register=template.Library()
register.simple_tag(profile_charts, name='profile_charts')
