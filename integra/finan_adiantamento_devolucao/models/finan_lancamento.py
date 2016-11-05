# -*- coding: utf-8 -*-
#!/usr/bin/python

# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from time import time
from mako.template import Template
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import hoje
from string import upper
from finan.models.finan_lancamento import TIPO_LANCAMENTO_PAGAMENTO_PAGO, TIPO_LANCAMENTO_PAGAMENTO_RECEBIDO


class finan_lancamento(osv.Model):
    _description = u'Lançamentos'
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    def busca_saldo_adiantamento(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for lancamento in self.browse(cursor, user_id, ids):
            if lancamento.partner_id:
                partner_id = lancamento.partner_id.id
                data = str(hoje())
                sql = """
                    select
                       coalesce(fad.saldo, 0) as saldo

                    from
                        finan_adiantamento_devolucao fad
                        join res_partner_bank rpb on rpb.id = fad.res_partner_bank_id
                    where
                        fad.partner_id = """ + str(partner_id) + """
                        and fad.company_id = """ + str(lancamento.company_id.id) + """
                        and upper(coalesce(rpb.state, '')) = 'ADIANTAMENTO'
                        and fad.data_quitacao <= '""" + data + """'
                """

                #if lancamento.tipo == 'R':
                    #sql += """
                        #and fad.tipo = 'C'
                    #"""
                #else:
                    #sql += """
                       #and fad.tipo = 'F'
                    #"""

                sql += """
                    order by
                        fad.data_quitacao desc

                    limit 1;
                """

                print(sql)
                cursor.execute(sql)
                dados = cursor.fetchall()

                saldo = 0
                for saldo  in dados:
                    saldo = saldo[0]

                if saldo:
                    if lancamento.tipo == 'R':
                        retorno[lancamento.id] = saldo * -1
                    else:
                        retorno[lancamento.id] = saldo
                else:
                    retorno[lancamento.id] = 0

            else:
                retorno[lancamento.id] = 0

        return retorno


    def busca_saldo_devolucao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for lancamento in self.browse(cursor, user_id, ids):
            if lancamento.partner_id:
                partner_id = lancamento.partner_id.id
                data = str(hoje())
                sql = """
                    select
                       coalesce(fad.saldo, 0) as saldo

                    from
                        finan_adiantamento_devolucao fad
                        join res_partner_bank rpb on rpb.id = fad.res_partner_bank_id
                    where
                        fad.partner_id = """ + str(partner_id) + """
                        and fad.company_id = """ + str(lancamento.company_id.id) + """
                        and upper(coalesce(rpb.state, '')) = 'DEVOLUCAO'
                        and fad.data_quitacao <= '""" + data + """'
                """

                #if lancamento.tipo == 'R':
                    #sql += """
                        #and fad.tipo = 'C'
                    #"""
                #else:
                    #sql += """
                        #and fad.tipo = 'F'
                    #"""

                sql += """
                    order by
                        fad.data_quitacao desc

                    limit 1;
                """

                print(sql)
                cursor.execute(sql)
                dados = cursor.fetchall()

                saldo = 0
                for saldo  in dados:
                    saldo = saldo[0]

                if saldo:
                    if lancamento.tipo == 'R':
                        retorno[lancamento.id] = saldo * -1
                    else:
                        retorno[lancamento.id] = saldo
                else:
                    retorno[lancamento.id] = 0

            else:
                retorno[lancamento.id] = 0

        return retorno

    _columns = {
        'saldo_adiantamento': fields.function(busca_saldo_adiantamento, string=u'Saldo adiantamento', method=True, type='float'),
        'saldo_devolucao': fields.function(busca_saldo_devolucao, string=u'Saldo devolucão', method=True, type='float'),

        #
        # Pagamentos simples, só pode ser do tipo pagamento de conta a pagar ou a receber
        #
        'pagamento_adiantamento_ids': fields.one2many('finan.lancamento', 'lancamento_id', u'Pagamentos', domain=[('tipo', 'in', [TIPO_LANCAMENTO_PAGAMENTO_PAGO, TIPO_LANCAMENTO_PAGAMENTO_RECEBIDO]), ('res_partner_bank_id.state', 'ilike', 'ADIANTAMENTO')]),
    }

    def create(self, cr, uid, dados, context={}):
        if ('tipo' in dados and dados['tipo'] in ('PR','PP')):
            lanc_id =  dados.get('lancamento_id', False)
            banco_id = dados.get('res_partner_bank_id', False)

            if banco_id and lanc_id:
                bank_obj =  self.pool.get('res.partner.bank').browse(cr, uid, banco_id)

                if bank_obj.state and upper(bank_obj.state) == 'ADIANTAMENTO':
                    lancamento_obj = self.browse(cr, uid, lanc_id)
                    valor_ad = D(lancamento_obj.saldo_adiantamento or 0)

                    if valor_ad < 0:
                        valor_ad = valor_ad * -1

                    valor_pagamento = D(dados.get('valor', False) or 0)
                    if valor_ad < valor_pagamento:
                        raise osv.except_osv(u'Inválido !', u'Valor de Pagamento maior que valor de adiantamento!')

        res = super(finan_lancamento, self).create(cr, uid, dados, context)

        return res


finan_lancamento()
