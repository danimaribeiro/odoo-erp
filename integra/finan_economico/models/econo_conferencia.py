# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


TIPO_LANCAMENTO = (
    ('R', u'A RECEBER'),
    ('P', u'A PAGAR'),
    ('T', u'TRANSFERÊNCIA'),
    ('E', u'ENTRADA'),
    ('S', u'SAÍDA'),
    ('PR', u'PAGAMENTO RECEBIDO'),
    ('PP', u'PAGAMENTO EFETUADO'),
    ('LR', u'LOTE RECEBIMENTO'),
    ('LP', u'LOTE PAGAMENTO'),
    ('AR', u'ADIANTAMENTO RECEBIDO'),
    ('AP', u'ADIANTAMENTO PAGO'),
)


class finan_rateio_economico_bi(orm.Model):
    _name = 'finan.rateio.economico.bi'
    _description = u'Conferência conta Econômica'
    #_auto = False

    _columns = {
        #
        # Controle serve para não trazer todos os dados na consulta de uma
        # vez só, quando se abre a tela
        #
        'controle': fields.boolean(u'Controle', select=True),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro'),
        'rateio_id': fields.many2one('finan.lancamento.rateio', u'Rateio financeiro'),
        'tipo': fields.selection(TIPO_LANCAMENTO, u'Tipo'),
        'data_quitacao': fields.date(u'Data de compensação', select=True),
        'company_id': fields.many2one('res.company', u'Unidade'),
        'grupo_id': fields.many2one('res.company', u'Grupo'),
        'conta_id': fields.many2one('finan.conta', u'Conta'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
        'hr_contract_id': fields.many2one('hr.contract', u'Funcionário'),
        'porcentagem': fields.float(u'Porcentagem'),
        'valor_documento': fields.float(u'Valor do documento'),
        'valor_desconto': fields.float(u'Desconto'),
        'valor_juros': fields.float(u'Juros'),
        'valor_multa': fields.float(u'Multa'),
        'valor_juros_multa': fields.float(u'Juros/Multa'),

        'valor_desconto_recebido': fields.float(u'Desconto'),
        'valor_juros_recebido': fields.float(u'Juros'),
        'valor_multa_recebido': fields.float(u'Multa'),
        'valor_juros_multa_recebido': fields.float(u'Juros/Multa'),

        'valor_desconto_pago': fields.float(u'Desconto'),
        'valor_juros_pago': fields.float(u'Juros'),
        'valor_multa_pago': fields.float(u'Multa'),
        'valor_juros_multa_pago': fields.float(u'Juros/Multa'),

        'valor': fields.float(u'Valor líquido'),
        'valor_usado': fields.float(u'Valor usado'),

        'econo_conta_id': fields.many2one('econo.conta', u'Conta econômica'),
        'repetido': fields.integer(u'Repetido?', select=True),
        'conta_individual_id': fields.many2one('finan.conta', u'Conta individual'),
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),

        'data_quitacao_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De quitacao'),
        'data_quitacao_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A quitacao'),
    }

    _default = {
        'controle': True,
    }

    def _conta_repetidos(self, cr, uid, ids, context={}):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for ecr_obj in self.browse(cr, uid, ids):

            if ecr_obj.rateio_id:
                sql = '''
                    update finan_rateio_economico_bi ecr set
                        repetido = (
                            select
                                count(ecr2.*)
                            from
                                finan_rateio_economico_bi ecr2
                            where
                                ecr2.rateio_id = {rateio_id}
                                and ecr2.valor = {valor}
                        )
                    where
                        ecr.rateio_id = {rateio_id}
                        and ecr.valor = {valor};
                '''
                sql = sql.format(rateio_id=ecr_obj.rateio_id.id, valor=ecr_obj.valor)
            else:
                sql = '''
                    update finan_rateio_economico_bi ecr set
                        repetido = (
                            select
                                count(ecr2.*)
                            from
                                finan_rateio_economico_bi ecr2
                            where
                                ecr2.lancamento_id = {lancamento_id}
                                and ecr2.valor = {valor}
                        )
                    where
                        ecr.lancamento_id = {lancamento_id}
                        and ecr.valor = {valor};
                '''
                sql = sql.format(lancamento_id=ecr_obj.lancamento_id.id, valor=ecr_obj.valor)

            cr.execute(sql)

    def create(self, cr, uid, dados, context={}):
        res = super(finan_rateio_economico_bi, self).create(cr, uid, dados, context=context)

        self._conta_repetidos(cr, uid, res, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_rateio_economico_bi, self).write(cr, uid, ids, dados, context=context)

        self._conta_repetidos(cr, uid, ids, context=context)

    def unlink(self, cr, uid, ids, context={}):
        res = super(finan_rateio_economico_bi, self).unlink(cr, uid, ids, context=context)

        self._conta_repetidos(cr, uid, ids, context=context)


finan_rateio_economico_bi()
