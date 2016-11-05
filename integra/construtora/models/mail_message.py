# -*- coding: utf-8 -*-

from osv import osv, fields
from const_imovel import *


class mail_message(osv.Model):
    _name = 'mail.message'
    _inherit = 'mail.message'

    _columns = {
        'tipo_negociacao': fields.selection([('P', u'Proposta'), ('C', u'Contraproposta')], u'Tipo de negociação'),
        'valor': fields.float(u'Valor'),
    }

    def schedule_with_attach(self, cr, uid, email_from, email_to, subject, body, **kwargs):
        message_id = super(mail_message, self).schedule_with_attach(cr, uid, email_from, email_to, subject, body, **kwargs)

        if 'context' in kwargs:
            context = kwargs['context']

            dados = {}
            if 'tipo_negociacao' in context:
                dados['tipo_negociacao'] = context['tipo_negociacao']

            if 'valor' in context:
                dados['valor'] = context['valor']

            if dados:
                mail_pool = self.pool.get('mail.message')
                mail_pool.write(cr, uid, [message_id], dados)

                #
                # Verifica se deve mudar a etapa automaticamente
                #
                mail_obj = mail_pool.browse(cr, uid, message_id)
                contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, mail_obj.res_id)
                for etapa_obj in contrato_obj.etapa_seguinte_ids:
                    if etapa_obj.tipo_negociacao == mail_obj.tipo_negociacao:
                        contrato_obj.write({'etapa_id': etapa_obj.id})

        return message_id


mail_message()
