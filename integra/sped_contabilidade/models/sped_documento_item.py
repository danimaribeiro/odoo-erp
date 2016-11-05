# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor import formata_valor
from pybrasil.valor.decimal import Decimal as D
from sped_modelo_partida_dobrada import PartidaDobrada, CAMPO_CONTABILIZA_ITEM
from copy import copy


class sped_documento_item(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
        'contabilizacao_ids': fields.one2many('sped.documento.contabilidade', 'documentoitem_id', u'Lançamentos contábeis'),
    }


    def get_partidas_dobradas_rateio(self, cr, uid, ids, item_partida_obj, valor, context={}):
        cc_pool = self.pool.get('finan.centrocusto')
        conta_pool = self.pool.get('finan.conta')
        campos = cc_pool.campos_rateio(cr, uid)

        res = []

        valor = D(valor)

        for item_obj in self.browse(cr, uid, ids):
            if not getattr(item_obj, item_partida_obj.campo_nota, False):
                continue

            #
            # Verifica o crédito nas notas de terceiro/entrada
            #
            if item_obj.documento_id.emissao == '1':
                if item_partida_obj.campo_nota == 'vr_icms_proprio' and not item_obj.credita_icms_proprio:
                    continue
                #elif item_partida_obj.campo_nota == 'vr_icms_st' and not item_obj.credita_icms_st:
                    #continue
                elif item_partida_obj.campo_nota == 'vr_ipi' and not item_obj.credita_ipi:
                    continue
                elif item_partida_obj.campo_nota == 'vr_pis_proprio' and not item_obj.credita_pis_cofins:
                    continue
                elif item_partida_obj.campo_nota == 'vr_cofins_proprio' and not item_obj.credita_pis_cofins:
                    continue

            contas = {}
            rateio_dic = {}

            item_obj.realiza_rateio(rateio=rateio_dic, context=context)

            dados_rateio = []
            dados_rateio = cc_pool.monta_dados(rateio_dic, campos=campos, lista_dados=dados_rateio, valor=valor, forcar_valor=valor)

            for rat_obj in dados_rateio:
                partida = PartidaDobrada()

                chave = ''
                if item_partida_obj.conta_credito_id:
                    partida.conta_credito_id = item_partida_obj.conta_credito_id
                    chave += str(item_partida_obj.conta_credito_id.id) + '_'
                elif rat_obj['conta_id']:
                    partida.conta_credito_id = conta_pool.browse(cr, uid, rat_obj['conta_id'])
                    chave += str(rat_obj['conta_id']) + '_'

                if item_partida_obj.conta_debito_id:
                    partida.conta_debito_id = item_partida_obj.conta_debito_id
                    chave += str(item_partida_obj.conta_debito_id.id) + '_'
                elif rat_obj['conta_id']:
                    partida.conta_debito_id = conta_pool.browse(cr, uid, rat_obj['conta_id'])
                    chave += str(rat_obj['conta_id']) + '_'

                if rat_obj['centrocusto_id']:
                    centrocusto_id = rat_obj['centrocusto_id']
                    partida.centrocusto_id = cc_pool.browse(cr, uid, centrocusto_id)
                    chave += str(rat_obj['centrocusto_id']) + '_'

                if item_partida_obj.historico_id:
                    partida.codigo_historico = item_partida_obj.historico_id.codigo

                if not chave in contas:
                    contas[chave] = partida
                    partida.valor = valor * D(rat_obj['porcentagem']) / D(100)
                else:
                    partida = contas[chave]
                    partida.valor += valor * D(rat_obj['porcentagem']) / D(100)


            for chave in contas:
                partida = contas[chave]
                if (partida.valor > 0) and \
                    (partida.conta_debito_id and partida.conta_credito_id) and \
                    partida.conta_credito_id.id != partida.conta_debito_id.id:
                    res.append(partida)

        return res

    def get_partidas_dobradas(self, cr, uid, ids, context={}):
        res = []

        partida_pool = self.pool.get('sped.modelo_partida_dobrada')

        partida_obj = False

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.documento_id.operacao_id and item_obj.documento_id.operacao_id.modelo_partida_dobrada_id:
                partida_obj = item_obj.documento_id.operacao_id.modelo_partida_dobrada_id
            else:
                partida_ids = partida_pool.search(cr, uid, [('modelo', '=', item_obj.documento_id.modelo)])
                if partida_ids:
                    partida_obj = partida_pool.browse(cr, uid, partida_ids[0])

        if not partida_obj:
            return res

        for item_partida_obj in partida_obj.item_ids:
            if item_partida_obj.campo_nota == 'vr_custo_estoque' and getattr(item_obj, item_partida_obj.campo_nota) == 0:
                res = []
                return res

            if not getattr(item_obj, item_partida_obj.campo_nota, False):
                continue

            #
            # Indica qual campo está sendo contabilizado
            #
            contexto_item = copy(context)
            contexto_item[item_partida_obj.campo_nota] = True

            rateio = item_obj.get_partidas_dobradas_rateio(item_partida_obj, D(getattr(item_obj, item_partida_obj.campo_nota, 0)), context=contexto_item)
            res += rateio

        return res


sped_documento_item()
