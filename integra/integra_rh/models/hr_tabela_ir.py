# -*- coding: utf-8 -*-


from osv import fields, orm
from hr_payslip_input import MESES



class hr_tabela_ir(orm.Model):
    _name = 'hr.tabela.ir'
    _description = u'Tabela de IR'
    _order = 'ano desc, mes desc, piso desc'

    _columns = {
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'piso': fields.float(u'Piso', select=True),
        'aliquota': fields.float(u'Alíquota'),
        'parcela_deduzir': fields.float(u'Parcela a Deduzir'),
    }

    _defaults = {
        'mes': '01',
    }


hr_tabela_ir()


class hr_tabela_ir_dependente(orm.Model):
    _name = 'hr.tabela.ir.dependente'
    _description = u'Tabela de IR de Dependente'
    _order = 'ano desc, mes'

    _columns = {
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'deducao_dependente': fields.float(u'Dedução dependente'),
    }

    _defaults = {
        'mes': '01',
    }


hr_tabela_ir_dependente()