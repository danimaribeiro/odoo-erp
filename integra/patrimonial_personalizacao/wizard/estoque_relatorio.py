# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
import base64
from finan.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from relatorio import *


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class estoque_relatorio(osv.osv_memory):
    _inherit = 'estoque.relatorio'
    _name = 'estoque.relatorio'


    _columns = {
        'operacao_id': fields.many2one('stock.operacao', u'Operação'),

    }

    _defaults = {

    }


    def movimentacao_interna_operacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            operacao_id = rel_obj.operacao_id.id
            operacao_nome = rel_obj.operacao_id.nome
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]

            sql = """
                select
                    rp.name,
                    pp.name_template as produto,
                    pp.default_code,
                    pu.name,
                    sum(sm.product_qty) as quantidade

                    from stock_picking sp
                    join stock_move sm on sm.picking_id = sp.id
                    join product_product pp on pp.id = sm.product_id
                    join product_template pt on pt.id = pp.product_tmpl_id
                    left join product_uom pu on pu.id = pt.uom_id

                    join res_company c on c.id = sp.company_id
                    join res_partner rp on rp.id = c.partner_id

                    where sp.operacao_id = '{operacao}'
                    and
                    sm.date between '{data_inicial}' and '{data_final}'

                    group by

                    rp.name,
                    pp.name_template,
                    pp.default_code,
                    pu.name

                    order by
                    rp.name, pp.name_template;
            """

            cr.execute(sql.format(operacao=str(operacao_id),data_inicial=data_inicial, data_final=data_final))

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            for empresa, produto, codigo, unidade, quantidade in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['codigo'] = codigo
                linha['produto'] = produto
                linha['unidade'] = unidade
                linha['quantidade'] = quantidade
                linhas.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Movimentação por Operação'
            rel.colunas = [
                ['codigo' , 'C', 8, u'Código', False],
                ['produto' , 'C', 50, u'Produto', False],
                ['unidade' , 'C', 5, u'UN', False],
                ['quantidade' , 'F', 10, u'Quantidade', True],

            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
            ]
            rel.monta_grupos(rel.grupos)


            rel.band_page_header.elements[-1].text = u'Operação: ' + operacao_nome + u' - Periodo ' + formata_data(data_inicial) + ' - ' + formata_data(data_final)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'movimento_por_operacao.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_produtos_cadastrado(self, cr, uid, ids, context={}):

        product_pool = self.pool.get('product.product')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        product_ids = product_pool.search(cr,uid, [])

        linhas = []
        for product_obj in product_pool.browse(cr,uid, product_ids):

            linha = DicionarioBrasil()

            if len(product_obj.relacionado_orcamento_ids) > 0:

                for product_relacionado in product_obj.relacionado_orcamento_ids:

                    if product_obj.company_id.partner_id:
                        linha['empresa'] = product_obj.company_id.partner_id.name or ''
                    else:
                        linha['empresa'] = ''

                    linha['codigo'] = product_obj.default_code
                    linha['descricao'] = product_obj.name
                    linha['nome_generico'] = product_obj.nome_generico or ''
                    linha['subtipos'] = product_obj.variants or ''

                    if product_obj.familiatributaria_id:
                        linha['familiatributaria'] = product_obj.familiatributaria_id.descricao or ''
                    else:
                        linha['familiatributaria'] = ''

                    if product_obj.orcamento_categoria_id:
                        linha['orcamento_categoria'] = product_obj.orcamento_categoria_id.nome or ''
                    else:
                        linha['orcamento_categoria'] = ''

                    if product_relacionado.produto_relacionado_id:
                        linha['produto_relacionado'] = product_relacionado.produto_relacionado_id.name or ''
                    else:
                        linha['produto_relacionado'] = ''

                    linha['quantidade_relacionada'] = formata_valor(D(product_relacionado.quantidade or 0))

                    if product_obj.state == 'draft':
                        linha['situacao'] = 'Em Desenvolvimento'
                    elif product_obj.state == 'sellable':
                        linha['situacao'] = 'Normal'
                    elif product_obj.state == 'end':
                        linha['situacao'] = 'Fim do ciclo de vida'
                    else:
                        linha['situacao'] = 'Obsoleto'

                    linha['unidade_medida'] = product_obj.uom_id.name

                    linha['vr_unitario_venda'] = formata_valor(D(product_obj.custo_ultima_compra or 0))
                    linha['vr_unitario_locacao'] = formata_valor(D(product_obj.custo_ultima_compra_locacao or 0))
                    linhas.append(linha)
            else:

                if product_obj.company_id.partner_id:
                    linha['empresa'] = product_obj.company_id.partner_id.name or ''
                else:
                    linha['empresa'] = ''

                linha['codigo'] = product_obj.default_code
                linha['descricao'] = product_obj.name
                linha['nome_generico'] = product_obj.nome_generico or ''
                linha['subtipos'] = product_obj.variants or ''

                if product_obj.familiatributaria_id:
                    linha['familiatributaria'] = product_obj.familiatributaria_id.descricao or ''
                else:
                    linha['familiatributaria'] = ''

                if product_obj.orcamento_categoria_id:
                    linha['orcamento_categoria'] = product_obj.orcamento_categoria_id.nome or ''
                else:
                    linha['orcamento_categoria'] = ''

                linha['produto_relacionado'] = ''

                linha['quantidade_relacionada'] = 0

                if product_obj.state == 'draft':
                    linha['situacao'] = 'Em Desenvolvimento'
                elif product_obj.state == 'sellable':
                    linha['situacao'] = 'Normal'
                elif product_obj.state == 'end':
                    linha['situacao'] = 'Fim do ciclo de vida'
                else:
                    linha['situacao'] = 'Obsoleto'

                linha['unidade_medida'] = product_obj.uom_id.name

                linha['vr_unitario_venda'] = formata_valor(D(product_obj.custo_ultima_compra or 0))
                linha['vr_unitario_locacao'] = formata_valor(D(product_obj.custo_ultima_compra_locacao or 0))
                linhas.append(linha)

        dados = {
            'titulo': u'Produtos em Estoque',
            'data': formata_data(agora()),
            'linhas': linhas,
        }

        nome_arquivo = JASPER_BASE_DIR + 'listagem_produtos_cadastrados.ods'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)

        dados = {
            'nome': 'listagem_produtos_cadastrados.xlsx',
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True

    def gera_estoque_minimo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            location_id = rel_obj.location_id.id

            sql = """
            select
                *
            from  (
                select
                    pp.id,
                    coalesce((
                    select
                        sw.product_min_qty

                    from
                        stock_warehouse_orderpoint sw

                    where
                        sw.product_id = pp.id
                        and sw.location_id = {location_id}
                    ), 0) as estoque_minimo

                from
                    product_product pp
                    join product_template pt on pt.id = pp.product_tmpl_id

                order by
                    pt.name
            ) as em

            where
                estoque_minimo > 0;
            """
            sql = sql.format(location_id=location_id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            product_pool = self.pool.get('product.product')
            linhas = []
            for product_id, estoque_minimo in dados:
                product_obj = product_pool.browse(cr, uid, product_id)
                linha = DicionarioBrasil()
                linha['codigo'] = product_obj.default_code or ''
                linha['produto'] = product_obj.name or ''
                linha['variants'] = product_obj.variants or ''
                linha['estoque_minimo'] = estoque_minimo or 0
                linha['na_mao'] = product_obj.qty_available or 0
                linha['disponivel'] = product_obj.virtual_available or 0
                #<field name="qty_locacao" />
                #<field name="quantidade_disponivel_locacao" />

                linhas.append(linha)


            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Estoque mínimo'
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['produto' , 'C', 50, u'Descrição', False],
                ['variants', 'C', 15, u'Marca', False],
                ['estoque_minimo' , 'F', 10, u'Mínimo', True],
                ['na_mao' , 'F', 10, u'Na mão', True],
                ['disponivel' , 'F', 10, u'Disponível', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['categoria', u'Categoria', False],
            #]
            #rel.monta_grupos(rel.grupos)

            location_obj = self.pool.get('stock.location').browse(cr, uid, location_id)
            rel.band_page_header.elements[-1].text = u'Local: ' + location_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'estoque_minimo.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True


estoque_relatorio()
