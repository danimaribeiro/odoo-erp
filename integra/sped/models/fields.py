# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import fields


class CampoDinheiro(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (18, 2)
        super(CampoDinheiro, self).__init__(*args, **kwargs)


class CampoPeso(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (18, 6)
        super(CampoPeso, self).__init__(*args, **kwargs)


class CampoPorcentagem(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (5, 2)
        super(CampoPorcentagem, self).__init__(*args, **kwargs)


class CampoQuantidade(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (18, 4)
        super(CampoQuantidade, self).__init__(*args, **kwargs)


class CampoValorUnitario(fields.float):
    def __init__(self, *args, **kwargs):
        kwargs['digits'] = (21, 10)
        super(CampoValorUnitario, self).__init__(*args, **kwargs)

