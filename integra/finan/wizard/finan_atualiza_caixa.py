# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
import random


class finan_atualiza_caixa(osv.osv_memory):
    _description = u'Ajuste de rateio de lançamentos'
    _name = 'finan.atualiza.caixa'

    _columns = {
    }

    _defaults = {
    }

    def atualiza_caixas(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}
        caixa_ids = context['active_ids']
        saldo_pool = self.pool.get('finan.saldo')

        for caixa_obj in saldo_pool.browse(cr, uid, caixa_ids, context=context):            
            caixa_obj.write({'recalculo': int(random.random() * 100000000)})
            print('aqui')
            
        return {'type': 'ir.actions.act_window_close'}


finan_atualiza_caixa()
