# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.models.trata_nfse import monta_nfse, grava_arquivo, grava_pdf_recibo_locacao
from pybrasil.valor.decimal import Decimal as D
from sped.constante_tributaria import *
from string import upper


class sped_documento(osv.Model):
    _description = 'Documentos SPED'
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'finan_devolucao_id': fields.many2one('finan.lancamento', string=u'Devolução')
    }

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        lancamento_pool = self.pool.get('finan.lancamento')
        bank_pool = self.pool.get('res.partner.bank')

        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.finalidade_nfe == FINALIDADE_NFE_DEVOLUCAO:
                if not doc_obj.res_partner_bank_id:
                    raise osv.except_osv(u'Erro!', u'O campo Conta bancária para depósito é Obrigatório!')

                bank_ids = bank_pool.search(cr, uid, [('state', 'in', ('DEVOLUCAO','devolucao', 'Devolucao'))])

                if not len(bank_ids):
                    raise osv.except_osv(u'Erro!', u'Não há uma conta de devolução configurada no financeiro!')

                dados = {
                    'company_id': doc_obj.company_id.id,
                    'tipo': 'T',
                    'provisionado': False,
                    'conta_id': doc_obj.finan_conta_id.id,
                    'documento_id': doc_obj.finan_documento_id.id,
                    'partner_id': doc_obj.partner_id.id,
                    'data_documento': doc_obj.data_entrada_saida_brasilia,
                    'sped_documento_id': doc_obj.id,
                    'res_partner_bank_id': bank_ids[0],
                }

                if doc_obj.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                    dados['tipo'] = 'S'  # A conta devolução fica devedora
                else:
                    dados['tipo'] = 'E'  # A conta devolução fica credora

                if doc_obj.finan_centrocusto_id:
                    dados['centrocusto_id'] = doc_obj.finan_centrocusto_id.id

                if doc_obj.finan_carteira_id:
                    dados['carteira_id'] = doc_obj.finan_carteira_id.id

                numero_documento = doc_obj.serie or 'SS'
                numero_documento += '-'
                numero_documento += str(doc_obj.numero)
                dados['numero_documento'] = numero_documento
                dados['valor_documento'] = doc_obj.vr_fatura
                dados['valor'] = doc_obj.vr_fatura
                dados['data_quitacao'] = doc_obj.data_entrada_saida_brasilia
                dados['data'] = doc_obj.data_entrada_saida_brasilia

                lanc_id = lancamento_pool.create(cr, uid, dados)

                sql = """
                update sped_documento set finan_devolucao_id = {lancamento_id}
                where id = {sped_id}
                """
                sql = sql.format(lancamento_id=lanc_id, sped_id=doc_obj.id)
                cr.execute(sql)

        return res

    def unlink(self, cr, uid, ids, context={}):
        lanc_pool = self.pool.get('finan.lancamento')
        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.finan_devolucao_id:
                lanc_obj = lanc_pool.browse(cr, uid, doc_obj.finan_devolucao_id.id)
                lanc_obj.unlink()

        return super(sped_documento, self).unlink(cr, uid, ids)


sped_documento()
