# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_tabela_salario_minimo(orm.Model):
    _name = 'hr.tabela.salario.minimo'
    _description = u'Tabela de Salário Mínimo'
    _rec_name = 'ano'
    _order = 'ano desc'


    _columns = {
        'ano': fields.integer(u'Ano'),
        'valor': fields.float('Valor'),
    }


hr_tabela_salario_minimo()
