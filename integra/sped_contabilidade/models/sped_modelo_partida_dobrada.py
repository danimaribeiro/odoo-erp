# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor


TABELA = (
    ('DF', u'Documento Fiscal'),
    ('PR', u'Lançamento financeiro'),
    ('PP', u'Lançamento financeiro'),
    ('FP', u'Folha de Pagamento'),
    #('E', u'Transação de Entrada'),
    #('S', u'Transação de Saída'),
    #('T', u'Transferência'),
)


CAMPO = [
    ('vr_cofins_proprio', u'COFINS própria'),
    ('vr_cofins_retido', u'COFINS retida'),
    ('vr_cofins_st', u'COFINS ST'),
    ('vr_icms_sn', u'Crédito de ICMS - SIMPLES Nacional'),
    ('vr_csll_propria', u'CSLL própria'),
    ('vr_csll', u'CSLL retida'),
    ('vr_custo', u'Custo (nas entradas/compras)'),
    ('vr_desconto_rateio', u'Desconto (rateio do custo)'),
    ('vr_desconto', u'Desconto'),
    ('vr_diferencial_aliquota', u'Diferencial de alíquota (ICMS próprio)'),
    ('vr_diferencial_aliquota_st', u'Diferencial de alíquota (ICMS ST)'),
    ('vr_frete_rateio', u'Frete (rateio do custo)'),
    ('vr_frete', u'Frete'),
    ('vr_icms_proprio', u'ICMS próprio'),
    ('vr_icms_st_retido', u'ICMS retido anteriormente por substituição tributária'),
    ('vr_icms_frete', u'ICMS retido sobre o frete'),
    ('vr_icms_st_compra', u'ICMS ST (recalculado na compra)'),
    ('vr_icms_st', u'ICMS ST'),
    ('vr_ii', u'Imposto de importação'),
    ('vr_previdencia', u'INSS retido'),
    ('vr_ipi', u'IPI'),
    ('vr_irpj_proprio', u'IRPJ próprio'),
    ('vr_irrf', u'IRRF retido'),
    ('vr_iss', u'ISS próprio'),
    ('vr_iss_retido', u'ISS retido'),
    ('vr_outras_rateio', u'Outras despesas acessórias (rateio do custo)'),
    ('vr_outras', u'Outras despesas acessórias'),
    ('vr_pis_proprio', u'PIS próprio'),
    ('vr_pis_retido', u'PIS retido'),
    ('vr_pis_st', u'PIS ST'),
    ('vr_seguro_rateio', u'Seguro (rateio do custo)'),
    ('vr_seguro', u'Seguro'),
    ('vr_servico_frete', u'Serviço do frete'),
    ('vr_fatura', u'Total da fatura'),
    ('vr_nf', u'Total da NF'),
    ('vr_operacao_tributacao', u'Valor da operação para tributação'),
    ('vr_operacao', u'Valor da operação'),
    ('vr_produtos_tributacao', u'Valor dos produtos para tributação'),
    ('vr_produtos', u'Valor dos produtos/serviços'),
    ('vr_servicos', u'Valor dos serviços'),
    ('vr_custo_estoque', u'Valor Custo Produto Estoque'),
]


CAMPO_CONTABILIZA_ITEM = (
    'vr_cofins_proprio',
    #'vr_cofins_retido',
    #'vr_cofins_st',
    'vr_icms_sn',
    #'vr_csll_propria',
    #'vr_csll',
    'vr_custo',
    'vr_desconto_rateio',
    'vr_desconto',
    'vr_diferencial_aliquota',
    'vr_diferencial_aliquota_st',
    'vr_frete_rateio',
    'vr_frete',
    'vr_icms_proprio',
    'vr_icms_st_retido',
    #'vr_icms_frete',
    'vr_icms_st_compra',
    'vr_icms_st',
    'vr_ii',
    #'vr_previdencia',
    'vr_ipi',
    #'vr_irpj_proprio',
    #'vr_irrf',
    #'vr_iss',
    #'vr_iss_retido',
    'vr_outras_rateio',
    'vr_outras',
    'vr_pis_proprio',
    #'vr_pis_retido',
    #'vr_pis_st',
    'vr_seguro_rateio',
    'vr_seguro',
    #'vr_servico_frete',
    #'vr_fatura',
    #'vr_nf',
    #'vr_operacao_tributacao',
    'vr_operacao',
    #'vr_produtos_tributacao',
    #'vr_produtos',
    #'vr_servicos',
    'vr_custo_estoque',
)


CAMPO_FINANCEIRO = [
    ('valor', u'Valor pago/recebido'),
    ('valor_documento', u'Valor do documento'),
    ('valor_juros', u'Juros'),
    ('valor_multa', u'Multa'),
    ('valor_multa', u'Taxas'),
    ('valor_desconto', u'Desconto'),    
    ('outros_acrescimos', u'Outros acréscimos'),
    #('outros_debitos', u'Outros débitos'),
]


class sped_modelo_partida_dobrada(osv.Model):
    _description = 'Modelo Partida Dobrada'
    _name = 'sped.modelo_partida_dobrada'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Descrição', size=60, select=True),
        'tabela': fields.selection(TABELA, string='Tabela', required=True),
        'item_ids': fields.one2many('sped.modelo_partida_dobrada.item','modelo_id', u'Item Modelo de Parametrização', domain=[('tipo', '=', 'A')]),
        'operacao_fiscal_ids': fields.one2many('sped.operacao', 'modelo_partida_dobrada_id', u'Operações Fiscais'),
        'modelo': fields.selection(MODELO_FISCAL, u'Modelo fiscal', select=True),
        'item_duplicata_ids': fields.one2many('sped.modelo_partida_dobrada.item','modelo_id', u'Item Modelo de Parametrização', domain=[('tipo', '=', 'B')]),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),     
    }

    def copy(self, cr, uid, id, default={}, context={}):
        if not id:
            return False

        original_obj = self.browse(cr, uid, id)

        default['nome'] = original_obj.nome + u' (cópia)'
        default['item_duplicata_ids'] = False
        default['operacao_fiscal_ids'] = False
        default['modelo'] = False

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res


sped_modelo_partida_dobrada()


class sped_modelo_partida_dobrada_item(osv.Model):
    _description = 'Item Modelo Partida Dobrada'
    _name = 'sped.modelo_partida_dobrada.item'

    _columns = {
      'modelo_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Parametrização'),
      'tabela': fields.related('modelo_id', 'tabela', type='char', relation='sped.modelo_partida_dobrada', selection=TABELA, string=u'Tabela', store=True),
      'tipo': fields.selection([('A', u'Nota/liquidação'), ('B', u'Duplicatas')], u'Tipo', select=True),
      'campo_nota': fields.selection(CAMPO, u'Campo do documento fiscal'),
      'campo_financeiro': fields.selection(CAMPO_FINANCEIRO, u'Campo do financeiro'),
      'conta_debito_id': fields.many2one('finan.conta', u'Conta Débito'),
      'conta_credito_id': fields.many2one('finan.conta', u'Conta Crédito'),
      #'cod_historico': fields.char(u'Cód. histórico', size=5),
      'historico_id': fields.many2one('finan.historico', u'Histórico'),
    }

    _defaults = {
        'tipo': 'A',
    }


sped_modelo_partida_dobrada_item()


class PartidaDobrada(object):
    def __init__(self):
        self.data = None
        self.conta_debito_id = None
        self.conta_credito_id = None
        self.valor = D(0)
        self.numero_documento = ''
        self.codigo_historico = ''
        self.historico = ''
        self.cnpj = ''
        self.centrocusto_id = None
        self.sem_partida = False
        self.rule_id = None

    def __str__(self):
        txt = 'Partida dobrada: '
        if self.conta_debito_id:
            txt += u'D-' + self.conta_debito_id.codigo_completo
        else:
            txt += u'D-[não configurado]'

        txt += ', '

        if self.conta_credito_id:
            txt += u'C-' + self.conta_credito_id.codigo_completo
        else:
            txt += u'C-[não configurado]'

        txt += u', R$ ' + formata_valor(self.valor)

        return txt
