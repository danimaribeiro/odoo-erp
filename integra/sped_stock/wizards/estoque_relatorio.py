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
from finan.wizard.finan_relatorio import Report
from collections import OrderedDict


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)



class estoque_relatorio(osv.osv_memory):
    _name = 'estoque.relatorio'
    _description = u'Relatórios do Estoque'
    _rec_name = 'nome'

    _columns = {
        #'ano': fields.integer(u'Ano'),
        #'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.date(u'Data do Arquivo'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'variants': fields.char(u'Subtipos', 120),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        #'tipo': fields.selection(TIPOS, u'Tipo'),
        'analitico': fields.boolean(u'Analítico?'),
        'acumula_produto': fields.boolean(u'Acumula por produto?'),
        'product_id': fields.many2one('product.product', u'Produto'),
        'location_id': fields.many2one('stock.location', u'Local do Estoque'),
        'category_id': fields.many2one('product.category', u'Categoria'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'location_ids': fields.many2many('stock.location', 'stock_location_relatorio', 'estoque_relatorio_id','location_id', u'Locais de Estoque'),
        'custo_ids': fields.one2many('custo.unidade.local.item', 'relatorio_id', u'Custo Unidade Local Itens'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'data': fields.date.today,
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        #'tipo': 'T',
        'formato': 'pdf',
    }

    def gera_movimento_estoque(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            sql = u'''
select
p.id as produto_id,
p.default_code as codigo,
p.name_template as produto,
l.id as local_id,
l.complete_name as local,
cm.data,
cm.entrada_saida,
cm.entrada,
cm.saida,
cast(cm.vr_unitario as varchar),
cast(cm.vr_unitario_custo as varchar),
cm.quantidade,
cm.vr_total,
case
  when pp.id is not null then '[' || coalesce(pp.name, '') || '] - ' || m.name
  else m.name
end as documento

from
custo_medio({company_id}, {local_id}, {produto_id}) cm
join stock_location l on l.id = cm.location_id and usage = 'internal'
join product_product p on p.id = cm.product_id
join stock_move m on m.id = cm.move_id
join res_company c on c.id = cm.company_id
left join stock_picking pp on pp.id = m.picking_id

where
cm.data between '{data_inicial}' and '{data_final}'
--and cast(p.id as varchar) like '{produto_id}'
--and cast(l.id as varchar) like '{local_id}'
--and cast(c.id as varchar) like '{company_id}'

order by
p.name_template,
l.complete_name,
cm.data,
cm.entrada_saida,
m.id;
            '''

            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
            }

            if rel_obj.product_id:
                filtro['produto_id'] = rel_obj.product_id.id
            else:
                filtro['produto_id'] = '%'

            if rel_obj.location_id:
                filtro['local_id'] = rel_obj.location_id.id
            else:
                filtro['local_id'] = '%'

            if rel_obj.company_id:
                filtro['company_id'] = rel_obj.company_id.id
            else:
                filtro['company_id'] = '%'

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            saldo_inicial = {}
            linhas = []
            for produto_id, codigo, produto, local_id, local, data, entrada_saida, entrada, saida, vr_unitario, vr_unitario_custo, quantidade, vr_total, documento in dados:
                linha = DicionarioBrasil()

                if produto_id not in saldo_inicial:
                    saldo_inicial[produto_id] = {}

                if local_id not in saldo_inicial[produto_id]:
                    saldo_inicial[produto_id][local_id] = [D(0), D(0)]

                    filtro['local_id'] = local_id
                    filtro['produto_id'] = produto_id
                    filtro['data_inicial'] = rel_obj.data_inicial

                    sql_ini = '''
                    select
                    cm.quantidade,
                    cm.vr_total
                    from custo_medio({company_id}, {local_id}, {produto_id}) cm
                    --join stock_move m on m.id = cm.move_id
                    --join res_company c on c.id = m.company_id
                    where --cm.product_id = {produto_id}
                    --and cm.location_id = {local_id}
                    --and cm.data < '{data_inicial}'
                    --and cast(c.id as varchar) like '{company_id}'
                    cm.data < '{data_inicial}'
                    order by
                    cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                    '''.format(**filtro)

                    cr.execute(sql_ini)
                    dados_ini = cr.fetchall()
                    if dados_ini:
                        saldo_inicial[produto_id][local_id] = [D(dados[0][0]), D(dados[0][0])]

                linha['produto_id'] = produto_id
                linha['codigo'] = codigo
                linha['produto'] = produto
                linha['quebra_produto'] = '[ ' + codigo + ' ] - ' + produto
                linha['local_id'] = local_id
                linha['local'] = local  # + ' - Saldo inicial: ' + formata_valor(saldo_inicial[produto_id][local_id][0]) + '; valor R$ ' + formata_valor(saldo_inicial[produto_id][local_id][1])
                linha['data'] = parse_datetime(data)
                linha['entrada_saida'] = entrada_saida
                linha['entrada'] = D(entrada)
                linha['saida'] = D(saida)
                linha['vr_unitario'] = D(vr_unitario)
                linha['vr_unitario_custo'] = D(vr_unitario_custo)
                linha['quantidade'] = D(quantidade)
                linha['vr_total'] = D(vr_total)
                linha['documento'] = documento

                linhas.append(linha)

            if not linhas:
                raise osv.except_osv(u'Aviso!', u'Não há dados para impressão!')

            rel = FinanRelatorioAutomaticoRetrato()

            rel.title = u'Movimentação de estoque'

            rel.colunas = [
                ['data', 'D', 10, u'Data', False],
                ['documento', 'C', 80, u'Documento', False],
                ['entrada', 'F', 10, u'Entrada', False],
                ['saida', 'F', 10, u'Saída', False],
                ['vr_unitario', 'F', 10, u'Unitário', False],
                ['vr_unitario_custo', 'F', 10, u'Custo médio', False],
                ['quantidade', 'F', 10, u'Saldo', False],
                ['vr_total', 'F', 10, u'Valor', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)
            rel.band_detail.elements[3].truncate_overflow = True

            rel.grupos = [
                ['quebra_produto', u'Produto', False],
                ['local', u'Local', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)
            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u' - Unidade ' + rel_obj.company_id.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'movimentacao_estoque.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

    def gera_posicao_estoque(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            rel_obj.data_final = parse_datetime(rel_obj.data_final).date()
            rel_obj.data_final += relativedelta(days=+1)
            rel_obj.data_final = str(rel_obj.data_final)

            filtro = {
                'local_id': rel_obj.location_id.id,
                'data_final': rel_obj.data_inicial,
            }

            if rel_obj.product_id:
                filtro['produto_id'] = rel_obj.product_id.id
            else:
                filtro['produto_id'] = '%'

            if rel_obj.company_id:
                filtro['company_id'] = rel_obj.company_id.id
            else:
                filtro['company_id'] = '%'

            if rel_obj.company_id and rel_obj.location_id and rel_obj.product_id:
                sql = u'''
                    select distinct
                        cm.product_id,
                        p.default_code as codigo,
                        p.name_template as produto,
                        cm.data,
                        cm.entrada_saida,
                        cm.move_id
                    from custo_medio({company_id}, {local_id}, {produto_id}) cm
                        join stock_move m on m.id = cm.move_id
                        join res_company c on c.id = m.company_id
                        join product_product p on p.id = cm.product_id
                    where
                        cm.data < '{data_final}'
                    order by
                        cm.data desc, cm.entrada_saida desc, cm.move_id desc;
                        '''

            else:
                sql = u'''
                    select distinct
                        cm.product_id,
                        p.default_code as codigo,
                        p.name_template as produto,
                        cm.data,
                        cm.entrada_saida,
                        cm.move_id
                    from custo_medio() cm
                        join stock_move m on m.id = cm.move_id
                        join res_company c on c.id = m.company_id
                        join product_product p on p.id = cm.product_id
                    where
                        cm.location_id = {local_id}
                        and cm.data < '{data_final}'
                        and cast(cm.product_id as varchar) like '{produto_id}'
                        and cast(c.id as varchar) like '{company_id}'
                    order by
                        cm.data desc, cm.entrada_saida desc, cm.move_id desc;
                        '''

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            linhas = []
            produtos = {}
            ordem = {}
            for produto_id, codigo, produto, data, entrada_saida, move_id in dados:
                linha = DicionarioBrasil()

                filtro['produto_id'] = produto_id

                if produto_id not in produtos:
                    if rel_obj.company_id and rel_obj.location_id:
                        sql_ini = u'''
                        select
                            cm.quantidade,
                            cm.vr_unitario_custo,
                            cm.vr_total
                        from custo_medio({company_id}, {local_id}, {produto_id}) cm
                        where
                            cm.data < '{data_final}'
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                            '''

                    else:
                        sql_ini = u'''
                        select
                            cm.quantidade,
                            cm.vr_unitario_custo,
                            cm.vr_total
                        from custo_medio() cm
                            join stock_move m on m.id = cm.move_id
                            join res_company c on c.id = m.company_id
                        where cm.location_id = {local_id}
                            and cm.data < '{data_final}'
                            and cm.product_id = {produto_id}
                            and cast(c.id as varchar) like '{company_id}'
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                            '''
                    #print(sql_ini.format(**filtro))
                    cr.execute(sql_ini.format(**filtro))
                    dados_ini = cr.fetchall()
                    if dados_ini:
                        quantidade = dados_ini[0][0]
                        vr_unitario_custo = dados_ini[0][1]
                        vr_total = dados_ini[0][2]

                        linha['produto_id'] = produto_id
                        linha['codigo'] = codigo
                        linha['produto'] = produto
                        linha['local'] = rel_obj.location_id.name
                        linha['quantidade'] = D(quantidade)
                        linha['vr_total'] = D(vr_total)
                        linha['vr_unitario_custo'] = D(vr_unitario_custo)

                        #linhas.append(linha)
                        produtos[produto_id] = linha
                        ordem[produto] = produto_id

            #
            # Trata a ordem do relatório
            #
            nomes = ordem.keys()
            nomes.sort()
            for nome in nomes:
                id = ordem[nome]
                linhas.append(produtos[id])

            if not linhas:
                raise osv.except_osv(u'Aviso!', u'Não há dados para impressão!')

            rel = FinanRelatorioAutomaticoRetrato()

            rel.title = u'Posição de estoque'

            rel.colunas = [
                ['codigo', 'C', 15, u'Código', False],
                ['produto', 'C', 60, u'Produto', False],
                ['quantidade', 'F', 10, u'Quantidade', True],
                ['vr_unitario_custo', 'F', 10, u'Custo médio', False],
                ['vr_total', 'F', 10, u'Valor', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['local', u'Local', False],
            #]
            #rel.monta_grupos(rel.grupos)

            rel_obj.data_final = parse_datetime(rel_obj.data_final).date()
            rel_obj.data_final += relativedelta(days=-1)
            rel.band_page_header.elements[-1].text = u'Data ' + formata_data(rel_obj.data_final)
            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u'; Unidade ' + rel_obj.company_id.name
            if rel_obj.location_id:
                rel.band_page_header.height += 7
                rel.band_page_header.elements[-1].text += u'<br/>Local ' + rel_obj.location_id.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'posicao_estoque.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

    #def gera_movimento_estoque(self, cr, uid, ids, context={}):
        #if not ids:
            #return {}

        #id = ids[0]

        #return self._gera_movimentacao_estoque(cr, uid, ids, context=context)

        #rel_obj = self.browse(cr, uid, id)

        #if rel_obj.product_id:
            #rel = Report('Movimento de Estoque', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'movimento_estoque.jrxml')
            #rel.parametros['PRODUCT_ID'] = rel_obj.product_id.id
            #rel.parametros['LOCATION_ID'] = rel_obj.location_id.id
            #rel.parametros['DATA_INICIAL'] = rel_obj.data_inicial
            #rel.parametros['DATA_FINAL'] = rel_obj.data_final

            #pdf, formato = rel.execute()

            #dados = {
                #'nome': u'movimento_estoque.pdf',
                #'arquivo': base64.encodestring(pdf)
            #}

        #else:
            #rel = Report('Posição de Estoque', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'posicao_estoque.jrxml')
            #rel.parametros['LOCATION_ID'] = rel_obj.location_id.id
            #rel.parametros['CATEGORIA'] = rel_obj.category_id.name
            #rel.parametros['DATA_FINAL'] = rel_obj.data_final

            #pdf, formato = rel.execute()

            #dados = {
                #'nome': u'posicao_estoque.pdf',
                #'arquivo': base64.encodestring(pdf)
            #}
        #rel_obj.write(dados)

        #return True

    def gera_listagem_preco_fornecedor(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id

            cr.execute("""
                        select
                        p.default_code as codigo,
                        rp.name as fornecedor,
                        p.name_template as produto,
                        pu.name as unidade,
                        pt.list_price as valor

                        from product_product p
                        join product_template pt on pt.id = p.product_tmpl_id
                        join product_uom pu on pu.id = pt.uom_id

                        join product_supplierinfo ps on ps.product_id = p.id
                        join res_partner rp on rp.id = ps.name

                        order by
                        rp.name, p.name_template ;
                        """)

            dados = cr.fetchall()
            print(dados)

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for codigo, fornecedor, produto, unidade,valor in dados:
                linha = DicionarioBrasil()
                linha['codigo'] = codigo
                linha['fornecedor'] = fornecedor
                linha['produto'] = produto
                linha['unidade'] = unidade
                linha['valor'] = valor
                linhas.append(linha)


            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Preço por Fornecedor'
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['produto' , 'C', 40, u'Produto', False],
                ['unidade' , 'C', 3, u'UN', False],
                ['valor' , 'F', 10, u'Valor', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['fornecedor', u'Fornecedor', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'listagem_produto_fornecedor.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_panoramico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_final = parse_datetime(rel_obj.data_final).date()

        lista_location_ids = []
        if len(rel_obj.location_ids):

            for location_id in rel_obj.location_ids:
                lista_location_ids.append(location_id.id)

        rel = Report('Relatório Panorâmico de Estoque', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'panoramico_estoque.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)

        if len(rel_obj.location_ids) > 0:
            rel.parametros['LOCAL_ID'] = 'and es.location_id in ' +  str(tuple(lista_location_ids)).replace(',)', ')')

        if rel_obj.product_id.id:
            rel.parametros['PRODUTO_ID'] = str(rel_obj.product_id.id)
        else:
            rel.parametros['PRODUTO_ID'] = '%'

        rel.parametros['DATA_FINAL'] = str(data_final)[:10]

        rel.outputFormat = rel_obj.formato


        pdf, formato = rel.execute()

        dados = {
            'nome': u'panoramico_estoque_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_tabela_preco(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            variants = rel_obj.variants

            sql = """
                        select
                        p.default_code as codigo,
                        p.name_template as produto,
                        p.variants,
                        pu.name as unidade,
                        pt.list_price as valor

                        from product_product p
                        join product_template pt on pt.id = p.product_tmpl_id
                        join product_uom pu on pu.id = pt.uom_id

                        join res_company c on c.id = pt.company_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                        where
                        (
                            c.id = """ + str(company_id) + """
                            or cc.id = """ + str(company_id) + """
                            or ccc.id = """ + str(company_id) + """
                        )
                        """

            if variants:
                sql += """
                        and p.variants like '%""" + variants + """%'"""

            sql += """
                        order by
                        p.variants, p.default_code ;"""

            cr.execute(sql)
            dados = cr.fetchall()
            print(dados)

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for codigo, produto, variants, unidade, valor in dados:
                linha = DicionarioBrasil()
                linha['codigo'] = codigo
                linha['produto'] = produto
                linha['variants'] = variants
                linha['unidade'] = unidade
                linha['valor'] = valor
                linhas.append(linha)


            rel = FinanRelatorioAutomaticoRetrato()
            rel.cpc_minimo_detalhe = 4.0
            rel.title = u'Tabela de Preços'
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['produto' , 'C', 40, u'Produto', False],
                ['unidade' , 'C', 3, u'UN', False],
                ['valor' , 'F', 10, u'Valor', False],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['variants', u'Subtipo', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'tabela_precos.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_listagem_estoque(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            company_id = rel_obj.company_id.id
            variants = rel_obj.variants

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Listagem de Estoque'
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['produto' , 'C', 40, u'Produto', False],
                ['unidade' , 'C', 5, u'UN', False],
                ['quantidade' , 'F', 15, u'Qtd.', True],
                ['valor', 'F', 15, u'Valor Unit.', True],
                ['total', 'F', 15, u'Valor Total.', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['variants', u'Subtipo', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql = """
                    select
                        p.id

                    from product_product p
                        join product_template pt on pt.id = p.product_tmpl_id
                        join product_uom pu on pu.id = pt.uom_id
                        join res_company c on c.id = pt.company_id
                        left join res_company cc on cc.id = c.parent_id
                        left join res_company ccc on ccc.id = cc.parent_id
                    where
                        (
                            c.id = """ + str(company_id) + """
                            or cc.id = """ + str(company_id) + """
                            or ccc.id = """ + str(company_id) + """
                        )
                        """

            if variants:
                sql += """
                        and p.variants like '%""" + variants + """%'"""

            sql += """
                        order by
                        p.variants, p.default_code ;"""

            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')


            produtos_ids = []
            for ret in dados:
                produtos_ids.append(ret[0])


            produtos_objs = self.pool.get('product.product').browse(cr, uid, produtos_ids)

            linhas = []
            for produto_obj in produtos_objs:
                linha = DicionarioBrasil()
                linha['codigo'] = produto_obj.default_code
                linha['produto'] = produto_obj.name_template
                linha['variants'] = produto_obj.variants
                linha['unidade'] = produto_obj.product_tmpl_id.uom_id.name

                quantidade = D(produto_obj.qty_available).quantize(D('0.01'))
                valor_unitario = D(produto_obj.product_tmpl_id.standard_price).quantize(D('0.01'))

                linha['quantidade'] = quantidade
                linha['valor'] = valor_unitario
                linha['total'] = quantidade * valor_unitario
                linhas.append(linha)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'listagem_estoque.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_custo_unidade_local_antigo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            lista_location_ids = []
            #
            # Primeiro, buscamos os locais e produtos que serão considerados
            #
            if len(rel_obj.location_ids):

                for location_id in rel_obj.location_ids:
                    lista_location_ids.append(location_id.id)

            sql = """
                select
                    ees.company_id,
                    c.name as empresa,
                    ll.id as local_pai_id,
                    ll.name as local_pai,
                    ees.location_id,
                    l.name as local,
                    ees.product_id,
                    p.name_template as produto

                from estoque_entrada_saida ees
                    join res_company c on c.id = ees.company_id
                    join stock_location l on l.id = ees.location_id
                    left join stock_location ll on ll.id = l.location_id
                    join product_product p on p.id = ees.product_id

                where
                    (ees.company_id = {company_id} or c.parent_id = {company_id})
                    and ees.data <= '{data_final}'
                    and ll.id not in (17, 2)  -- Locais virtuais e de parceiros
                    and l.active = True
                    {filtro_adicional}

                group by
                    ees.company_id,
                    c.name,
                    ll.id,
                    ll.name,
                    ees.location_id,
                    l.name,
                    ees.product_id,
                    p.name_template

                order by
                    c.name,
                    ll.name,
                    l.name,
                    p.name_template;
            """

            filtro = {
                'company_id': rel_obj.company_id.id,
                'data_final': rel_obj.data_final,
                'filtro_adicional': '',
            }


            if len(rel_obj.location_ids) > 0:
                filtro['filtro_adicional'] = 'and ees.location_id in ' +  str(tuple(lista_location_ids)).replace(',)', ')')

            sql = sql.format(**filtro)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            #
            # Agora, acumulamos o custo do estoque em cada caso
            #
            linhas = []
            custo_locacao = {}
            custo_venda = {}
            produtos_acumulados = {}
            for company_id, unidade, local_pai_id, local_pai, location_id, local, product_id, produto in dados:

                location_obj = self.pool.get('stock.location').browse(cr, uid , location_id)

                sql = """
                    select
                        cm.quantidade,
                        cm.vr_unitario_custo,
                        cm.vr_total
                    from custo_medio({company_id}, {local_id}, {produto_id}) cm
                    where
                        cm.data <= '{data_final}'
                    order by
                        cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                """

                filtro = {
                    'company_id': company_id,
                    'local_id': location_id,
                    'produto_id': product_id,
                    'data_final': rel_obj.data_final,
                }

                sql = sql.format(**filtro)

                cr.execute(sql)
                dados_custo = cr.fetchall()

                if len(dados_custo) == 0:
                    continue
                quantidade = dados_custo[0][0]
                vr_unitario_custo = dados_custo[0][1]
                vr_total = dados_custo[0][2]
                print(vr_unitario_custo)

                if location_obj.location_custo_id:

                    location_custo_id = location_obj.location_custo_id.id

                    sql = """
                        select
                            cm.vr_unitario_custo
                        from custo_medio({company_id}, {local_id}, {produto_id}) cm
                        where
                            cm.data <= '{data_final}'
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                    """

                    filtro = {
                        'company_id': company_id,
                        'local_id': location_custo_id,
                        'produto_id': product_id,
                        'data_final': rel_obj.data_final,
                    }

                    sql = sql.format(**filtro)
                    cr.execute(sql)
                    dados_custo = cr.fetchall()
                    if len(dados_custo):
                        vr_unitario_custo = dados_custo[0][0]

                if location_id == 27:
                    custo_locacao[product_id] = D(vr_unitario_custo or 0)
                elif location_id == 22:
                    custo_venda[product_id] = D(vr_unitario_custo or 0)

                if vr_total == 0:
                    if 'usado' in local_pai.lower():
                        if product_id in custo_locacao:
                            vr_unitario_custo = custo_locacao[product_id]

                        elif product_id in custo_venda:
                            vr_unitario_custo = custo_venda[product_id]

                    elif product_id in custo_venda:
                        vr_unitario_custo = custo_venda[product_id]

                    elif product_id in custo_locacao:
                        vr_unitario_custo = custo_locacao[product_id]

                    vr_total = D(quantidade or 0) * vr_unitario_custo

                print(unidade, local, produto, vr_total)

                if vr_total <= 0:
                    continue

                #
                # Agrupando o relatório por local pai, para os casos
                # em que o pai não é o localizações físicas
                #
                linha = DicionarioBrasil()
                linha['unidade'] = unidade

                if local_pai_id != 13:
                    linha['local_pai'] = local_pai
                    linha['local_pai_id'] = local_pai_id
                    linha['local'] = local
                    linha['local_id'] = location_id
                else:
                    linha['local_pai'] = local
                    linha['local_pai_id'] = location_id
                    linha['local'] = local
                    linha['local_id'] = location_id

                linha['product_id'] = product_id
                linha['produto'] = produto
                linha['quantidade'] = D(quantidade or 0)
                linha['vr_unitario_custo'] = D(vr_unitario_custo or 0)
                linha['vr_total'] = D(vr_total or 0)

                linhas.append(linha)
                if product_id in produtos_acumulados:
                    linha_produto = produtos_acumulados[product_id]
                else:
                    linha_produto = DicionarioBrasil()
                    linha_produto['unidade'] = False
                    linha_produto['local_pai'] = False
                    linha_produto['local_pai_id'] = False
                    linha_produto['local'] = False
                    linha_produto['local_id'] = False
                    linha_produto['product_id'] = product_id
                    linha_produto['produto'] = produto
                    linha_produto['quantidade'] = D(0)
                    linha_produto['vr_unitario_custo'] = D(vr_unitario_custo or 0)
                    linha_produto['vr_total'] = D(0)
                    produtos_acumulados[product_id] = linha_produto

                if quantidade > 0:
                    linha_produto.quantidade += D(quantidade)
                else:
                    linha_produto.quantidade += 1

                linha_produto.vr_total = linha_produto.quantidade * linha_produto.vr_unitario_custo

            for product_id in produtos_acumulados:
                linhas.append(produtos_acumulados[product_id])

            #
            # Agora, filtra as linhas que não deverão constar no relatório
            #

            if len(linhas) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            if not rel_obj.location_id:
                linhas_imprime = linhas
            else:
                linhas_imprime = []
                for linha in linhas:
                    if linha.local_pai_id != rel_obj.location_id.id and linha.local_id != rel_obj.location_id.id:
                        continue

                    linhas_imprime.append(linha)

            if rel_obj.analitico or rel_obj.acumula_produto:
                rel = FinanRelatorioAutomaticoRetrato()
                rel.title = u'Panorâmico de Estoque (custo)'

                if rel_obj.acumula_produto:
                    linhas_produto = OrderedDict()

                    for linha in linhas_imprime:
                        if linha.local_pai_id not in linhas_produto:
                            linhas_produto[linha.local_pai_id] = OrderedDict()

                        if linha.product_id not in linhas_produto[linha.local_pai_id]:
                            linhas_produto[linha.local_pai_id][linha.product_id] = linha
                        else:
                            linhas_produto[linha.local_pai_id][linha.product_id].quantidade += linha.quantidade
                            linhas_produto[linha.local_pai_id][linha.product_id].vr_total += linha.vr_total
                            linhas_produto[linha.local_pai_id][linha.product_id].vr_unitario_custo = linhas_produto[linha.local_pai_id][linha.product_id].vr_total / linhas_produto[linha.local_pai_id][linha.product_id].quantidade

                    nova_linhas_imprime = []
                    for local_pai_id in linhas_produto:
                        for product_id in linhas_produto[local_pai_id]:
                            nova_linhas_imprime.append(linhas_produto[local_pai_id][product_id])

                    linhas_imprime = nova_linhas_imprime

                    rel.colunas = [
                        #['unidade' , 'C', 60, u'Unidade', False],
                        #['local_pai' , 'C', 40, u'Local pai', False],
                        ['produto' , 'C', 60, u'Produto', False],
                        ['quantidade' , 'F', 10, u'Quantidade', False],
                        ['vr_unitario_custo' , 'F', 10, u'Custo un.', False],
                        ['vr_total' , 'F', 10, u'Custo', True],
                    ]

                else:
                    rel.colunas = [
                        #['unidade' , 'C', 60, u'Unidade', False],
                        #['local_pai' , 'C', 40, u'Local pai', False],
                        #['local' , 'C', 60, u'Local', False],
                        ['produto' , 'C', 60, u'Produto', False],
                        ['quantidade' , 'F', 10, u'Quantidade', False],
                        ['vr_unitario_custo' , 'F', 10, u'Custo un.', False],
                        ['vr_total' , 'F', 10, u'Custo', True],
                    ]
                rel.monta_detalhe_automatico(rel.colunas)
                rel.band_detail.elements[0].truncate_overflow = True

            else:
                rel = FinanRelatorioAutomaticoRetrato()
                rel.title = u'Panorâmico de Estoque (custo)'

                rel.colunas = [
                    #['unidade' , 'C', 60, u'Unidade', False],
                    #['local_pai' , 'C', 40, u'Local', False],
                    #['produto' , 'C', 60, u'Produto', False],
                    #['quantidade' , 'F', 10, u'Quantidade', False],
                    #['vr_unitario_custo' , 'F', 10, u'Custo un.', False],
                    ['vr_total' , 'F', 10, u'Custo', True],
                ]
                rel.monta_detalhe_automatico(rel.colunas)


            rel.grupos = [
                ['unidade', u'Unidade', True],
                ['local_pai', u'Local', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Grupo/Unidade ' + rel_obj.company_id.name + u' até ' + formata_data(rel_obj.data_final)

            #
            # Relatório sintético
            # não tem detalhe
            # o cabeçalho do último grupo não precisa aparecer
            #
            if not rel_obj.analitico:
                rel.band_detail.elements = []
                rel.band_detail.height = 0
                rel.groups[-1].band_header.elements = []
                rel.groups[-1].band_header.height = 0

            pdf = gera_relatorio(rel, linhas_imprime)

            dados = {
                'nome': 'custo_estoque_unidade_local.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True

    def gera_custo_unidade_local(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        
        item_pool = self.pool.get('custo.unidade.local.item')
        print(context)
        location_ids = context['location_ids']
        self.write(cr, uid, ids, {'location_ids': location_ids})
        
        for rel_obj in self.browse(cr, uid, ids):            
            
            cr.execute('delete from custo_unidade_local_item where relatorio_id = {id}'.format(id=rel_obj.id))

            lista_location_ids = []
            #
            # Primeiro, buscamos os locais e produtos que serão considerados
            #
            if len(location_ids):

                for location_id in location_ids[0][2]:
                    lista_location_ids.append(location_id)

            sql = """
                select
                    ees.company_id,
                    c.name as empresa,
                    ll.id as local_pai_id,
                    ll.name as local_pai,
                    ees.location_id,
                    l.name as local,
                    ees.product_id,
                    p.name_template as produto

                from estoque_entrada_saida ees
                    join res_company c on c.id = ees.company_id
                    join stock_location l on l.id = ees.location_id
                    left join stock_location ll on ll.id = l.location_id
                    join product_product p on p.id = ees.product_id

                where
                    (ees.company_id = {company_id} or c.parent_id = {company_id})
                    and ees.data <= '{data_final}'
                    and ll.id not in (17, 2)  -- Locais virtuais e de parceiros
                    and l.active = True
                    {filtro_adicional}

                group by
                    ees.company_id,
                    c.name,
                    ll.id,
                    ll.name,
                    ees.location_id,
                    l.name,
                    ees.product_id,
                    p.name_template

                order by
                    c.name,
                    ll.name,
                    l.name,
                    p.name_template;
            """

            filtro = {
                'company_id': rel_obj.company_id.id,
                'data_final': rel_obj.data_final,
                'filtro_adicional': '',
            }


            if len(rel_obj.location_ids) > 0:
                filtro['filtro_adicional'] = 'and ees.location_id in ' +  str(tuple(lista_location_ids)).replace(',)', ')')

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            #
            # Agora, acumulamos o custo do estoque em cada caso
            #
            linhas = []
            custo_locacao = {}
            custo_venda = {}
            produtos_acumulados = {}
            for company_id, unidade, local_pai_id, local_pai, location_id, local, product_id, produto in dados:
                
                if product_id == 483:
                    print()

                location_obj = self.pool.get('stock.location').browse(cr, uid , location_id)

                sql = """
                    select
                        cm.quantidade,
                        cm.vr_unitario_custo,
                        cm.vr_total
                    from custo_medio({company_id}, {local_id}, {produto_id}) cm
                    where
                        cm.data <= '{data_final}'
                    order by
                        cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                """

                filtro = {
                    'company_id': company_id,
                    'local_id': location_id,
                    'produto_id': product_id,
                    'data_final': rel_obj.data_final,
                }

                sql = sql.format(**filtro)

                cr.execute(sql)
                dados_custo = cr.fetchall()

                if len(dados_custo) == 0:
                    continue
                quantidade = dados_custo[0][0]
                vr_unitario_custo = dados_custo[0][1]
                vr_total = dados_custo[0][2]
                #print(vr_unitario_custo)

                if location_obj.location_custo_id:

                    location_custo_id = location_obj.location_custo_id.id

                    sql = """
                        select
                            cm.vr_unitario_custo
                        from custo_medio({company_id}, {local_id}, {produto_id}) cm
                        where
                            cm.data <= '{data_final}'
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
                    """

                    filtro = {
                        'company_id': company_id,
                        'local_id': location_custo_id,
                        'produto_id': product_id,
                        'data_final': rel_obj.data_final,
                    }

                    sql = sql.format(**filtro)
                    cr.execute(sql)
                    dados_custo = cr.fetchall()
                    if len(dados_custo):
                        vr_unitario_custo = dados_custo[0][0]                        

                if location_id == 27:
                    custo_locacao[product_id] = D(vr_unitario_custo or 0)
                elif location_id == 22:
                    custo_venda[product_id] = D(vr_unitario_custo or 0)

                if vr_total == 0:
                    if 'usado' in local_pai.lower():
                        if product_id in custo_locacao:
                            vr_unitario_custo = custo_locacao[product_id]

                        elif product_id in custo_venda:
                            vr_unitario_custo = custo_venda[product_id]

                    elif product_id in custo_venda:
                        vr_unitario_custo = custo_venda[product_id]

                    elif product_id in custo_locacao:
                        vr_unitario_custo = custo_locacao[product_id]

                vr_total = D(quantidade or 0) * vr_unitario_custo

                #print(unidade, local, produto, vr_total)

                if vr_total <= 0:
                    continue

                #
                # Agrupando o relatório por local pai, para os casos
                # em que o pai não é o localizações físicas
                #
                linha = DicionarioBrasil()
                linha['relatorio_id'] = rel_obj.id
                linha['company_id'] = company_id
                linha['data_final'] = rel_obj.data_final

                if local_pai_id != 13:
                    linha['local_pai'] = local_pai
                    linha['local_pai_id'] = local_pai_id
                    linha['local'] = local
                    linha['local_id'] = location_id
                else:
                    linha['local_pai'] = local
                    linha['local_pai_id'] = location_id
                    linha['local'] = local
                    linha['local_id'] = location_id

                linha['product_id'] = product_id
                linha['produto'] = produto
                linha['quantidade'] = D(quantidade or 0)
                linha['vr_unitario_custo'] = D(vr_unitario_custo or 0)
                linha['vr_total'] = D(vr_total or 0)

                linhas.append(linha)
                
            if len(linhas) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')
                
            for linha in linhas:                
                item_pool.create(cr, uid, linha)
                    
                                
        return True
            
    
    def gera_relatorio_custo_unidade_local(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        
        for rel_obj in self.browse(cr, uid, ids):
              
            rel = Report('Relatório Panorâmico de Estoque Custo Unidade Local', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'estoque_custo_unidade_local.jrxml')     
            rel.parametros['RELATORIO_ID'] = rel_obj.id           
            rel.outputFormat = rel_obj.formato

            pdf, formato = rel.execute()

            dados = {
                'nome': u'custo_estoque_unidade_local_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)        
                                
        return True
    
    def gera_relatorio_projeto_orcamento_compras(self, cr, uid, ids, context={}):
        
        product_pool = self.pool.get('product.product').broswe(cr,ids)
        
        product_ids = product_pool.search(cr,uid)        
        
        linhas = []
        for product_obj in product_pool.browse(cr,uid, product_ids):        
        
            linha = DicionarioBrasil()
            linha['codigo'] = product_obj.default_code
            linha['descricao'] = product_obj.name
            linha['nome_generio'] = product_obj.nome_generio
            linha['subtipos'] = product_obj.variants
            
            if product_obj.state == 'draft':
                linha['situacao'] = 'Em Desenvolvimento'                               
            elif product_obj.state == 'sellable':
                linha['situacao'] = 'Normal'                
            elif product_obj.state == 'end':
                linha['situacao'] = 'Fim do ciclo de vida'                
            else:
                linha['situacao'] = 'Obsoleto'
                
            linha['unidade_medida'] = product_obj.uom_id.name
            
            linha['vr_unitario_venda'] = D(product_obj.custo_ultima_compra or 0)
            linha['vr_unitario_locacao'] = D(product_obj.custo_ultima_compra_locacao or 0)
            linhas.append(linha)
        
        dados = {
            'titulo': u'Produtos em Estoque',
            'data': formata_data(agora()),
            'linhas': linhas,
        }

        nome_arquivo = JASPER_BASE_DIR + 'listagem_produtos_cadastrados.odt'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)

        dados = {
            'nome': 'listagem_produtos_cadastrados.xlsx',
            'arquivo': planilha
        }
        rel_obj.write(dados)

        return True

estoque_relatorio()


class custo_unidade_local_item(osv.osv_memory):
    _name = 'custo.unidade.local.item'
    _description = u'Custo Unidade local Item'   
    
    _columns = {
        'relatorio_id': fields.many2one('estoque.relatorio', u'Relatorio de estoque'),        
        'company_id': fields.many2one('res.company', u'Empresa'),
        'local_pai_id': fields.many2one('stock.location', u'Local do Estoque Pai'),                
        'local_id': fields.many2one('stock.location', u'Local do Estoque'),        
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),        
        'product_id': fields.many2one('product.product', u'Produto'),        
        'quantidade': fields.float(u'Quantidade'),
        'vr_unitario_custo': fields.float(u'Vlr. Unitário de Custo'),
        'vr_total': fields.float(u'Vlr. Unitário de Custo'),        
    }
    
custo_unidade_local_item() 
