# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from sped.constante_tributaria import *


class sped_documento(osv.Model):
    _inherit = 'sped.documento'

    _columns = {
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),
        'finan_lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do contrato', ondelete='restrict'),
    }

    def unlink(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False, 'valor_documento': doc_obj.finan_lancamento_id.contrato_id.valor_mensal})

        return super(sped_documento, self).unlink(cr, uid, ids, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        cancelando = False

        if 'situacao' in dados and dados['situacao'] in [SITUACAO_FISCAL_CANCELADO, SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO, SITUACAO_FISCAL_DENEGADO]:
            cancelando = True

        if 'state' in dados and dados['state'] in ['cancelada', 'denegada']:
            cancelando = True

        if cancelando:
            for doc_obj in self.browse(cr, uid, ids):
                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False, 'valor_documento': doc_obj.vr_nf, 'numero_documento': doc_obj.finan_lancamento_id.numero_documento_original})

        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        lancamento_pool = self.pool.get('finan.lancamento')

        for doc_id in ids:
            campos = self.pool.get('sped.documento').read(cr, uid, doc_id, ['finan_lancamento_id', 'vr_fatura', 'data_emissao_brasilia', 'serie', 'numero'])

            if campos['finan_lancamento_id']:
                lancamento_pool.write(cr, uid, [campos['finan_lancamento_id'][0]], {'valor_documento': campos['vr_fatura'], 'data_documento': campos['data_emissao_brasilia'], 'numero_documento': campos['serie'] + '-' + str(campos['numero']) })

        #
        # Se houver outros lançamentos vinculados a nota, que não seja o do
        # contrato, vamos excluir e manter apenas o do contrato
        #
        if 'finan_lancamento_id' in dados and 'finan_contrato_id' in dados:
            for nf_obj in self.browse(cr, uid, ids):
                if nf_obj.emissao != '0':
                    continue

                if dados['finan_lancamento_id']:
                    cr.execute('delete from finan_lancamento where contrato_id is null and sped_documento_id = ' + str(nf_obj.id) + ';')

                    #
                    # E agora, ativamos e vinculamos o documento fiscal ao lançamento do contrato
                    #
                    sql = """
                        update finan_lancamento set
                            provisionado = False,
                            sped_documento_id = """ + str(nf_obj.id) + """,
                            numero_documento = '""" + str(nf_obj.numero) + """'
                        where id = """ + str(dados['finan_lancamento_id']) + """;"""
                    cr.execute(sql)

        return res

    def onchange_finan_lancamento_id(self, cr, uid, ids, lancamento_id, vr_nf, context={}):
        res = {}
        valores = {
            'finan_contrato_id': False,
        }
        res['value'] = valores

        if not lancamento_id:
            return res

        lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id)

        valores['finan_contrato_id'] = lancamento_obj.contrato_id.id
        valores['finan_conta_id'] = lancamento_obj.conta_id.id
        valores['finan_documento_id'] = lancamento_obj.documento_id.id

        if lancamento_obj.centrocusto_id:
            valores['finan_centrocusto_id'] = lancamento_obj.centrocusto_id.id

        valores['duplicata_ids'] = [
            [5, False, False],
            [0, False, {
                'numero': '1',
                'data_vencimento': lancamento_obj.data_vencimento,
                'valor': vr_nf,
            }]
        ]

        return res


sped_documento()
