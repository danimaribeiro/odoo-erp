# -*- coding: utf-8 -*-

from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, formata_data


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'provisao_compra_ids': fields.one2many('sped.documento.provisao.compra','documento_id', u'Documento', required=True, ondelete='cascade', select=True),

    }

    def create(self, cr, uid, dados, context={}):

        self.verifica_valores_provisao(cr, uid, [], dados)

        res = super(sped_documento, self).create(cr, uid, dados, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):

        self.verifica_valores_provisao(cr, uid, ids, dados,context)

        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        return res

    def verifica_valores_provisao(self, cr, uid, ids, vals, context=None):
        if 'provisao_compra_ids' not in vals or not vals['provisao_compra_ids']:
            return

        provisao_pool = self.pool.get('sped.documento.provisao.compra')
        documento_pool = self.pool.get('sped.documento')

        provisao_compras = vals['provisao_compra_ids']
        provisao_compras_alteradas = []

        total_provisionado = D('0')
        total_atendido = D('0')
        total_nf = D('0')
        total_nf = D(vals.get('vr_nf', 0) or 0)

        for operacao, provisao_id, valores in provisao_compras:
            #
            # Cada lanc_item tem o seguinte formato
            # [operacao, id_original, valores_dos_campos]
            #
            # operacao pode ser:
            # 0 - criar novo registro (no caso aqui, vai ser ignorado)
            # 1 - alterar o registro
            # 2 - excluir o registro (também vai ser ignorado)
            # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
            # 4 - vincular a um registro existente
            # 5 - excluiu todos a vai incluir todos de novo

            print(operacao, 'operacao', provisao_id, valores)

            if operacao == 0:
                total_provisionado += D(valores.get('valor_provisionado', 0) or 0)
                total_atendido += D(valores.get('valor_atendido', 0) or 0)

                if total_atendido > total_provisionado:
                    raise osv.except_osv(u'Inválido !', u'Valor Atendido maior que valor provisionado!')


            if operacao == 5:
                excluido_ids = self.pool.get('sped.documento.provisao.compra').search(cr, uid, [('documento_id', 'in', ids)])
                provisao_compras_alteradas += excluido_ids

            if operacao == 2:
                provisao_compras_alteradas += [provisao_id]

            if operacao == 1 and ('valor_provisionado' in valores or 'valor_atendido' in valores):
                provisao_compras_alteradas += [provisao_id]

                for provisao_obj in provisao_pool.browse(cr, uid, [provisao_id]):

                    total_provisionado += D(valores.get('valor_provisionado', 0) or 0)
                    if  total_provisionado == 0:
                        total_provisionado = D(str(provisao_obj.valor_provisionado))

                    total_atendido += D(valores.get('valor_atendido', 0) or 0)
                    if  total_atendido == 0:
                        total_atendido = D(str(provisao_obj.valor_atendido))

                if total_atendido > total_provisionado:
                    raise osv.except_osv(u'Inválido !', u'Valor Atendido maior que valor provisionado!')


        #
        # Ajusta com os possíveis não alterados
        #

        provisao_ids = []
        if ids and ids[0]:

            documento_obj = documento_pool.browse(cr, uid, ids[0])
            total_nf += D(str(documento_obj.vr_nf))

            provisao_ids = provisao_pool.search(cr, uid, [('documento_id', '=', ids[0]), ('id', 'not in', provisao_compras_alteradas)])

            for provisao_obj in provisao_pool.browse(cr, uid, provisao_ids):
                total_provisionado += D(str(provisao_obj.valor_provisionado or 0))
                total_atendido += D(str(provisao_obj.valor_atendido or 0))

        total_provisionado = total_provisionado.quantize(D('0.01'))
        total_atendido = total_atendido.quantize(D('0.01'))
        if total_atendido > total_nf:
            raise osv.except_osv(u'Inválido !', u'Valor Atendido maior que valor da NF!')

    def cancela_provisao_pedido_compra(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            if not len(doc_obj.provisao_compra_ids):
                continue

            for provisao_obj in doc_obj.provisao_compra_ids:
                #
                # Lançamento já excluído?
                #
                if provisao_obj.salvo:
                    continue

                #
                # Não está consumindo toda a provisão, ajusta o valor provisionado
                #
                if provisao_obj.valor_atendido != provisao_obj.valor_provisionado:
                    self.pool.get('finan.lancamento').write(cr, uid, [provisao_obj.lancamento_id.id], {'valor_documento': D(provisao_obj.valor_provisionado or 0) - D(provisao_obj.valor_atendido or 0)})
                    provisao_obj.write({'salvo': True})

                #
                # Consumiu toda a provisão, excluir a provisão do financeiro
                #
                else:
                    self.pool.get('finan.lancamento').unlink(cr, uid, [provisao_obj.lancamento_id.id])
                    provisao_obj.write({'salvo': True})

    def onchange_finan_lancamento_id(self, cr, uid, ids, lancamento_id, vr_nf, context={}):
        res = {}
        valores = {
            'finan_contrato_id': False,
        }
        res['value'] = valores

        if not lancamento_id:
            return res

        lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id)

        if lancamento_obj.contrato_imovel_id:
            valores['finan_contrato_id'] = lancamento_obj.contrato_imovel_id.id
        else:
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
