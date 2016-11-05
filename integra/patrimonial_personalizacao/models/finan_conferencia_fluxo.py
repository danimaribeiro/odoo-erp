# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv

SQL_CONFERENCIA_FLUXO = """
DROP VIEW IF EXISTS finan_conferencia_fluxo;

CREATE OR REPLACE VIEW finan_conferencia_fluxo AS
select
    row_number() over() as id,
    f.data,
    fl.company_id,
    c.parent_id as grupo_id,
    fl.partner_id,
    f.conta_id,
    fl.centrocusto_id,
    f.res_partner_bank_id,
    fl.tipo,
    fl.numero_documento,
    fl.documento_id,
    coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1)  as valor_entrada,
    coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1)  as valor_saida,
    coalesce(f.valor_entrada, 0) * coalesce(ldp.porcentagem, 1) - coalesce(f.valor_saida, 0) * coalesce(ldp.porcentagem, 1) as diferenca

from
    finan_fluxo_mensal_diario f

    left join finan_lancamento_lote_divida_pagamento ldp on ldp.lote_id = f.lancamento_id
    join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = f.lancamento_id)
    join res_company c on c.id = fl.company_id


where
    f.tipo = 'Q';
"""

class finan_conferencia_fluxo(orm.Model):
    _name = 'finan.conferencia.fluxo'
    _description = u'Conferência de fluxo de caixa'
    _sql = SQL_CONFERENCIA_FLUXO
    _auto = False
    _order = 'data desc, valor_entrada, valor_saida'

    _columns = {
        'data': fields.date(u'Data'),
        'company_id': fields.many2one('res.company', u'Empresa/unidade'),
        'grupo_id': fields.many2one('res.company', u'Grupo'),
        'partner_id': fields.many2one('res.partner', u'Cliente/Fornecedor'),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
        'documento_id': fields.many2one('finan.documento', u'Documento'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'numero_documento': fields.char(u'Número do documento', size=30),
        'valor_entrada': fields.float(u'Valor de entrada'),
        'valor_saida': fields.float(u'Valor de saída'),
        'diferenca': fields.float(u'Diferença'),

        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De data'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A data'),
    }

    def create(self, cr, uid, dados, context={}):
        pass

    def write(self, cr, uid, ids, dados, context={}):
        pass

    def unlink(self, cr, uid, ids, context={}):
        pass


finan_conferencia_fluxo()
