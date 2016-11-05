# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
from pybrasil.data import formata_data



class finan_altera_vencimento(osv.osv_memory):
    _description = u'Alteração de vencimento dos lançamentos'
    _name = 'finan.altera.vencimento'
    _inherit = 'ir.wizard.screen'

    _columns = {
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento'),
        'data_vencimento_anterior': fields.date(u'Vencimento anterior'),
        'data_vencimento': fields.date(u'Vencimento novo'),
        'justificativa': fields.char(u'Justificativa', size=80),
    }

    def confirmar(self, cr, uid, ids, context=None):
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        message_pool = self.pool.get('mail.message')

        for altera_obj in self.browse(cr, uid, ids):
            texto = u'Alterado do vencimento de '
            texto += formata_data(altera_obj.data_vencimento_anterior)
            texto += u' para '
            texto += formata_data(altera_obj.data_vencimento)
            texto += u' por '
            texto += user_obj.name
            texto += u'; justificativa: '
            texto += altera_obj.justificativa

            dados = {
                'model': 'finan.lancamento',
                'res_id': altera_obj.lancamento_id.id,
                #'display_text': texto,
                'date': fields.datetime.now(),
                'subject': texto,
                'body_text': texto,
            }

            message_pool.create(cr, uid, dados)
            altera_obj.lancamento_id.write({'data_vencimento': altera_obj.data_vencimento})


finan_altera_vencimento()
