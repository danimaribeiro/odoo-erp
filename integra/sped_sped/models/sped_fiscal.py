# -*- coding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from pybrasil.data import parse_datetime, hoje, agora, UTC, formata_data
from sped_fiscal_gerar import SPEDFiscal
import base64
from dateutil.relativedelta import relativedelta
from sped.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D


FINALIDADE = (
    ('0', u'0 - Arquivo original'),
    ('1', u'1 - Arquivo substituto')
)

TIPO_ATIVIDADE = (
    ('0', u'0 - Industrial ou equiparado (exige IPI)'),
    ('1', '1 - Outros (não exige IPI)')
)


class sped_sped_fiscal(osv.Model):
    _name = 'sped.sped_fiscal'
    _description = 'SPED Fiscal'
    _order = 'data desc'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'finalidade': fields.selection(FINALIDADE, u'Finalidade'),
        'perfil': fields.char(u'Perfil', size=1),
        'tipo_atividade': fields.selection(TIPO_ATIVIDADE, u'Atividade'),
        'stock_location_ids': fields.many2many('stock.location', 'sped_fiscal_stock_location', 'sped_fiscal_id', 'stock_location_id', u'Locais de estoque para inventário'),

        'nome_arquivo': fields.char(u'Nome arquivo', size=60),
        'data': fields.datetime(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'nome_arquivo_registro_h': fields.char(u'Nome arquivo registro H', size=60),
        'arquivo_registro_h': fields.binary(u'Arquivo registro H'),

        'questor': fields.boolean(u'Exportação para o Questor?'),
    }

    _defaults = {
        'finalidade': '0',
        'perfil': 'A',
        'tipo_atividade': '1',
        'questor': False,
    }

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return

        for sf_obj in self.browse(cr, uid, ids):
            sped = SPEDFiscal()
            sped.questor = sf_obj.questor
            sped.cr = cr
            sped.filial = sf_obj.company_id.partner_id
            sped.data_inicial = parse_datetime(sf_obj.data_inicial).date()
            sped.data_final = parse_datetime(sf_obj.data_final).date()
            sped.finalidade = sf_obj.finalidade
            sped.perfil = sf_obj.perfil
            sped.tipo_atividade = sf_obj.tipo_atividade

            sped.locais_estoque = []
            for loc_obj in sf_obj.stock_location_ids:
                sped.locais_estoque += [loc_obj.id]

            sped.gera_arquivo()

            dados = {
                'nome_arquivo': 'sped_fiscal.txt',
                'data': str(UTC.normalize(agora()))[:19],
                'arquivo_texto': sped.arquivo.decode('iso-8859-1').encode('utf-8'),
                'arquivo': base64.encodestring(sped.arquivo),
            }

            if sf_obj.data_inicial[5:7] == '02' and len(sped.locais_estoque):
                dados.update(self._relatorio_registro_h(cr, uid, ids, sped.locais_estoque))

            sf_obj.write(dados)

        return ids

    def _relatorio_registro_h(self, cr, uid, ids, locais_estoque, context={}):

        for sf_obj in self.browse(cr, uid, ids):
            sql_inventario = """
                select
                    es.company_id,
                    es.location_id,
                    pp.default_code,
                    es.product_id,
                    sum(
                        case
                            when es.tipo = 'S' then es.quantidade * -1
                            else es.quantidade
                        end
                    ) as quantidade,
                    coalesce(
                        (select
                            cm.vr_total / cm.quantidade
                        from
                            custo_medio(es.company_id, es.location_id, es.product_id) cm
                        where
                            cm.data <= '{data_inventario}'
                            and cm.vr_total > 0
                        order by
                            cm.data desc,
                            cm.entrada_saida desc,
                            cm.move_id desc
                        limit 1
                        ), 0) as custo_medio

                from
                    estoque_entrada_saida es
                    join stock_location sl on sl.id = es.location_id
                    join product_product pp on pp.id = es.product_id
                    join res_company c on c.id = es.company_id

                where
                    es.location_id in {location_ids}
                    and es.data <= '{data_inventario}'
                    and sl.usage = 'internal'
                    and c.cnpj_cpf = '{cnpj}'

                group by
                    es.company_id,
                    es.location_id,
                    pp.default_code,
                    es.product_id

                having
                    sum(
                        case
                            when es.tipo = 'S' then es.quantidade * -1
                            else es.quantidade
                        end
                    ) > 0

                order by
                    pp.default_code;
            """

            data_inventario = parse_datetime(sf_obj.data_inicial).date() + relativedelta(day=31, month=12, years=-1)
            sql_inventario = sql_inventario.format(data_inventario=data_inventario, location_ids=str(tuple(locais_estoque)).replace(',)', ')'), cnpj=sf_obj.company_id.cnpj_cpf)

            cr.execute(sql_inventario)
            dados_inventario = cr.fetchall()
            linhas = {}
            if len(dados_inventario) > 0:
                for company_id, location_id, produto_codigo, product_id, quantidade, custo_medio in dados_inventario:
                    produto_obj = self.pool.get('product.product').browse(cr, uid, product_id)
                    quantidade = D(quantidade or 0)
                    quantidade = quantidade.quantize(D('0.01'))
                    custo_medio = D(custo_medio or 0)
                    custo_medio = custo_medio.quantize(D('0.01'))

                    if produto_codigo not in linhas:
                        linha = DicionarioBrasil()
                        linhas[produto_codigo] = linha
                        linha['product_id'] = product_id
                        linha['produto_codigo'] = produto_codigo
                        linha['produto_nome'] = produto_obj.name
                        linha['produto'] = u'[' + produto_codigo + u'] ' + produto_obj.name
                        linha['quantidade'] = D(0)
                        linha['custo_medio'] = D(0)
                        linha['valor'] = D(0)

                    linha = linhas[produto_codigo]
                    linha['quantidade'] += quantidade

                    if custo_medio > linha['custo_medio']:
                        linha['custo_medio'] = custo_medio

                    #linha['custo_medio'] += custo_medio
                    #linha['valor'] += quantidade * custo_medio

            linhas_impresso = []
            codigos_ordem = linhas.keys()
            codigos_ordem.sort()
            arquivo_csv = ''
            for produto_codigo in codigos_ordem:
                linha = linhas[produto_codigo]

                if linha['custo_medio'] == 0:
                    produto_obj = self.pool.get('product.product').browse(cr, uid, linha['product_id'])
                    linha['custo_medio'] = D(produto_obj.standard_price or 1)

                linha['custo_medio'] = D(linha['custo_medio']).quantize(D('0.01'))

                linha['valor'] = linha['quantidade'] * linha['custo_medio']
                linha['valor'] = linha['valor'].quantize(D('0.01'))
                #if linha['valor'] == 0:
                    #produto_obj = self.pool.get('product.product').browse(cr, uid, linha['product_id'])
                    #linha['custo_medio'] = D(produto_obj.standard_price or 1)
                    #linha['valor'] = linha['quantidade'] * linha['custo_medio']

                #else:
                    #linha['custo_medio'] = linha['valor'] / D(linha['quantidade'] or 1)

                arquivo_csv += '"' + unicode(linha['produto_codigo']).encode('iso-8859-1').replace('"', '') + '";'
                arquivo_csv += '"' + unicode(linha['produto_nome']).encode('iso-8859-1').replace('"', '') + '";'
                arquivo_csv += str(linha['quantidade']).replace('.', ',') + ';'
                arquivo_csv += str(linha['custo_medio']).replace('.', ',') + ';'
                arquivo_csv += str(linha['valor']).replace('.', ',') + '\r\n'

                linhas_impresso.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Registro H - ref. ' + formata_data(data_inventario)
            rel.monta_contagem = True
            rel.colunas = [
                ['produto'    , 'C', 60, u'Produto', False],
                ['quantidade' , 'F', 10, u'Quantidade' , False],
                ['custo_medio', 'F', 10, u'Custo médio', False],
                ['valor'      , 'F', 12, u'Valor', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['local', u'Local', False],
            #]
            #rel.monta_grupos(rel.grupos)

            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Empresa ' + sf_obj.company_id.partner_id.razao_social + ' - '
            filtro.text += sf_obj.company_id.partner_id.cnpj_cpf
            filtro.text += ' - '
            filtro.text += formata_data(sf_obj.data_inicial)
            filtro.text += ' a '
            filtro.text += formata_data(sf_obj.data_final)


            pdf = gera_relatorio(rel, linhas_impresso)

            dados = {
                #'nome_arquivo_registro_h': 'registro_h.pdf',
                #'arquivo_registro_h': base64.encodestring(pdf),
                'nome_arquivo_registro_h': 'registro_h.csv',
                'arquivo_registro_h': base64.encodestring(arquivo_csv),
            }

            return dados


sped_sped_fiscal()
