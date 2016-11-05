# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
from sped.models.fields import CampoDinheiro


class finan_ajusta_rateio(osv.osv_memory):
    _description = u'Ajuste de rateio de lançamentos'
    _name = 'finan.ajusta.rateio'

    _columns = {
    }

    _defaults = {
    }

    def ajusta_rateio_lancamento(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        lancamento_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')

        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context=context):
            dados = lancamento_obj.onchange_centrocusto_id(lancamento_obj.centrocusto_id.id, lancamento_obj.valor_documento, lancamento_obj.valor, lancamento_obj.company_id.id, lancamento_obj.conta_id.id, partner_id=lancamento_obj.partner_id.id, data_vencimento=lancamento_obj.data_vencimento, data_documento=lancamento_obj.data_documento, context={})
            
            if 'value' not in dados:
                continue
            
            rateio_ids = dados['value']['rateio_ids']
            
            dados_rateio = []
            
            for rateio in rateio_ids:
                dados_rateio.append([0, False, rateio])
                
            print('dados')
            print('dados')
            print('dados')
            print('dados')
            print('dados')
            print(dados_rateio)
            
            #
            # Exclui os rateios anteriores
            #
            cr.execute('delete from finan_lancamento_rateio where lancamento_id = {id};'.format(id=lancamento_obj.id))
            
            lancamento_obj.write({'rateio_ids': dados_rateio})

        return {'type': 'ir.actions.act_window_close'}


finan_ajusta_rateio()
