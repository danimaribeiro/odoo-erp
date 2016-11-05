# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import parse_datetime
from dateutil.relativedelta import relativedelta

COMPLEMENTO_NUMEROS_SERIE = u'Números de série: ${ "; ".join([ns.numero_serie or "" for ns in item.numero_serie_ids]) }'


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    def action_enviar(self, cr, uid, ids, context=None):
        for doc_obj in self.browse(cr, uid, ids, context={'lang': 'pt_BR'}):
            if doc_obj.operacao_id and doc_obj.operacao_id.valida_numero_serie:
                for item_obj in doc_obj.documentoitem_ids:
                    if item_obj.produto_id.usa_numero_serie:
                        quantidade = item_obj.quantidade
                        if quantidade != len(item_obj.numero_serie_ids):
                            raise osv.except_osv(u'Erro!', u'A quantidade dos nº de série do produto ' + item_obj.produto_id.name_template + u', deve ser igual a ' + str(quantidade) + '!')

                        if COMPLEMENTO_NUMEROS_SERIE not in item_obj.infcomplementar:
                            infcomplementar = item_obj.infcomplementar or u''

                            if len(infcomplementar):
                                infcomplementar += u'\n'

                            infcomplementar += COMPLEMENTO_NUMEROS_SERIE

                            cr.execute("update sped_documentoitem set infcomplementar = '" + unicode(infcomplementar).encode('utf-8') + "' where id = " + str(item_obj.id) + ';')

        return super(sped_documento, self).action_enviar(cr, uid, ids, context=context)

    def ajusta_nf_garantia(self, cr, uid, ids, context={}):
        for nf_obj in self.browse(cr, uid, ids):
            if nf_obj.modelo != '55' or nf_obj.emissao != '0':
                continue

            if not nf_obj.operacao_id.marca_inicio_garantia:
                continue

            for item_obj in nf_obj.documentoitem_ids:
                if not item_obj.produto_id.warranty:
                    continue

                dados = {
                    'sped_documento_garantia_id': nf_obj.id,
                    'data_inicial_garantia': nf_obj.data_emissao_brasilia,
                    'data_final_garantia': str(parse_datetime(nf_obj.data_emissao_brasilia).date() + relativedelta(months=item_obj.produto_id.warranty))
                }

                for numser_obj in item_obj.numero_serie_ids:
                    if numser.sped_documento_garantia_id:
                        continue

                    numser_obj.write(dados)

    def depois_autorizar(self, cr, uid, ids, dados={}, context={}):
        res = super(sped_documento, self).depois_autorizar(cr, uid, ids, dados=dados, context=context)

        #self.pool.get('sped.documento').ajusta_nf_garantia(cr, uid, ids, context=context)

        return res


sped_documento()
