# -*- coding: utf-8 -*-

import os
from osv import fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from finan.wizard.relatorio import *
from pybrasil.data import parse_datetime, hoje, agora, formata_data
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
import csv

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

TIPO = (
    ('P', u'Prospecto'),
    ('V', u'Venda/orçamento'),
    ('O', u'Ordem de serviço'),
)

SITUACAO_ETAPA = (
    ('V', u'Venda'),
    ('L', u'Locação'),
)

ORDEM = (
    ('mes', 'Mês'),
)


class sale_relatorio(osv.osv_memory):
    _name = 'sale.relatorio'
    _description = u'Relatórios Vendas e OSs'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'etapa_id': fields.many2one('sale.etapa', u'Etapa'),
        'tipo': fields.selection(TIPO, u'Tipo'),
        'tipo_os_id': fields.many2one('sale.tipo.os', u'Tipo da OS'),
        'pricelist_id': fields.many2one('product.pricelist', u'Tipo de orçamento'),
        'etapa_ids': fields.many2many('sale.etapa','sale_relatorio_etapa', 'relatorio_id', 'etapa_id', u'Etapas'),        
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'rentabilidade': fields.boolean(u'Listar Rentabilidade?'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'nome': '',
        'formato': 'pdf',        
    }

    def gera_relatorio_venda_os(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            so.name as numero,
            so.date_order as data,
            c.name as empresa,
            et.nome as etapa,
            p.name as cliente,
            v.name as vendedor,
            pp.name as tipo_orcamento,
            e.nome as etapa,
            sto.nome as tipo_os,
            coalesce(so.vr_total_produtos, 0) as valor_produtos,
            coalesce(so.vr_total_servicos, 0) as valor_servicos,
            coalesce(so.vr_total_mensalidades, 0) as valor_mensalidades,
            coalesce(so.vr_mensal_total, 0) as valor_mensal

        from
            sale_order so
            join sale_etapa et on et.id = so.etapa_id
            join res_company c on c.id = so.company_id
            join res_partner p on p.id = so.partner_id
            join res_users v on v.id = so.user_id
            join product_pricelist pp on pp.id = so.pricelist_id
            join sale_etapa e on e.id = so.etapa_id
            join sale_tipo_os sto on sto.id = so.tipo_os_id

        where
            cast(so.date_order at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
            and e.tipo = '{tipo}'
        """

        filtro = {
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
            'tipo': rel_obj.tipo or 'O',
        }

        if rel_obj.company_id:
            filtro['company_id'] = rel_obj.company_id.id

            sql += """
            and c.id = {company_id}
            """

        if rel_obj.partner_id:
            filtro['partner_id'] = rel_obj.partner_id.id

            sql += """
            and p.id = {partner_id}
            """

        if rel_obj.pricelist_id:
            filtro['pricelist_id'] = rel_obj.pricelist_id.id

            sql += """
            and pp.id = {pricelist_id}
            """

        if rel_obj.tipo_os_id:
            filtro['tipo_os_id'] = rel_obj.tipo_os_id.id

            sql += """
            and to.id = {tipo_os_id}
            """

        if rel_obj.etapa_id:
            filtro['etapa_id'] = rel_obj.etapa_id.id

            sql += """
            and e.id = {etapa_id}
            """

        sql += """
            order by
                to_char(cast(so.date_order at time zone 'UTC' at time zone 'America/Sao_Paulo' as date), 'YYYY-MM'),
                pp.name,
                e.nome,
                so.name
        """

        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        for numero, data, empresa, cliente, vendedor, tipo_orcamento, etapa, tipo_os, vr_produtos, vr_servicos, vr_mensalidades, vr_mensal in dados:
            linha = DicionarioBrasil()
            linha['numero'] = numero
            linha['data'] = parse_datetime(data)
            linha['empresa'] = empresa
            linha['cliente'] = cliente
            linha['vendedor'] = vendedor
            linha['tipo_orcamento'] = tipo_orcamento
            linha['etapa'] = etapa
            linha['tipo_os'] = tipo_os
            linha['vr_produtos'] = D(vr_produtos or 0)
            linha['vr_servicos'] = D(vr_servicos or 0)
            linha['vr_total'] = D(vr_servicos or 0) + D(vr_produtos or 0)
            linha['vr_mensalidades'] = D(vr_mensalidades or 0)
            linha['vr_mensal'] = D(vr_mensal or 0)
            linha['mes'] = formata_data(parse_datetime(data), '%B de %Y')

            linhas.append(linha)

        rel = FinanRelatorioAutomaticoRetrato()
        rel.cpc_minimo_detalhe = 4
        rel.title = u'Ordens de Serviço por Mês, Tipo de Orçamento e Etapa'

        rel.colunas = [
            ['numero', 'C', 10, u'Nº OS', False],
            ['data', 'D', 10, u'Data', False],
            ['cliente', 'C', 60, u'Cliente', False],
            ['vr_mensal', 'F', 12, u'Mensalidade', True],
            ['vr_produtos', 'F', 12, u'Produtos', True],
            ['vr_servicos', 'F', 12, u'Serviços', True],
            ['vr_total', 'F', 12, u'Total', True],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        rel.grupos = [
            ['mes', u'Mês', True],
            ['tipo_orcamento', u'Tipo de Orçamento', False],
            ['etapa', u'Etapa', False],
        ]
        rel.monta_grupos(rel.grupos)

        filtro = u'Período de ' + formata_data(rel_obj.data_inicial)
        filtro += u' a ' + formata_data(rel_obj.data_final)

        #rel.band_page_header.height += 18
        #rel.band_page_header.elements[-1].text += u'<br/>Data ' + formata_data(rel_obj.data_final)

        pdf = gera_relatorio(rel, linhas)

        dados = {
            'nome': 'os_mes_tipo_orcamento_etapa.pdf',
            'arquivo': base64.encodestring(pdf),
            #'nome_csv': 'finan_ageing.csv',
            #'arquivo_csv': base64.encodestring(csv),
        }
        rel_obj.write(dados)

        return True
    
    def gera_relatorio_vendas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        
        filtro = {            
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }  
                
        if len(rel_obj.etapa_ids) > 0:
            etapa_ids = []

            for etapa_obj in rel_obj.etapa_ids:
                etapa_ids.append(etapa_obj.id)
            
        sql = """
            select
                empresa.name as empresa_nome,
                cliente.name as cliente_nome,
                pedido.id as pedido_id,
                pedido.name as pedido_numero,
                pedido.date_order as data_pedido,
                etapa.nome as etapa_nome,
                pedido.vr_total_produtos_sem_desconto as valor_produto,
                pedido.vr_total_servicos_sem_desconto as valor_servico,
                coalesce(pedido.vr_desconto_rateio,0) + coalesce(pedido.vr_desconto_rateio_servicos,0)  as valor_desconto,
                pedido.amount_total as valor_total,
                coalesce(pedido.vr_produto_base_produtos,0) + coalesce(pedido.vr_produto_base_servicos,0) as valor_custo,
                coalesce(pedido.vr_margem_contribuicao_produtos,0) + coalesce(pedido.vr_margem_contribuicao_servicos,0) as valor_lucro,
            
                case when prodmod.type = 'product' then 'Produto' else 'Servico' end as tipo,
                prod.name_template as item_produto,
                prod.default_code as item_produto_codigo,
                unid.name as item_unidade,
                coalesce(item.product_uom_qty, 0) as item_quantidade,
                coalesce(item.vr_unitario_venda_impostos, 0) as item_vr_unitario,
                coalesce(item.vr_total_venda_impostos, 0) as item_vr_total,
                coalesce(item.vr_produto_base, 0) as item_vr_custo,
                coalesce(item.vr_margem_contribuicao, 0) as item_vr_margem_contribuicao
            
            from
                sale_order pedido
                join sale_order_line item on item.order_id = pedido.id
                join sale_etapa etapa on etapa.id = pedido.etapa_id
                join product_product prod on prod.id = item.product_id
                join product_template prodmod on prodmod.id = prod.product_tmpl_id
                join product_uom as unid on unid.id = prodmod.uom_id
                join res_company comp on comp.id = pedido.company_id
                left join res_company cc on cc.id = comp.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
                join res_partner empresa on empresa.id = comp.partner_id
                join res_partner cliente on cliente.id = pedido.partner_id
            where 
                pedido.date_order between '{data_inicial}' and '{data_final}'"""
                
        sql_ids = """
            select distinct
                pedido.id  
            from
                sale_order pedido
                join res_company comp on comp.id = pedido.company_id
                left join res_company cc on cc.id = comp.parent_id
                left join res_company ccc on ccc.id = cc.parent_id
            where 
                pedido.date_order between '{data_inicial}' and '{data_final}'
            """        
                
        if rel_obj.company_id: 
            
            filtro['company_id'] = str(rel_obj.company_id.id)          
            
            sql += """
                and (
                    comp.id = {company_id}
                    or cc.id = {company_id}
                    or ccc.id = {company_id}
                   )"""
                    
            sql_ids += """   
                and (
                    comp.id = {company_id}
                    or cc.id = {company_id}
                    or ccc.id = {company_id}
                )
                """ 
                             
        if len(rel_obj.etapa_ids) > 0:
            sql += 'and pedido.etapa_id in'   +  str(tuple(etapa_ids)).replace(',)', ')')
            
            sql_ids += 'and pedido.etapa_id in'   +  str(tuple(etapa_ids)).replace(',)', ')')
                    
        sql += """                
            order by
            empresa.name,
            pedido.id,
            cliente.name;"""

        sql = sql.format(**filtro)
        sql_ids = sql_ids.format(**filtro)
        
        print(sql_ids)
        cr.execute(sql_ids)
        dados = cr.fetchall()
        
        ids = []        
        if len(dados) > 0:
            for id in dados:
                ids.append(id[0])                
            
            self.pool.get('sale.order')._simulacao_parcelas(cr, uid, ids, None, None, context={'salva_dados' : True})        
            cr.commit()
            
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        
        rel = Report(u'Relatório de Vendas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'integra_relatorio_venda.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['RENTABILIDADE'] = rel_obj.rentabilidade        
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()
        

        dados = {
            'nome': u'Relatório_Vendas_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + ('.') + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True       
    

sale_relatorio()
