# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID
from sped.models import trata_nfe
from sped.models import trata_nfse


class sped_documento(osv.Model):
    _inherit = 'sped.documento'
    _name = 'sped.documento'

    _columns = {
        'sale_order_ids': fields.many2many('sale.order', 'sale_order_sped_documento', 'sped_documento_id', 'sale_order_id', string=u'Orçamentos'),
    }

    def enviar_email_nota(self, cr, uid, ids, context={}):
        ids_contexto = context.get('active_ids', [])

        print('ids_contexto', ids_contexto)
        print('ids', ids)

        if ids_contexto:
            ids = ids_contexto

        if not ids:
            return False

        doc_pool = self.pool.get('sped.documento')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)
        mail_pool = self.pool.get('mail.message')
        attachment_pool = self.pool.get('ir.attachment')

        print('vai fazer')
        if user_obj.user_email:
            for doc_obj in doc_pool.browse(cr, uid, ids):
                if doc_obj.partner_id.email_nfe:
                    #
                    # Força a geração do PDF do recibo de locação
                    #
                    if doc_obj.modelo == 'RL':
                        trata_nfse.grava_pdf_recibo_locacao(self, cr, uid, doc_obj)
                    elif doc_obj.modelo == '55':
                        trata_nfe.gera_danfe(self, cr, uid, doc_obj)
                    elif doc_obj.modelo == 'SE':
                        trata_nfse.grava_pdf(self, cr, uid, doc_obj)

                    dados = {
                        #'subject':  u'Envio de nossa NF-e',
                        'subject':  u'Nota Fiscal e Boleto Software Beview',
                        'model': 'sped.documento',
                        'res_id': doc_obj.id,
                        'user_id': uid,
                        'email_to': doc_obj.partner_id.email_nfe or '',
                        #'email_to': 'ari@erpintegra.com.br',
                        'email_from': user_obj.user_email,
                        'date': str(fields.datetime.now()),
                        'headers': '{}',
                        'email_cc': '',
                        'reply_to': user_obj.user_email,
                        'state': 'outgoing',
                        'message_id': False,
                    }

                    mail_id = mail_pool.create(cr, uid, dados)

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sped.documento'), ('res_id', '=', doc_obj.id)])
                    if len(attachment_ids):
                        anexos = []
                        for attachment_id in attachment_ids:
                            anexos.append((4, attachment_id))
                        mail_pool.write(cr, uid, mail_id, {'attachment_ids': anexos})

                    mail_pool.process_email_queue(cr, uid, [mail_id])

        return {'value': {}, 'warning': {'title': u'Confirmação', 'message': u'Envio agendado!'}}


sped_documento()
