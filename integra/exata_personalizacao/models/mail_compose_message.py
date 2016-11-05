# -*- coding: utf-8 -*-

from osv import osv, fields


class mail_compose_message(osv.osv_memory):
    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context=None):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'finan.contrato':
            contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, res_id)

            if contrato_obj.natureza == 'RI':
                gerente_obj = self.pool.get('res.partner').browse(cr, uid, 7089)
                res['email_to'] = contrato_obj.vendedor_id.user_email

                if gerente_obj.email not in res['email_to']:
                    res['email_to'] += ','
                    res['email_to'] += gerente_obj.email

        return res


mail_compose_message()
