from django import template
from board.matrix import attack_matrix
register=template.Library()
register.simple_tag(attack_matrix,name='attack_matrix')
