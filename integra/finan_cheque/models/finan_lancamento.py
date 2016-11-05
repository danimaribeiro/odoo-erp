# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from time import time
from mako.template import Template
from copy import copy
from pybrasil.valor.decimal import Decimal as D




class finan_lancamento(osv.Model):
    _description = u'Lançamentos'
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'cheque_id': fields.many2one('finan.cheque', u'Cheque', ondelete='restrict'),
        'cheque_receber_ids': fields.one2many('finan.cheque', 'receber_id', u'Cheques'),
        'cheque_pagar_ids': fields.many2many('finan.cheque','finan_cheques_itens', 'lancamento_id', 'cheque_id', string='Cheque', ondelete='cascade'),
        'data_quitacao_cheque': fields.date(u'Data de quitação', select=True),
        'cheque_deposito_id': fields.many2one('finan.cheque.deposito', u'Depósito de cheque', ondelete='cascade'),
    }

    _defaults = {
        'data_quitacao_cheque': fields.date.today,
    }

    def quitar_titulo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        lancamento_pool = self.pool.get('finan.lancamento')

        if isinstance(ids, list):
            id = ids[0]

        lancamento_obj = lancamento_pool.browse(cr, uid, id)

        if lancamento_obj.tipo == 'R' and len(lancamento_obj.cheque_receber_ids) == 0:
            raise osv.except_osv(u'Aviso!', u'Não existem cheques vinculados ao lançamento!')
        elif lancamento_obj.tipo == 'P' and len(lancamento_obj.cheque_pagar_ids) == 0:
            raise osv.except_osv(u'Aviso!', u'Não existem cheques vinculados ao lançamento!')

        formapagamento_id = self._cria_formapagamento_id(cr, uid, nome='CHEQUE')
        documento_id = self._cria_documento_id(cr, uid, nome='CHEQUE')

        if lancamento_obj.tipo == 'R':
            tipo = 'PR'
        else:
            tipo = 'PP'

        dados_quitacao = {
            'lancamento_id': lancamento_obj.id,
            'company_id': lancamento_obj.company_id.id,
            'formapagamento_id': formapagamento_id,
            'documento_id': documento_id,
            'tipo': tipo,
            'data_quitacao': lancamento_obj.data_quitacao_cheque,
        }

        if lancamento_obj.tipo == 'R':
            for cheque_obj in lancamento_obj.cheque_receber_ids:
                jah_existe = lancamento_pool.search(cr, uid, [('tipo', '=', tipo), ('lancamento_id', '=', lancamento_obj.id), ('cheque_id', '=', cheque_obj.id)])

                #
                # Se já foi lançada a quitação, ignora o cheque
                #
                if len(jah_existe) > 0:
                    continue

                dados = {}
                dados.update(dados_quitacao)
                dados['data_documento'] = cheque_obj.data_recebimento
                dados['data_quitacao'] = cheque_obj.data_recebimento
                dados['valor_documento'] = cheque_obj.valor
                dados['valor'] = cheque_obj.valor
                dados['res_partner_bank_id'] = cheque_obj.res_partner_bank_id.id
                dados['numero_documento'] = 'CHQR-' + cheque_obj.numero_cheque
                dados['situacao'] = 'Quitado'
                dados['cheque_id'] = cheque_obj.id
                pagamento_id = lancamento_pool.create(cr, uid, dados)

        else:
            for cheque_obj in lancamento_obj.cheque_pagar_ids:
                jah_existe = lancamento_pool.search(cr, uid, [('tipo', '=', tipo), ('lancamento_id', '=', lancamento_obj.id), ('cheque_id', '=', cheque_obj.id)])

                #
                # Se já foi lançada a quitação, ignora o cheque
                #
                if len(jah_existe) > 0:
                    continue

                dados = {}
                dados.update(dados_quitacao)
                dados['data_documento'] = lancamento_obj.data_quitacao_cheque
                dados['data_quitacao'] = lancamento_obj.data_quitacao_cheque
                dados['valor_documento'] = cheque_obj.valor
                dados['valor'] = cheque_obj.valor
                dados['res_partner_bank_id'] = cheque_obj.res_partner_bank_id.id
                dados['numero_documento'] = 'CHQP-' + cheque_obj.numero_cheque
                dados['situacao'] = 'Quitado'
                dados['cheque_id'] = cheque_obj.id
                pagamento_id = lancamento_pool.create(cr, uid, dados)

                cheque_obj.write({'situacao': 'RP'})

        return True

    def _cria_formapagamento_id(self, cr, uid, nome):
        forma_pool = self.pool.get('finan.formapagamento')
        forma_ids = forma_pool.search(cr, uid, [('nome', 'in', [nome.lower(), nome.upper()])])

        if forma_ids:
            return forma_ids[0]

        dados = {
            'nome': nome.upper(),
        }
        forma_id = forma_pool.create(cr, uid, dados)

        return forma_id

    def _cria_documento_id(self, cr, uid, nome):
        documento_pool = self.pool.get('finan.documento')
        documento_ids = documento_pool.search(cr, uid, [('nome', 'in', [nome.lower(), nome.upper()])])

        if documento_ids:
            return documento_ids[0]

        dados = {
            'nome': nome.upper(),
        }
        documento_id = documento_pool.create(cr, uid, dados)

        return documento_id

finan_lancamento()
