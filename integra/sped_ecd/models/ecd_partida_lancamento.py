# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


TIPO_PARTIDA = [
    ('D', u'Débito'),
    ('C', u'Crédito'),
]

STORE_COMPANY = {
    'ecd.lancamento.contabil': (
        lambda lanc_pool, cr, uid, ids, context={}: lanc_pool.pool.get('ecd.partida.lancamento').search(cr, uid, [['lancamento_id', 'in', ids]]),
        ['company_id', 'cnpj_cpf','data', 'plano_id'],
        20  #  Prioridade
    )
}


class ecd_partida_lancamento(osv.Model):
    _description = u'ECD Partidas do Lançamento'
    _name = 'ecd.partida.lancamento'
    _rec_name = 'codigo'
    _order = 'id'


    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = lancamento_obj.id

        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'tipo': fields.selection(TIPO_PARTIDA,u'Tipo'),
        'numero_documento': fields.char(u'Nº Doc.', size=60),
        'lancamento_id': fields.many2one('ecd.lancamento.contabil', u'Lançamento', ondelete='cascade'),
        'finan_lancamento_id': fields.related('lancamento_id', 'finan_lancamento_id', type='many2one', relation='finan.lancamento', string=u'Lançamento financeiro'),
        'sped_documento_id': fields.related('lancamento_id', 'sped_documento_id', type='many2one', relation='sped.documento', string=u'Documento fiscal'),
        'lote_id': fields.related('lancamento_id', 'lote_id', type='many2one', relation='lote.contabilidade', string=u'Lote', store=True),
        'data': fields.related('lancamento_id', 'data', type='date', string=u'Data', store=STORE_COMPANY),
        'plano_id': fields.related('lancamento_id', 'plano_id', type='many2one', string=u'Plano de contas', relation='ecd.plano.conta', store=STORE_COMPANY),
        'company_id': fields.related('lancamento_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=STORE_COMPANY),
        'cnpj_cpf': fields.related('lancamento_id', 'cnpj_cpf', type='char', string=u'Cnpj', store=STORE_COMPANY),
        'conta_id': fields.many2one('finan.conta', u'Conta Contábil', ondelete='restrict'),
        'contra_partida_id': fields.many2one('finan.conta', u'Contra Partida', ondelete='restrict'),
        'tipo_conta': fields.related('conta_id', 'tipo', type='char', string=u'Tipo conta'),
        'centrocusto_id': fields.many2one('finan.centrocusto',u'Centro Custo', ondelete='restrict'),
        'vr_debito': fields.float(u'Débito'),
        'vr_credito': fields.float(u'Crédito'),
        'historico_id': fields.many2one('finan.historico',u'Cód.Hist', ondelete='restrict'),
        'historico': fields.text(u'Histórico', size=6000),
        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
        'plano_id': fields.many2one('ecd.plano.conta', u'Plano de Conta', ondelete='restrict'),
        'nao_excluir': fields.boolean(u'Não excluir'),
        'saldo_inicial': fields.boolean(u'Saldo Inicial'),
        'saldo_inicial_cnpj': fields.char(u'Saldo Inicial CNPJ', size=18),

        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data de'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data até'),

        'valor_de': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'De valor'),
        'valor_ate': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'A valor'),
    }

    _defaults = {
        'vr_debito': D(0),
        'vr_credito': D(0),
        'saldo_inicial': False,
    }

    _sql_constraints = [
        ('saldo_inicial_cnpj_conta_id_saldo_inicial_unique', 'unique(saldo_inicial_cnpj, conta_id, saldo_inicial)',u'O já existe saldo inicial para conta nesse CNPJ!')
    ]

    def tipo_conta(self, cr, uid, ids, conta_id, context={}):

        if not conta_id:
            return {}
        context['conta_simples'] = True
        res = {}
        valores = {}
        res['value'] = valores

        conta_pool = self.pool.get('finan.conta')
        conta_obj = conta_pool.browse(cr, uid, conta_id, context=context)
        self.verifica_conta_inativa(cr, uid , [ids], conta_id, context=context)
        valores['tipo_conta'] = conta_obj.tipo
        return res


    def verifica_conta_inativa(self, cr, uid, ids, conta_id, context={}):
        if not conta_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores
        conta_pool = self.pool.get('finan.conta')
        conta_obj = conta_pool.browse(cr, uid, conta_id, context=context )
        data = context.get('data', False)

        if conta_obj.inativa and data:
            if data > conta_obj.data_inativacao:
                valores['conta_id'] = ''
                raise osv.except_osv(u'ATENÇÃO!', u'Conta: {conta}, Inativa! '.format(conta=conta_obj.nome_simples))

        return res

    def debito_credito_block(self, cr, uid, ids, vr_debito, vr_credito, context={}):
        if not vr_debito and not vr_credito :
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        if vr_debito > 0:
            valores['vr_debito'] = vr_debito
            valores['vr_credito'] = 0
            valores['tipo'] = 'D'

        if vr_credito > 0:
            valores['vr_debito'] = 0
            valores['vr_credito'] = vr_credito
            valores['tipo'] = 'C'

        return res

    def get_historico(self, cr, uid, ids, historico_id, context={}):
        if not historico_id:
            return {}

        historico_pool = self.pool.get('finan.historico')
        historico_obj = historico_pool.browse(cr, uid, historico_id )
        res = {}
        valores = {}
        res['value'] = valores
        valores['historico'] = historico_obj.nome
        return res

    def unlink(self, cr, uid, ids, context={}):

        nao_excluir = context.get('nao_excluir')

        if nao_excluir:
            return {}
        else:
            return super(ecd_partida_lancamento, self).unlink(cr, uid, ids, context)



ecd_partida_lancamento()
