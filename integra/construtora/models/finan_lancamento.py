# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_lancamento(osv.Model):
    _inherit = 'finan.lancamento'

    _columns = {
        'parcela_comissao_id': fields.many2one('finan.contrato.comissao', u'Parcela Comissao', ondelete='cascade'),
        'contrato_imovel_id': fields.many2one('finan.contrato', u'Contrato de Imovel', ondelete='cascade'),

        'lancamento_recebimento_imovel_id': fields.many2one('finan.lancamento', u'Venda Imóvel Receber', ondelete='restrict'),

        'finan_contrato_condicao_id': fields.many2one('finan.contrato.condicao', u'Condição de pagamento', ondelete='cascade'),
        'finan_contrato_condicao_renegociacao_id': fields.many2one('finan.contrato.condicao', u'Renegociação de pagamento', ondelete='cascade'),

        'finan_contrato_condicao_parcela_id': fields.many2one('finan.contrato.condicao.parcela', u'Parcela do contrato', ondelete='cascade'),

        'finan_contrato_condicao_parcela_valor': fields.related('finan_contrato_condicao_parcela_id', 'valor', type='float', string=u'Valor'),
        'finan_contrato_condicao_parcela_valor_seguro': fields.related('finan_contrato_condicao_parcela_id', 'valor_seguro', type='float', string=u'Seguro'),
        'finan_contrato_condicao_parcela_valor_administracao': fields.related('finan_contrato_condicao_parcela_id', 'valor_administracao', type='float', string=u'Adm.'),
        'finan_contrato_condicao_parcela_valor_original': fields.related('finan_contrato_condicao_parcela_id', 'valor_original', type='float', string=u'Valor original'),
        'finan_contrato_condicao_parcela_valor_capital': fields.related('finan_contrato_condicao_parcela_id', 'valor_capital', type='float', string=u'Capital'),
        'finan_contrato_condicao_parcela_valor_capital_juros': fields.related('finan_contrato_condicao_parcela_id', 'valor_capital_juros', type='float', string=u'Capital + Juros'),
        'finan_contrato_condicao_parcela_valor_capital_juros_correcao': fields.related('finan_contrato_condicao_parcela_id', 'valor_capital_juros_correcao', type='float', string=u'Capital + Juros + Correção'),
        'finan_contrato_condicao_parcela_juros': fields.related('finan_contrato_condicao_parcela_id', 'juros', type='float', string=u'Juros'),
        'finan_contrato_condicao_parcela_correcao': fields.related('finan_contrato_condicao_parcela_id', 'correcao', type='float', string=u'Correção'),
        'finan_contrato_condicao_parcela_amortizacao': fields.related('finan_contrato_condicao_parcela_id', 'amortizacao', type='float', string=u'Amortização'),
        'finan_contrato_condicao_parcela_divida_amortizada': fields.related('finan_contrato_condicao_parcela_id', 'divida_amortizada', type='float', string=u'Dívida amortizada'),
        'finan_contrato_condicao_parcela_saldo_devedor': fields.related('finan_contrato_condicao_parcela_id', 'saldo_devedor', type='float', string=u'Saldo devedor'),
    }

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_lancamento, self).write(cr, uid, ids, dados, context=context)

        saldo_pool =  self.pool.get('finan.saldo')
        saldo_pool.cria_fechamentos_gerais(cr, uid, ids, context)

        return res


finan_lancamento()


class finan_lancamento_rateio(osv.Model):
    _inherit = 'finan.lancamento.rateio'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto/empreendimento', select=True, ondelete='restrict'),
        'project_orcamento_item_id': fields.many2one('project.orcamento.item', u'Item do orçamento', ondelete='restrict'),
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', select=True, ondelete='restrict'),
    }


finan_lancamento_rateio()
