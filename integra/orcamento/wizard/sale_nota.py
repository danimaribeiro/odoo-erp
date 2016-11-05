# -*- coding: utf-8 -*-


from osv import fields, osv
from mail.mail_message import truncate_text
from datetime import datetime


class sale_nota(osv.osv_memory):
    _name = 'sale.nota'
    _description = u'Adiciona anotação interna'

    _columns = {
        'data_hora': fields.datetime('Data', required=True),
        'texto': fields.text('Nota', required=True),
    }

    _defaults = {
        'data_hora': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def adiciona_nota(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        if (not context.get('modelo')) or (not context.get('texto')) or (not context.get('data_hora')):
            return {'type': 'ir.actions.act_window_close'}

        modelo = context.get('modelo')
        modelo_pool = self.pool.get(modelo)
        modelo_ids = context['active_ids']
        texto = context['texto']
        data_hora = context['data_hora']

        for id in modelo_ids:
            modelo_pool.message_append(cr, uid, [id], truncate_text(texto), body_text=texto, email_date=data_hora, forcar_data=True)

        return {'type': 'ir.actions.act_window_close'}


sale_nota()
