# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
import os
from osv import osv, orm, fields
from dateutil.relativedelta import relativedelta
from pybrasil.febraban.banco_central import *
from pybrasil.data import hoje, parse_datetime, formata_data
from pybrasil.inscricao import limpa_formatacao
from pybrasil.sped.base.certificado import Certificado
from pybrasil.valor.decimal import Decimal as D


WS_BACEN = [
   [str(WS_BC_DOLAR), u'Dólar'],
   [str(WS_BC_EURO_VENDA), u'Euro'],
   #[str(WS_BC_IGPM), u'IGPM'],
   #[str(WS_BC_INPC), u'INPC'],
   #[str(WS_BC_EURO_COMPRA), u'Euro - compra'],
    #WS_BC_IGPM: u'IGPM',
    #WS_BC_INPC: u'INPC',
    #WS_BC_SELIC: u'SELIC',
]


class res_currency(orm.Model):
    _name = 'res.currency'
    _inherit = 'res.currency'

    def _taxa_atual(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        if 'date' in context:
            data = context['date']
        elif 'data' in context:
            data = context['data']
        else:
            data = str(hoje())

        data = data or str(hoje())

        if 'data_base' in context:
            data_base = context['data_base']
        else:
            data_base = str(hoje())

        data_base = data_base or str(hoje())

        for id in ids:
            res[id] = {'rate': D(0), 'taxa_acumulada': D(0)}

            sql = """
                select
                    coalesce(t.rate, 0)

                from
                    res_currency_rate t

                where
                    t.currency_id = {currency_id}
                    and t.name <= '{data}'

                order by
                    t.name desc

                limit 1;
            """
            sql = sql.format(currency_id=id, data=data)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                res[id]['rate'] = D(dados[0][0] or 0).quantize(D('0.000001'))

            sql = """
                select
                    coalesce(t.rate, 0)

                from
                    res_currency_rate t

                where
                    t.currency_id = {currency_id}
                    and t.name <= '{data}'
                    and t.name > '{data_base}'
                    and t.rate > 0

                order by
                    t.name;
            """
            sql = sql.format(currency_id=id, data=data, data_base=data_base)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                taxa_acumulada = D(0)
                for taxa, in dados:
                    taxa_acumulada = (1 + (taxa_acumulada / 100)) * D(1 + (D(taxa or 0) / 100))
                    taxa_acumulada -= 1
                    taxa_acumulada *= 100

                res[id]['taxa_acumulada'] = taxa_acumulada

        return res


    _columns = {
        'rate': fields.function(_taxa_atual, type='float', string=u'Taxa atual', digits=(12, 6), multi='taxa'),
        'taxa_acumulada': fields.function(_taxa_atual, type='float', string=u'Taxa acumulada', digits=(12, 6), multi='taxa'),
        'codigo_ws_bacen': fields.selection(WS_BACEN, u'Atualização do BACEN'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
    }

    def atualiza_cotacao(self, cr, uid, ids=[], context={}):
        datas = False

        if not ids:
            ids = self.pool.get('res.currency').search(cr, uid, [('codigo_ws_bacen', '!=', False)])
            datas = True

        #
        # Empresa para usar o certificado
        #
        company_ids = self.pool.get('res.company').search(cr, 1, [('cnpj_cpf', '!=', False)])
        company_obj = self.pool.get('res.company').browse(cr, 1, company_ids[0])

        taxa_pool = self.pool.get('res.currency.rate')

        empresa = company_obj.partner_id
        caminho_empresa = os.path.expanduser('~/sped')
        caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf))

        certificado = Certificado()
        certificado.arquivo = open(os.path.join(caminho_empresa, 'certificado_caminho.txt')).read().strip()
        certificado.senha = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip()

        for moeda_obj in self.browse(cr, uid, ids):
            if not datas:
                data_inicial = moeda_obj.data_inicial or hoje()
                data_final = moeda_obj.data_final or hoje()
            else:
                data_inicial = hoje()
                data_final = hoje()

            data_inicial = parse_datetime(data_inicial)
            data_final = parse_datetime(data_final)

            data = data_inicial

            while data <= data_final:
                valor = D(0)

                if moeda_obj.codigo_ws_bacen == str(WS_BC_DOLAR):
                    valor = cotacao_dolar(certificado, data)
                elif moeda_obj.codigo_ws_bacen == str(WS_BC_EURO_VENDA):
                    valor = cotacao_euro(certificado, data)

                dados = {
                    'currency_id': moeda_obj.id,
                    'name': str(data),
                    'rate': valor
                }

                #
                # Já existe?
                #
                taxa_id = taxa_pool.search(cr, uid, [('currency_id', '=', moeda_obj.id), ('name', '=', str(data))])

                if len(taxa_id):
                    taxa_pool.write(cr, uid, taxa_id, dados)
                else:
                    taxa_pool.create(cr, uid, dados)

                data += relativedelta(days=+1)

        return True

    def taxa_conversao(self, cr, uid, moeda_origem_id, moeda_destino_id, data=None, data_base=None, context={}):
        if data is None:
            data = hoje()

        if data_base is None:
            data_base = hoje()

        contexto_novo = {}
        contexto_novo['data'] = str(data)
        contexto_novo['data_base'] = str(data_base)
        print('contexto_novo', contexto_novo)

        moeda_origem_obj = self.browse(cr, uid, moeda_origem_id, context=contexto_novo)
        moeda_destino_obj = self.browse(cr, uid, moeda_destino_id, context=contexto_novo)

        if not moeda_origem_obj.rate:
            if moeda_origem_obj.symbol == '%':
                raise osv.except_osv(u'Erro', u'O índice ' + moeda_origem_obj.name + u' não tem taxa de conversão para o dia ' + formata_data(data))
            else:
                raise osv.except_osv(u'Erro', u'A moeda ' + moeda_origem_obj.name + u' não tem taxa de conversão para o dia ' + formata_data(data))

        if not moeda_destino_obj.rate:
            if moeda_destino_obj.symbol == '%':
                raise osv.except_osv(u'Erro', u'O índice ' + moeda_destino_obj.name + u' não tem taxa de conversão para o dia ' + formata_data(data))
            else:
                raise osv.except_osv(u'Erro', u'A moeda ' + moeda_destino_obj.name + u' não tem taxa de conversão para o dia ' + formata_data(data))

        taxa = D(moeda_destino_obj.rate or 1) / D(moeda_origem_obj.rate or 1)
        taxa_acumulada = D(moeda_destino_obj.taxa_acumulada or 1) / (moeda_origem_obj.taxa_acumulada or 1)

        if moeda_destino_obj.symbol == '%':
            taxa = D(1 + (taxa / 100))

        elif moeda_destino_obj.symbol == '%a':
            taxa = D(1 + (taxa_acumulada / 100))

        return taxa

    def converte(self, cr, uid, moeda_origem_id, moeda_destino_id, valor_original, data=None, data_base=None, context={}):
        valor_original = D(valor_original or 0)
        taxa = self.taxa_conversao(cr, uid, moeda_origem_id, moeda_destino_id, data=data, data_base=data_base, context=context)
        valor_corrigido = valor_original * taxa
        valor_corrigido = valor_corrigido.quantize(D('0.01'))

        return valor_corrigido


res_currency()



class res_currency_rate(orm.Model):
    _name = 'res.currency.rate'
    _inherit = 'res.currency.rate'

    _columns = {
        'taxa_acumulada': fields.float(u'Taxa acumulada', digits=(12, 6)),
    }

res_currency_rate()
