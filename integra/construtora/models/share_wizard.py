# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv


class share_wizard(osv.osv_memory):
    _inherit = 'share.wizard'

    def send_emails(self, cr, uid, wizard_data, context={}):
        self._logger.info(u'Enviando emails de compartilhamento...')
        mail_pool = self.pool.get('mail.message')
        user = self.pool.get('res.users').browse(cr, 1, uid)

        # TODO: also send an HTML version of this mail
        msg_ids = []

        for result_line in wizard_data.result_line_ids:
            email_to = result_line.user_id.user_email
            if not email_to:
                continue

            if not user.user_email:
                raise osv.except_osv(u'Email obrigatório!', u'Seu usuário precisa ter um endereço de email configurado nas preferências de usuário para poder enviar emails')

            assunto = wizard_data.name
            texto = u'Olá,'
            texto += u'\n\n'
            texto += u'Eu compartilhei %s com você!' % wizard_data.name
            texto += u'\n\n'
            texto += u'Os documentos não estão em anexo; você pode vê-los online diretamente no nosso sistema, no seguinte endereço:'
            texto += u'\n    ' + result_line.share_url
            texto += u'\n\n'

            if wizard_data.message:
                texto += wizard_data.message
                texto += u'\n\n'

            if result_line.newly_created:
                texto += u'Para que você possa ter acesso à informação, use o seguinte nome de usuário e senha:\n'
                texto += u'Usuário: %s\n' % result_line.user_id.login
                texto += u'Senha: %s\n' % result_line.password
                texto += u'Banco de dados: %s\n' % cr.dbname

            else:
                #texto += u'Os documento foram adicionandos automaticamente ao seu usuário no sistema.\n'
                #texto += u'Voce pode user seu login atual (%s) para ter acesso a eles\n' % result_line.user_id.login
                texto += u'Para que você possa ter acesso à informação, use o seguinte nome de usuário e senha:\n'
                texto += u'Usuário: %s\n' % result_line.user_id.login
                texto += u'Senha: %s\n' % result_line.user_id.password
                texto += u'Banco de dados: %s\n' % cr.dbname

            texto += u'\n\n'
            texto += (user.signature or u'')
            texto += u'\n\n'
            texto += u'--\n'
            texto += u'Enviado usando o ERP Integra - www.ERPIntegra.com.br'

            msg_ids.append(mail_pool.schedule_with_attach(cr, uid,
                                                       user.user_email,
                                                       [email_to],
                                                       assunto,
                                                       texto,
                                                       model='share.wizard',
                                                       context=context))
        # force direct delivery, as users expect instant notification
        mail_pool.send(cr, uid, msg_ids, context=context)
        self._logger.info(u'%d emails de compartilhamento enviados.', len(msg_ids))


share_wizard()
