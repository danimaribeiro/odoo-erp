# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_tabela_salario_familia(orm.Model):
    _name = 'hr.tabela.salario.familia'
    _description = u'Tabela de Salário Familia'
    _rec_name = 'ano'
    _order = 'ano desc, teto'
       

    _columns = {
        'ano': fields.integer(u'Ano'),
        'teto': fields.float('Teto'),
        'valor': fields.float('Valor'),
    }


hr_tabela_salario_familia()
