# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor import formata_valor
from pybrasil.valor.decimal import Decimal as D
from sped_modelo_partida_dobrada import PartidaDobrada, CAMPO_CONTABILIZA_ITEM
from copy import copy


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'contabilizacao_ids': fields.one2many('sped.documento.contabilidade', 'documento_id', u'Lançamentos contábeis'),
    }

    def get_partidas_dobradas(self, cr, uid, ids, context={}):
        res = []

        partida_pool = self.pool.get('sped.modelo_partida_dobrada')

        partida_obj = False

        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.operacao_id and doc_obj.operacao_id.modelo_partida_dobrada_id:
                partida_obj = doc_obj.operacao_id.modelo_partida_dobrada_id
            else:
                partida_ids = partida_pool.search(cr, uid, [('modelo', '=', doc_obj.modelo)])
                if partida_ids:
                    partida_obj = partida_pool.browse(cr, uid, partida_ids[0])

        if not partida_obj:
            return res

        for item_partida_obj in partida_obj.item_ids:
            if (not item_partida_obj.conta_credito_id) or (not item_partida_obj.conta_debito_id) or item_partida_obj.campo_nota in CAMPO_CONTABILIZA_ITEM:

                if item_partida_obj.campo_nota in CAMPO_CONTABILIZA_ITEM :
                    for item_obj in doc_obj.documentoitem_ids:

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

                    continue

                else:
                    lanc_obj = None

                    if doc_obj.finan_lancamento_id:
                        lanc_obj = doc_obj.finan_lancamento_id
                    elif doc_obj.duplicata_ids and doc_obj.duplicata_ids[0].finan_lancamento_id:
                        lanc_obj = doc_obj.duplicata_ids[0].finan_lancamento_id

                    if lanc_obj:
                        rateio = lanc_obj.get_partidas_dobradas_rateio(item_partida_obj, D(getattr(doc_obj, item_partida_obj.campo_nota, 0)))
                        res += rateio
                        continue


            partida = PartidaDobrada()

            if item_partida_obj.conta_credito_id:
                partida.conta_credito_id = item_partida_obj.conta_credito_id
            elif doc_obj.finan_conta_id:
                partida.conta_credito_id = doc_obj.finan_conta_id

            if item_partida_obj.conta_debito_id:
                partida.conta_debito_id = item_partida_obj.conta_debito_id
            elif doc_obj.finan_conta_id:
                partida.conta_credito_id = doc_obj.finan_conta_id

            if item_partida_obj.historico_id:
                partida.codigo_historico = item_partida_obj.historico_id.codigo
                partida.historico = item_partida_obj.historico_id.nome or u'' + ' '

            #
            # Busca o valor do campo correspondente
            #
            partida.valor = D(getattr(doc_obj, item_partida_obj.campo_nota, 0))

            #partida.historico += formata_valor(doc_obj.numero, casas_decimais=0)
            #partida.historico += ' - '

            #if doc_obj.partner_id.razao_social:
            #    partida.historico += doc_obj.partner_id.razao_social
            #else:
            #    partida.historico += doc_obj.partner_id.name

            if (partida.valor > 0) and \
                (partida.conta_debito_id and partida.conta_credito_id) and \
                partida.conta_credito_id.id != partida.conta_debito_id.id:
                res.append(partida)

        return res

    def gera_contabilizacao(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            #
            # Exclui as contabilizações anteriores
            #
            for cont_obj in doc_obj.contabilizacao_ids:
                cont_obj.unlink()

            partidas = doc_obj.get_partidas_dobradas()

            for partida in partidas:
                dados = {
                    'documento_id': doc_obj.id,
                    'data': fields.related('documento_id', 'data_entrada_saida_brasilia', type='date', string=u'Data'),
                    'conta_credito_id': partida.conta_credito_id.id,
                    'conta_debito_id': partida.conta_debito_id.id,
                    'valor': partida.valor,
                    'codigo_historico': partida.codigo_historico,
                    'historico': partida.historico,
                }
                self.pool.get('sped.documento.contabilidade').create(cr, uid, dados)

            #
            # Agora, geramos as partidas individuais de cada item
            #
            for item_obj in doc_obj.documentoitem_ids:
                for cont_obj in item_obj.contabilizacao_ids:
                    cont_obj.unlink()

                partidas = item_obj.get_partidas_dobradas()

                for partida in partidas:
                    dados = {
                        'documentoitem_id': item_obj.id,
                        #'data': fields.related('documentoitem_id', 'data_entrada_saida_brasilia', type='date', string=u'Data'),
                        'conta_credito_id': partida.conta_credito_id.id,
                        'conta_debito_id': partida.conta_debito_id.id,
                        'valor': partida.valor,
                        'codigo_historico': partida.codigo_historico,
                        'historico': partida.historico,
                    }
                    self.pool.get('sped.documento.contabilidade').create(cr, uid, dados)

        return {}

    def get_rateio_contabil_gerencial(self, cr, uid, ids, context={}):
        res = []

        for doc_obj in self.browse(cr, uid, ids):
            lanc_obj = None
            if doc_obj.finan_lancamento_id:
                lanc_obj = doc_obj.finan_lancamento_id
            elif doc_obj.duplicata_ids and doc_obj.duplicata_ids[0].finan_lancamento_id:
                lanc_obj = doc_obj.duplicata_ids[0].finan_lancamento_id

            if lanc_obj:
                rateio = lanc_obj.get_rateio_contabil_gerencial()
                print('rateio gerencial')
                print(rateio)
                res += rateio

        return res



sped_documento()
