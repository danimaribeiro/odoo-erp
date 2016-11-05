# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, formata_data

class finan_contrato_suspensao(osv.Model):
    _description = u'Suspensão Contrato'
    _name = 'finan.contrato.suspensao'
    _order = 'data_suspensao desc'


    def _dias_antes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):

            if item_obj.data_suspensao:
                res[item_obj.id] = int(str(item_obj.data_suspensao)[8:10])
            else:
                res[item_obj.id] = 0

        return res

    def _dias_depois(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):

            if item_obj.data_liberacao:
                ultimo_dia = ultimo_dia_mes(item_obj.data_liberacao)
                data_inicial = parse_datetime(item_obj.data_liberacao).date()
                dias = ultimo_dia - data_inicial
                res[item_obj.id] = dias.days
            else:
                res[item_obj.id] = 0

        return res

    def _valor_antes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if item_obj.data_suspensao:
                contrato_obj = item_obj.contrato_id
                valor += D(contrato_obj.valor_mensal)
                dias_mes = D(str(ultimo_dia_mes(item_obj.data_suspensao))[8:10])
                dias_antes = item_obj.dias_antes

                valor = valor / dias_mes * dias_antes
                valor = valor.quantize(D('0.01'))
                res[item_obj.id] = valor

            else:
                res[item_obj.id] = 0


        return res

    def _valor_depois(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if item_obj.data_liberacao:
                contrato_obj = item_obj.contrato_id
                valor += D(contrato_obj.valor_mensal)
                dias_mes = D(str(ultimo_dia_mes(item_obj.data_liberacao))[8:10])
                dias_antes = item_obj.dias_depois

                valor = valor / dias_mes * dias_antes
                valor = valor.quantize(D('0.01'))
                res[item_obj.id] = valor
            else:
                res[item_obj.id] = 0

        return res

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="cascade"),
        'name': fields.char(u'Descrição', size=512),
        'data_suspensao': fields.date(u'Data Suspensão'),
        'data_liberacao': fields.date(u'Data Liberação'),
        'create_uid': fields.many2one('res.users', u'Suspenso por'),
        'write_uid': fields.many2one('res.users', u'Liberado por'),
        'dias_antes': fields.function(_dias_antes, type='integer', string=u'Dias Antes', store=False),
        'dias_depois': fields.function(_dias_depois, type='integer', string=u'Dias Depois', store=False),
        'valor_antes': fields.function(_valor_antes, type='float', string=u'Valor Antes', store=False),
        'valor_depois': fields.function(_valor_depois, type='float', string=u'Valor Depois', store=False),
    }

    _defaults = {
        'data_suspensao': fields.datetime.now,
    }

    def verifica_data_suspensao(self, cr, uid, ids, dados, context=None):

        if 'contrato_id' in dados:

            contrato_id = dados.get('contrato_id')

            contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, contrato_id)

            for suspensao_obj in contrato_obj.suspensao_ids:

                if not suspensao_obj.data_liberacao:
                    raise osv.except_osv(u'ATENÇÃO!', u'Suspensão em Aberto, Finalize!')

            if 'data_suspensao' in dados:
                data_suspensao = dados.get('data_suspensao')

                sql = """
                select
                    case
                    when fs.data_liberacao is not null then
                    fs.data_liberacao
                    else
                    fs.data_suspensao end as data
                from
                    finan_contrato_suspensao fs
                where
                    fs.contrato_id = {contrato_id}
                    and fs.data_suspensao >= '{data}'
                order by
                    fs.data_suspensao desc
                limit 1
                """
                sql = sql.format(contrato_id=contrato_obj.id,data=data_suspensao)
                cr.execute(sql)
                dados = cr.fetchall()
                for data in dados:
                    raise osv.except_osv(u'ATENÇÃO!', u'Data de Suspensão deve ser maior que {data}!'.format(data=formata_data(data[0])))

    def gera_faturamento_supensao(self, cr, uid, ids, context=None):
        eventual_pool = self.pool.get('finan.contrato_produto')

        for suspensao_obj in self.browse(cr,uid, ids):

            contrato_obj = suspensao_obj.contrato_id

            for produto_mensal_obj in contrato_obj.contrato_produto_mensal_ids:

                if suspensao_obj.data_liberacao and str(suspensao_obj.data_suspensao)[:8] == str(suspensao_obj.data_liberacao)[:8]:
                    continue

                else:
                    dados_mensal = {
                        'contrato_id': contrato_obj.id,
                        'product_id': produto_mensal_obj.product_id.id,
                        'quantidade': produto_mensal_obj.quantidade * -1,
                        'vr_unitario': produto_mensal_obj.vr_unitario,
                        'vr_total': produto_mensal_obj.vr_total
                    }

                    if suspensao_obj.data_liberacao:
                        data = parse_datetime(suspensao_obj.data_liberacao) 
                        data = primeiro_dia_mes(data)
                        data = data + relativedelta(months=+1)
                        data = str(data)[:10]
                        data = str(data)[:8] + str(contrato_obj.dia_vencimento).zfill(2)                          
                        dados_mensal['data'] = data
                    else:
                        dados_mensal['data'] = suspensao_obj.data_suspensao
                        data = parse_datetime(suspensao_obj.data_suspensao) 
                        data = primeiro_dia_mes(data)
                        data = data + relativedelta(months=+1)
                        data = str(data)[:10]
                        data = str(data)[:8] + str(contrato_obj.dia_vencimento).zfill(2)                      
                        dados_mensal['data'] = data                        
                      

                    if produto_mensal_obj.res_partner_address_id:
                        dados_mensal['res_partner_address_id'] = produto_mensal_obj.res_partner_address_id.id

                    if produto_mensal_obj.hr_department_id:
                        dados_mensal['hr_department_id'] = produto_mensal_obj.hr_department_id.id

                    eventual_pool.create(cr, uid, dados_mensal)

            for produto_mensal_obj in contrato_obj.contrato_produto_mensal_ids:

                dados_suspensao = {
                    'contrato_id': contrato_obj.id,
                    'suspensao_id': suspensao_obj.id,
                    'product_id': produto_mensal_obj.product_id.id,
                    'quantidade': 1,
                }

                if suspensao_obj.data_liberacao:                                       
                    data = parse_datetime(suspensao_obj.data_liberacao) 
                    data = primeiro_dia_mes(data)
                    data = data + relativedelta(months=+1)
                    data = str(data)[:10]
                    data = str(data)[:8] + str(contrato_obj.dia_vencimento).zfill(2)                          
                    dados_suspensao['data'] = data                                    
                    dados_suspensao['vr_unitario'] = suspensao_obj.valor_depois
                    dados_suspensao['vr_total'] =  suspensao_obj.valor_depois                
                else:
                    data = parse_datetime(suspensao_obj.data_suspensao) 
                    data = primeiro_dia_mes(data)
                    data = data + relativedelta(months=+1)
                    data = str(data)[:10]
                    data = str(data)[:8] + str(contrato_obj.dia_vencimento).zfill(2)                          
                    dados_suspensao['data'] = data                                                 
                    dados_suspensao['vr_unitario'] = suspensao_obj.valor_antes
                    dados_suspensao['vr_total'] =  suspensao_obj.valor_antes

                if produto_mensal_obj.res_partner_address_id:
                    dados_suspensao['res_partner_address_id'] = produto_mensal_obj.res_partner_address_id.id

                if produto_mensal_obj.hr_department_id:
                    dados_suspensao['hr_department_id'] = produto_mensal_obj.hr_department_id.id

                eventual_pool.create(cr, uid, dados_suspensao)

    def create(self, cr, uid, dados, context={}):
        self.verifica_data_suspensao(cr, uid, False, dados, context=context)

        res = super(finan_contrato_suspensao, self).create(cr, uid, dados, context=context)

        suspensao_obj = self.browse(cr,uid, res)

        if not suspensao_obj.data_liberacao:
            self.gera_faturamento_supensao(cr, uid, [res], context=context)
            contrato_obj = suspensao_obj.contrato_id
            contrato_obj.write({'suspenso_inadimplente': True})

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_contrato_suspensao, self).write(cr, uid, ids, dados, context=context)

        for suspensao_obj in self.browse(cr, uid, ids):
            contrato_obj = suspensao_obj.contrato_id
            sql = """
                select
                id
                from finan_contrato_suspensao fs
                where
                fs.contrato_id = {contrato_id}
                and fs.data_liberacao is null
            """
            sql = sql.format(contrato_id=contrato_obj.id)
            cr.execute(sql)
            dados_sql = cr.fetchall()
            if not dados_sql:
                contrato_obj.write({'suspenso_inadimplente': False})

            if 'data_liberacao' in dados:
                data_liberacao = dados.get('data_liberacao')

                sql = """
                select
                    fs.data_suspensao
                from
                    finan_contrato_suspensao fs
                where
                    fs.contrato_id = {contrato_id}
                    and fs.data_suspensao >= '{data}'
                order by
                    fs.data_suspensao desc
                limit 1
                """
                sql = sql.format(contrato_id=contrato_obj.id,data=data_liberacao)
                print(sql)
                cr.execute(sql)
                dados_sql = cr.fetchall()
                for data in dados_sql:
                    raise osv.except_osv(u'ATENÇÃO!', u'Data de Liberacão deve ser maior que {data}!'.format(data=formata_data(data[0])))

        self.gera_faturamento_supensao(cr, uid, ids, context=context)

        return res

finan_contrato_suspensao()

