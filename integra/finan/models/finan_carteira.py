# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class finan_carteira(orm.Model):
    _name = 'finan.carteira'
    _description = 'Carteira de cobrança'

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return {}

        res = []
        for id in ids:
            carteira_obj = self.browse(cr, 1, id)
            if carteira_obj.res_partner_bank_id:
                texto = carteira_obj.res_partner_bank_id.nome or ''
            else:
                texto = ''

            texto += ' - ' + carteira_obj.carteira or ''

            if carteira_obj.modalidade:
                texto += '-' + carteira_obj.modalidade

            res += [(id, texto)]

        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('res_partner_bank_id', 'ilike', texto),
            ('carteira', 'ilike', texto),
        ]

        return procura

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.cnpj_cpf:
                res[obj.id] = obj.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    def _procura_raiz_cnpj(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('res_partner_bank_id.partner_id.raiz_cnpj', '=', texto)
        ]

        return procura

    _columns = {
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', fnct_search=_procura_nome, store=True),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária', required=True, select=True),
        'carteira': fields.char(u'Carteira', size=10, required=True, select=True),
        'modalidade': fields.char(u'Modalidade', size=10),
        'beneficiario': fields.char(u'Código do beneficiário', size=20),
        'beneficiario_digito': fields.char(u'Beneficiário - dígito', size=1),
        'ultimo_nosso_numero': fields.char(u'Último nosso número', size=20),
        'ultimo_arquivo_remessa': fields.integer(u'Último arquivo de remessa'),
        'porcentagem_juros': fields.float(u'% de Juros por dia', digits=(18,8)),
        'porcentagem_multa': fields.float(u'% de Multa por atraso', digits=(5,2)),
        'dias_protesto': fields.integer(u'Dias para protesto'),
        'partner_id': fields.related('res_partner_bank_id', 'partner_id', type='many2one', string=u'Titular', relation='res.partner', store=True),
        #'cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', string=u'CNPJ/CPF', store=True),
        #'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True, fnct_search=_procura_raiz_cnpj),
        'nosso_numero_pelo_banco': fields.boolean(u'Nosso número gerado pelo banco?'),
        'taxa_boleto': fields.float(u'Taxa geração de boleto', digits=(18,2)),
        'cnpj_cpf': fields.related('res_partner_bank_id', 'cnpj_cpf', type='char', string=u'CNPJ/CPF', store=True, select=True),
        'raiz_cnpj': fields.related('res_partner_bank_id', 'raiz_cnpj', type='char', string=u'Raiz do CNPJ', store=True, select=True),
        'instrucao': fields.text(u'Instrução livre'),
    }

    #
    # O valor do juros dia foi calculado com a seguinte fórmula, onde:
    # tm = taxa mensal = 1%
    # pm = periodo = 1 mês
    # pi = período de incidência = 1/30 (1 dia)
    # td = taxa diária = (((1 + tm) ** (pi / pm)) - 1) * 100
    # td = (((1 + 0.01) ** ((1.0 / 30.0) / 1)) - 1) * 100
    #

    defaults = {
        'porcentagem_juros': (((1 + 0.01) ** ((1.0 / 30.0) / 1)) - 1) * 100,
        'porcentagem_multa': 2,
        'nosso_numero_pelo_banco': False,
    }

    _order = 'res_partner_bank_id, carteira, modalidade'
    _rec_name = 'nome'


finan_carteira()
