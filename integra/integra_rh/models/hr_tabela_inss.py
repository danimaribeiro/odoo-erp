# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_tabela_inss(orm.Model):
    _name = 'hr.tabela.inss'
    _description = u'Tabela de Salário Familia'
    _rec_name = 'ano'
    _order = 'ano desc, teto desc'

    _columns = {
        'ano': fields.integer(u'Ano'),
        'teto': fields.float(u'Teto'),
        'aliquota': fields.float(u'Alíquota'),
        #'valor': fields.float(u'Valor'),
    }


hr_tabela_inss()
