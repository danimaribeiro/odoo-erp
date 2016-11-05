# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import ENTRADA_SAIDA, ENTRADA_SAIDA_SAIDA


class sped_cfop(osv.Model):
    _description = 'CFOP'
    _name = 'sped.cfop'
    _order = 'codigo'
    _rec_name = 'nome'

    def monta_nome(self, cr, uid, id):
        cfop_obj = self.browse(cr, uid, id)

        nome = cfop_obj.codigo
        nome += ' - ' + cfop_obj.descricao

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res.append((id, self.monta_nome(cr, uid, id)))

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.nome_get(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('codigo', '>=', texto),
            ('descricao', 'ilike', texto)
        ]

        return procura

    _columns = {
        'codigo': fields.char(u'Código', size=4, select=True),
        'descricao': fields.char(u'Descrição', size=512, select=True),
        'entrada_saida': fields.selection(ENTRADA_SAIDA, u'Entrada/saída'),
        'dentro_estado': fields.boolean(u'Dentro do estado?'),
        'fora_estado': fields.boolean(u'Para fora do estado?'),
        'fora_pais': fields.boolean(u'Para fora do país?'),
        'gera_pis_cofins': fields.boolean(u'Gera crédito de PIS-COFINS (entrada)/paga PIS-COFINS (saída)?'),
        'natureza_bc_credito_pis_cofins': fields.char(u'Natureza da BC do crédito de PIS-COFINS', size=2),
        'gera_ipi': fields.boolean(u'Gera crédito de IPI (entrada)/paga IPI (saída)?'),
        'gera_icms_proprio': fields.boolean(u'Gera crédito de ICMS próprio (entrada)/paga ICMS próprio (saída)?'),
        'gera_icms_st': fields.boolean(u'Gera crédito de ICMS ST (entrada)/paga ICMS ST (saída)?'),
        'gera_icms_sn': fields.boolean(u'Dá direito a crédito de ICMS SIMPLES (saída)?'),
        'cfop_dentro_estado_id': fields.many2one('sped.cfop', u'CFOP equivalente dentro do estado'),
        'cfop_fora_estado_id': fields.many2one('sped.cfop', u'CFOP equivalente para fora do estado'),
        'cfop_fora_pais_id': fields.many2one('sped.cfop', u'CFOP equivalente para fora do país'),
        'movimentacao_fisica': fields.boolean(u'Há movimentação física do produto?'),
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome),
        'cfop_entrada_id': fields.many2one('sped.cfop', u'CFOP padrão para entrada'),
    }

    _defaults = {
        'entrada_saida': ENTRADA_SAIDA_SAIDA,
        'dentro_estado': False,
        'fora_estado': False,
        'fora_pais': False,
        'gera_pis_cofins': False,
        'natureza_bc_credito_pis_cofins': '',
        'gera_ipi': False,
        'gera_icms_proprio': False,
        'gera_icms_st': False,
        'gera_icms_sn': False,
        'movimentacao_fisica': False,
    }

    _sql_constraints = [
        ('codigo_unique', 'unique (codigo)', u'O código não pode se repetir!'),
    ]


sped_cfop()
