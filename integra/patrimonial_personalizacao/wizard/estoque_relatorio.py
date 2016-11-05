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

SALDO = [
    ('T', u'Todos'),      
    ('S', u'Somente com saldo'),      
    ('Z', u'Somente saldo zero'),      
]




class estoque_relatorio(osv.osv_memory):
    _inherit = 'estoque.relatorio'
    _name = 'estoque.relatorio'


    _columns = {
        'operacao_id': fields.many2one('stock.operacao', u'Operação de Estoque'),        
        'sped_operacao_id': fields.many2one('sped.operacao', u'Operação Nf'),
        'saldo_zero': fields.selection(SALDO,u'Saldo Zero'),
        'vendedor_id': fields.many2one('res.users', u'Vendedor')               
    }

    _defaults = {

    }


    def movimentacao_interna_operacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):            
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            date_inicial = str(data_inicial)[:10]
            date_final = str(data_final)[:10]            
            
            if rel_obj.operacao_id and rel_obj.sped_operacao_id.id:
                raise osv.except_osv(u'Erro!', u'Escolha somente uma operação!!')               
                

            if rel_obj.operacao_id:
                operacao_id = rel_obj.operacao_id.id
                operacao_nome = rel_obj.operacao_id.nome
                local_id = rel_obj.operacao_id.location_id.id
                sql = """                
                    select
                        c.id as company_id,
                        rp.name as empresa,
                        0 as nf,
                        pp.id as produto_id,
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
                    where
                        sp.operacao_id = '{operacao}'
                        and sm.date between '{data_inicial}' and '{data_final}'
                    group by
                        c.id,    
                        rp.name,
                        pp.id,
                        pp.name_template,
                        pp.default_code,
                        pu.name
                    order by
                        rp.name, pp.name_template;"""
                
            else:    
                operacao_id = rel_obj.sped_operacao_id.id
                operacao_nome = rel_obj.sped_operacao_id.nome
                local_id = rel_obj.sped_operacao_id.stock_operacao_id.location_id.id
                
                sql = """
                    select 
                        c.id as company_id,
                        rp.name as empresa,
                        sd.numero as nf,
                        pp.id as produto_id,
                        pp.name_template as produto,
                        pp.default_code,
                        pu.name,
                        sum(item.quantidade) as quantidade
                    from sped_documento sd
                        join sped_documentoitem item on item.documento_id = sd.id
                        join sped_operacao op on op.id = sd.operacao_id    
                        join product_product pp on pp.id = item.produto_id
                        join product_template pt on pt.id = pp.product_tmpl_id
                        left join product_uom pu on pu.id = pt.uom_id
                        join res_company c on c.id = sd.company_id
                        join res_partner rp on rp.id = c.partner_id                        
                    where 
                        op.id = '{operacao}'
                        and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'                    
                    group by
                        c.id,
                        rp.name,
                        sd.numero,
                        pp.id,
                        pp.name_template,
                        pp.default_code,
                        pu.name
    
                    order by
                        rp.name, pp.name_template ;"""

            cr.execute(sql.format(operacao=str(operacao_id),data_inicial=data_inicial, data_final=data_final))

            dados = cr.fetchall()
            linhas = []

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem dados nos parâmetros informados!')

            for company_id, empresa, nf, produto_id, produto, codigo, unidade, quantidade in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['codigo'] = codigo
                linha['nf'] = '' if nf == 0 else str(nf)  
                linha['produto'] = produto
                linha['unidade'] = unidade
                linha['quantidade'] = quantidade
                
                sql_custo = u'''
                    select
                        cm.quantidade,
                        cm.vr_unitario_custo,
                        cm.vr_total
                    from custo_medio({company_id}, {local_id}, {produto_id}) cm
                    where
                        cast(cm.data at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) <= '{data_final}'
                    order by
                        cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;'''
                cr.execute(sql_custo.format(company_id=company_id,local_id=local_id, produto_id=produto_id,data_final=data_final))
                dados_custo = cr.fetchall()
                if len(dados_custo) > 0:
                    linha['custo_medio'] = dados_custo[0][0]   
                else:
                    linha['custo_medio'] = 0                                                                                         
                linhas.append(linha)

            rel = RHRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Movimentação por Operação'
            rel.colunas = [
                ['codigo' , 'C', 8, u'Código', False],
                ['produto' , 'C', 50, u'Produto', False],
                ['unidade' , 'C', 5, u'UN', False],
                ['nf' , 'C', 10, u'Nota Fiscal', False],
                ['quantidade' , 'F', 10, u'Quantidade', True],
                ['custo_medio' , 'F', 10, u'Custo Médio', True],
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
            company_id = rel_obj.company_id.id
            
            if rel_obj.formato == 'pdf':
                formato = 'pdf'
                nome = u'Estoque_minimo.pdf'
            else:
                formato = 'xlsx'   
                nome = u'Estoque_minimo.xlsx'

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
                        and sw.company_id = {company_id}

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
            sql = sql.format(location_id=location_id,company_id=company_id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            product_pool = self.pool.get('product.product')
            
            total_estoque_minimo = D(0)
            total_na_mao = D(0)
            total_disponivel = D(0)
            total_compra = D(0)
            linhas= []
            for product_id, estoque_minimo in dados:
                
                product_obj = product_pool.browse(cr, uid, product_id)
                linha = DicionarioBrasil()
                linha['codigo'] = product_obj.default_code or ''
                linha['produto'] = product_obj.name or ''
                linha['variants'] = product_obj.variants or ''
                linha['estoque_minimo'] = D(estoque_minimo or 0)
                linha['na_mao'] = D(product_obj.qty_available or 0)
                linha['disponivel'] = D(product_obj.virtual_available or 0)
                quantidade_compra = D(product_obj.qty_available or 0) - D(estoque_minimo or 0)
                
                if quantidade_compra >= 0:
                    quantidade_compra = 0
                else:
                    quantidade_compra *= -1
                    
                linha['quantidade_compra'] = quantidade_compra
                linhas.append(linha)
                
            for linha in linhas:                
                total_estoque_minimo += linha.estoque_minimo
                total_na_mao += linha.na_mao
                total_disponivel += linha.disponivel                
                total_compra += linha.quantidade_compra                
                linha.estoque_minimo = formata_valor(linha.estoque_minimo) 
                linha.na_mao = formata_valor(linha.na_mao)
                linha.disponivel = formata_valor(linha.disponivel)
                linha.quantidade_compra = formata_valor(linha.quantidade_compra)
            
            dados = {
                'titulo': u'Estoque Minímo',                
                'empresa': rel_obj.company_id.partner_id.name,
                'local': rel_obj.location_id.name,
                'data': formata_data(agora()),
                'linhas': linhas,
                'total_estoque_minimo': formata_valor(total_estoque_minimo),
                'total_na_mao': formata_valor(total_na_mao),
                'total_disponivel': formata_valor(total_disponivel),
                'total_compra': formata_valor(total_compra),
            }
    
            nome_arquivo = JASPER_BASE_DIR + 'estoque_minimo.ods'
    
            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados, formato=formato)
    
            dados = {
                'nome': nome,
                'arquivo': planilha
            }
            rel_obj.write(dados)    
            
            return True
        
    def gera_relatorio_ordem_entrega(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):            
            company_id = rel_obj.company_id.id
            
            if rel_obj.formato == 'pdf':
                formato = 'pdf'
                nome = u'Estoque_minimo.pdf'
            else:
                formato = 'xlsx'   
                nome = u'Estoque_minimo.xlsx'

            sql = """
                select 
                    rp.name as empresa,
                    sp.name as referencia,
                    sp.date,
                    parc.name as parceiro,
                    sp.origin,
                    case
                    when sp.state = 'draft' then 'Novo'
                    when sp.state = 'confirmed' then 'Aguardando'
                    when sp.state = 'assigned' then 'Pronto'
                    when sp.state = 'done' then 'Concluido'
                    when sp.state = 'cancel' then 'Cancelado'
                    end as status,
                    sp.saldo_zero,
                    v.name as vendedor,
                    so.nome as operacao
                from stock_picking sp
                join res_company c on c.id = sp.company_id
                join res_partner rp on rp.id = c.partner_id
                join res_partner parc on parc.id = sp.partner_id
                left join stock_operacao so on so.id = sp.operacao_id
                left join res_users v on v.id = sp.vendedor_id
                    
                where 
                    cast(sp.date at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '2016-10-01' and '2016-10-31'
                    and (
                        c.id = {company_id}
                        or c.parent_id = {company_id}
                    )"""
            if rel_obj.operacao_id:
                sql +="""
                    and so.id = """ + str(rel_obj.operacao_id.id)
                
            if rel_obj.saldo_zero == 'S':
                sql +="""
                    and sp.saldo_zero = true"""
                    
                if rel_obj.vendedor_id:
                    sql +="""
                        and v.id = """ + str(rel_obj.vendedor_id.id)   
                        
            elif rel_obj.saldo_zero == 'Z':
                sql +="""
                    and coalesce(sp.saldo_zero, False) = False"""
                    
            sql += """
                order by 
                    rp.name, sp.name;"""
                                    
            sql = sql.format(company_id=company_id, data_inicial=rel_obj.data_inicial,data_final=rel_obj.data_final)
            
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')
            linhas = []
            for empresa, referencia, data, parceiro, origin, state, saldo_zero, vendedor, operacao in dados:
                
               
                linha = DicionarioBrasil()
                linha['empresa'] = empresa 
                linha['referencia'] = referencia
                linha['data'] = formata_data(data)
                linha['parceiro'] = parceiro
                linha['origin'] = origin
                linha['state'] = state
                linha['saldo_zero'] = 'X' if saldo_zero else ' '
                linha['vendedor'] = vendedor
                linha['operacao'] = operacao
                linhas.append(linha)               
                
               
            
            dados = {
                'titulo': u'Relatório Ordem de Entrega',                
                'empresa': rel_obj.company_id.partner_id.name,
                'data': formata_data(agora()),
                'data_inicial': formata_data(rel_obj.data_inicial),
                'data_final': formata_data(rel_obj.data_final),
                'linhas': linhas,
                'local': '',
                'vendedor': '',                
            }
            
            if rel_obj.operacao_id:
                dados['local'] = rel_obj.location_id.name
            
            if rel_obj.vendedor_id:
                dados['vendedor'] = rel_obj.vendedor_id.name
            
            nome = u'Ordem_Entrega.' + formato
            nome_arquivo = JASPER_BASE_DIR + 'estoque_ordem_entrega.ods'
    
            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados, formato=formato)
    
            dados = {
                'nome': nome,
                'arquivo': planilha
            }
            rel_obj.write(dados)    
            
            return True



estoque_relatorio()
