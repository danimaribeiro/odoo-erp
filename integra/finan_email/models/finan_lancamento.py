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
from pybrasil.valor import formata_valor, numero_por_extenso_unidade


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    def campos_email(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                'valor_documento_formatado': formata_valor(lancamento_obj.valor_documento or 0),
                'valor_documento_extenso': numero_por_extenso_unidade(lancamento_obj.valor_documento or 0),
                'data_vencimento_formatada': formata_data(lancamento_obj.data_vencimento or hoje()),
            }

            res[lancamento_obj.id] = dados

        return res

    _columns = {
        'valor_documento_extenso': fields.function(campos_email, type='char', string=u'Valor por extenso', multi='email'),
        'valor_documento_formatado': fields.function(campos_email, type='char', string=u'Valor formatado', multi='email'),
        'data_vencimento_formatada': fields.function(campos_email, type='char', string=u'Data de vencimento formatada', multi='email'),
    }


finan_lancamento()
