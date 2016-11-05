# -*- encoding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields


class patrimonio_setor(osv.Model):
    _name = 'patrimonio.setor'
    _rec_name = 'nome'
    _order = 'nome'


    _columns = {
        'nome': fields.char(u'Nome', size=30, select=True),
    }


patrimonio_setor()
