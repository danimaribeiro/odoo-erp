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
from pybrasil.feriado import data_eh_feriado


class finan_email(osv.Model):
    _description = u'Emails automaticos do financeiro'
    _name = 'finan.email'

    _columns = {
        'descricao': fields.char(u'Descrição', size=80),
        'dias': fields.integer(u'Dias'),
        'posicao': fields.selection((('A', u'Antes do vencimento'), ('D', u'Depois do vencimento')), u'Posição'),
        'template_id': fields.many2one('email.template', u'Modelo de email'),
        'com_contrato': fields.boolean(u'Somente clientes com contrato?'),
        'somente_dias_uteis': fields.boolean(u'Somente em dias úteis?'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento', ondelete='restrict'),
    }

    def enviar_emails(self, cr, uid, ids=[], context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        template_pool = self.pool.get('email.template')
        mail_pool = self.pool.get('mail.message')

        email_pool = self.pool.get('finan.email')
        email_ids = email_pool.search(cr, uid, [])

        for email_obj in email_pool.browse(cr, uid, email_ids):
            sql = """
            select distinct
                l.id

            from
                finan_lancamento l
                join res_partner p on p.id = l.partner_id
                {join_contrato}

            where
                l.tipo = 'R'
                and coalesce(l.provisionado, False) = False
                and p.email_nfe is not null
                and p.email_nfe != ''
                {situacao}
                {vencimento}
                {forma_pagamento}
            """

            filtro = {}

            if email_obj.com_contrato:
                filtro['join_contrato'] = 'join finan_contrato c on c.id = l.contrato_id'
            else:
                filtro['join_contrato'] = ''

            if email_obj.posicao == 'A':
                filtro['situacao'] = "and (l.situacao = 'A vencer' or l.situacao = 'Vence hoje')"
                filtro['data'] = hoje() + relativedelta(days=email_obj.dias or 1)
                filtro['vencimento'] = "and l.data_vencimento = '{data}'".format(**filtro)

            else:
                filtro['situacao'] = "and l.situacao = 'Vencido'"
                filtro['data'] = hoje() + relativedelta(days=(email_obj.dias or 1) * -1)
                filtro['vencimento'] = "and l.data_vencimento = '{data}'".format(**filtro)

                #
                # Tratamento especial para 1 dia
                #
                if email_obj.dias == 1:
                    data = hoje()

                    #
                    # segunda-feira
                    #
                    if data.weekday() == 0:
                        sexta = hoje() + relativedelta(days=-3)
                        compensa_feriado = len(data_eh_feriado(sexta, estado='SC', municipio='CHAPECO')) > 0
                        #
                        # Dá o aviso da sexta (e quinta, se sexta foi feriado)
                        #
                        if compensa_feriado:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-4)
                            filtro['data_final'] = hoje() + relativedelta(days=-3)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)

                        else:
                            filtro['data'] = hoje() + relativedelta(days=-3)
                            filtro['vencimento'] = "and l.data_vencimento = '{data}'".format(**filtro)
                    #
                    # terça-feira
                    #
                    elif data.weekday() == 1:
                        segunda = hoje() + relativedelta(days=-1)
                        compensa_feriado = len(data_eh_feriado(segunda, estado='SC', municipio='CHAPECO')) > 0
                        #
                        # Dá o aviso do sábado, do domingo e da segunda (e da sexta, se segunda foi feriado)
                        #
                        if compensa_feriado:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-4)
                            filtro['data_final'] = hoje() + relativedelta(days=-1)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)

                        else:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-3)
                            filtro['data_final'] = hoje() + relativedelta(days=-1)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)

                    #
                    # quarta-feira
                    #
                    elif data.weekday() == 2:
                        terca = hoje() + relativedelta(days=-1)
                        compensa_feriado = len(data_eh_feriado(terca, estado='SC', municipio='CHAPECO')) > 0

                        #
                        # Dá o aviso da terça (e do sábado, domingo e segunda, se na terça foi feriado)
                        #
                        if compensa_feriado:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-4)
                            filtro['data_final'] = hoje() + relativedelta(days=-1)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)

                    #
                    # quinta-feira
                    #
                    elif data.weekday() == 3:
                        quarta = hoje() + relativedelta(days=-1)
                        compensa_feriado = len(data_eh_feriado(quarta, estado='SC', municipio='CHAPECO')) > 0

                        #
                        # Dá o aviso da quarta (e da terça, se quarta foi feriado)
                        #
                        if compensa_feriado:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-2)
                            filtro['data_final'] = hoje() + relativedelta(days=-1)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)
                    #
                    # sexta-feira
                    #
                    elif data.weekday() == 4:
                        quinta = hoje() + relativedelta(days=-1)
                        compensa_feriado = len(data_eh_feriado(quinta, estado='SC', municipio='CHAPECO')) > 0

                        #
                        # Dá o aviso da quinta (e da quarta, se quinta foi feriado)
                        #
                        if compensa_feriado:
                            filtro['data_inicial'] = hoje() + relativedelta(days=-2)
                            filtro['data_final'] = hoje() + relativedelta(days=-1)
                            filtro['vencimento'] = "and l.data_vencimento between '{data_inicial}' and '{data_final}'".format(**filtro)

                    #
                    # sábado
                    #
                    elif data.weekday() == 5:
                        #
                        # Não manda email no sábado
                        #
                        continue

                    #
                    # domingo
                    #
                    elif data.weekday() == 6:
                        #
                        # Não manda email no domingo
                        #
                        continue

            if email_obj.formapagamento_id:
                filtro['forma_pagamento'] = 'and l.formapagamento_id = ' + str(email_obj.formapagamento_id.id)
            else:
                filtro['forma_pagamento'] = ''

            #filtro['data_vencimento'] = formata_data(filtro['data'])

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            lancamento_ids = []
            for lancamento_id, in dados:
                lancamento_ids.append(lancamento_id)

            for lancamento_obj in lancamento_pool.browse(cr, 1, lancamento_ids):
                dados = template_pool.generate_email(cr, 1, email_obj.template_id.id, lancamento_obj.id, context=filtro)

                if 'attachment_ids' in dados:
                    del dados['attachment_ids']

                dados.update({
                    'model': 'finan.lancamento',
                    'res_id': lancamento_obj.id,
                    'user_id': uid,
                    'email_to': lancamento_obj.partner_id.email_nfe or '',
                    #'email_from': user_obj.user_email,
                    'date': str(fields.datetime.now()),
                    #'reply_to': user_obj.user_email,
                    'state': 'outgoing',
                })

                mail_id = mail_pool.create(cr, uid, dados)
                #mail_pool.process_email_queue(cr, uid, [mail_id])


finan_email()
