# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
from sql_finan_saldo import SQL_VIEW_GERAL


class finan_views(osv.Model):
    _description = u'Financeiro - Views no banco'
    _name = 'finan.views'
    _sql = SQL_VIEW_GERAL
    _auto = False


    _columns = {
        'data': fields.date(u'Data'),
    }


finan_views()
