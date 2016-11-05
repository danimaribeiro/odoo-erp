# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, formata_data
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, valida_cnpj, valida_cpf)


class finan_email(osv.Model):
    _description = u'Emails automaticos do financeiro'
    _name = 'finan.email'

    _columns = {
        'descricao': fields.char(u'Descrição', size=80),
        'dias': fields.integer(u'Dias'),
        'posicao': fields.selection((('A', u'Antes do vencimento'), ('D', u'Depois do vencimento')), u'Posição'),
        'template_id': fields.many2one('email.template', u'Modelo de email'),
        'com_contrato': fields.boolean(u'Somente clientes com contrato?'),
    }

    def enviar_emails(self, cr, uid, ids=[], context={}):
        partner_pool = self.pool.get('res.partner')
        template_pool = self.pool.get('email.template')
        mail_pool = self.pool.get('mail.message')

        email_pool = self.pool.get('finan.email')
        email_ids = email_pool.search(cr, uid, [])

        for email_obj in email_pool.browse(cr, uid, email_ids):
            sql = """
            select distinct
                l.partner_id

            from
                finan_lancamento l
                join res_partner p on p.id = l.partner_id
                {join_contrato}

            where
                l.tipo = 'R'
                and coalesce(l.provisionado, False) = False
                {situacao}
                {vencimento}
            """

            filtro = {}

            if email_obj.com_contrato:
                filtro['join_contrato'] = 'join finan_contrato c on c.id = l.contrato_id'
            else:
                filtro['join_contrato'] = ''

            if email_obj.posicao == 'A':
                filtro['situacao'] = "and (l.situacao = 'A vencer' or l.situacao = 'Vence hoje')"
                filtro['data'] = hoje() + relativedelta(days=email_obj.dias or 1)

            else:
                filtro['situacao'] = "and l.situacao = 'Vencido'"
                filtro['data'] = hoje() + relativedelta(days=(email_obj.dias or 1) * -1)

            filtro['data_vencimento'] = formata_data(filtro['data'])
            filtro['vencimento'] = "and l.data_vencimento = '{data}'".format(**filtro)

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            partner_ids = []
            for partner_id, in dados:
                partner_ids.append(partner_id)

            for partner_obj in partner_pool.browse(cr, uid, partner_ids):
                dados = template_pool.generate_email(cr, 1, email_obj.template_id.id, partner_obj.id, context=filtro)

                if 'attachment_ids' in dados:
                    del dados['attachment_ids']

                dados.update({
                    'model': 'res.partner',
                    'res_id': partner_id,
                    'user_id': uid,
                    'email_to': partner_obj.email_nfe or '',
                    #'email_from': user_obj.user_email,
                    'date': str(fields.datetime.now()),
                    #'reply_to': user_obj.user_email,
                    'state': 'outgoing',
                })

                mail_id = mail_pool.create(cr, uid, dados)
                #mail_pool.process_email_queue(cr, uid, [mail_id])


finan_email()
