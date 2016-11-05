# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
from pybrasil.valor.decimal import Decimal as D
import tools


MESES = (
    ('01', u'janeiro'),
    ('02', u'fevereiro'),
    ('03', u'março'),
    ('04', u'abril'),
    ('05', u'maio'),
    ('06', u'junho'),
    ('07', u'julho'),
    ('08', u'agosto'),
    ('09', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)


class finan_lancamento_fluxo_caixa(osv.Model):    
    _name = 'finan.lancamento.fluxo.caixa'
    _inherit = 'finan.lancamento'
    _description = u'Lançamento financeiro - Fluxo de Caixa'
    _auto = False
    
    _columns = {
        'valor_extrato_saldo': fields.float(u'Saldo'),
        'valor_extrato_debito': fields.float(u'Débito'),
        'valor_extrato_credito': fields.float(u'Crédito'),
        
        'data_vencimento_ano': fields.char(u'Ano de vencimento', size=4),
        'data_vencimento_mes': fields.selection(MESES, u'Mês de vencimento'),
        'data_vencimento_dia': fields.char(u'Dia de vencimento', size=10),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'finan_lancamento_fluxo_caixa')
        cr.execute("""
            create or replace view finan_lancamento_fluxo_caixa as (
                select 
                    *,
                    case
                        when tipo in ('P', 'S', 'PP', 'LP') then coalesce(valor_saldo, 0)
                        else 0
                    end as valor_extrato_debito,
                    case
                        when tipo in ('P', 'S', 'PP', 'LP') then 0
                        else coalesce(valor_saldo, 0)
                    end as valor_extrato_credito,
                    case
                        when tipo in ('P', 'S', 'PP', 'LP') then coalesce(valor_saldo, 0) * -1
                        else coalesce(valor_saldo, 0)
                    end as valor_extrato_saldo,
                    
                    to_char(data_vencimento, 'YYYY') as data_vencimento_ano,
                    to_char(data_vencimento, 'MM') as data_vencimento_mes,
                    to_char(data_vencimento, 'YYYY-MM-DD') as data_vencimento_dia

                from 
                    finan_lancamento
                
                where
                    tipo != 'T'
            );""")
    
    


finan_lancamento_fluxo_caixa()
