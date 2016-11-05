# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.relatorio import *
import csv
from pybrasil.base import DicionarioBrasil



DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class asp_relatorio(osv.osv_memory):
    _name = 'asp.relatorio'
    _description = 'asp.relatorio'
    _rec_name = 'nome'
    
    _columns = {        
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),        
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),   
        'location_id': fields.many2one('stock.location', u'Local do Estoque'), 
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'municipio_id': fields.many2one('sped.municipio', u'Cidade'),
        'estado_id': fields.many2one('sped.estado', u'Estado'),
        'user_id': fields.many2one('res.users', u'Representate'),            
    }

    _defaults = {
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,              
    }     
    
    def gera_estoque_minimo(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            location_id = rel_obj.location_id.id

            sql = """select * from  (
                        select 
                        pc.nome_completo,
                        pp.default_code,
                        pt.name,
                        pp.variants,                       
                        
                        coalesce((select sw.product_min_qty
                        from stock_warehouse_orderpoint sw
                        where sw.product_id = pp.id), 0) as minimo_stock,
                        
                        coalesce((select 
                        sum(
                        case
                        when es.tipo = 'S' THEN 
                        es.quantidade * -1
                        else
                        es.quantidade
                        end ) as quantidade
                        from estoque_entrada_saida es 
                        where es.product_id = pp.id
                        and es.location_id = sm.location_id ), 0) as quantidade,
                        
                        coalesce((select distinct
                        sum(sol.quantidade) as quantidade_venda
                        from sale_order_line sol
                        where sol.product_id = pp.id
                        and state = 'Confirmed'), 0) as quantidade_venda,
                        
                        
                        coalesce((select distinct
                        sum(pol.product_qty) as pedido
                        from purchase_order_line pol
                        where pol.product_id = pp.id
                        and state = 'confirmed'), 0) as pedido
                        
                        from estoque_entrada_saida sm 
                        join product_product pp on pp.id = sm.product_id
                        join product_template pt on pt.id = pp.product_tmpl_id
                        join product_category pc on pc.id = pt.categ_id
                        
                        where sm.location_id =  """ + str(location_id) + """
                        
                        order by 
                        pc.id , pt.name)
                        as a 
                        where 
                        minimo_stock > 0
           ;"""
                        
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for categoria, codigo, produto, variants, minimo_stock, quantidade, quantidade_venda, pedido in dados:
                linha = DicionarioBrasil()
                linha['categoria'] = categoria
                linha['codigo'] = codigo
                linha['produto'] = produto
                linha['variants'] = variants
                linha['minimo_stock'] = minimo_stock
                linha['quantidade'] = quantidade
                linha['quantidade_venda'] = quantidade_venda
                linha['pedido'] = pedido
                linhas.append(linha)


            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Produtos para Comprar'
            rel.colunas = [
                ['codigo' , 'C', 10, u'Código', False],
                ['produto' , 'C', 50, u'Descrição', False],
                ['variants', 'C', 15, u'Fornecedor', False],
                ['quantidade' , 'F', 10, u'Estoque.', True],
                ['minimo_stock' , 'F', 10, u'Minimo.', True],
                ['quantidade_venda' , 'I', 10, u'Venda', True],
                ['pedido' , 'I', 10, u'Compra', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)
            
            rel.grupos = [
                ['categoria', u'Categoria', False],
            ]
            rel.monta_grupos(rel.grupos)
            

            location_obj = self.pool.get('stock.location').browse(cr, uid, location_id)
            rel.band_page_header.elements[-1].text = u'Local: ' + location_obj.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'produto_para_compra.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True 
    
    def gera_relatorio_clientes(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
                        
            sql = """select 
                    rp.name,
                    cli.name as cliente,
                    coalesce(cli.email_nfe,'') as email,
                    coalesce(cli.bairro,'') as bairro,
                    coalesce(cli.fone,'') as fone,
                    coalesce(cli.endereco,'') ||', nº' || coalesce(cli.numero,'') as endereco,
                    case 
                    when cli.active = true then
                    'Ativo'
                    else 
                    'Inativo'
                    end as ativo,
                    coalesce(u.name, 'Sem representante') as representante,
                    coalesce(spu.nome, 'Sem municipio') as municipio,
                    coalesce(se.nome, 'Sem estado') as estado
                                        
                    
                    from res_partner cli
                    left join res_users u on u.id = cli.user_id
                    left join sped_municipio spu on spu.id = cli.municipio_id
                    left join sped_estado se on se.id = spu.estado_id  
                                                                
                    left join res_company c on c.id = cli.company_id
                    left join res_partner rp on rp.id = c.partner_id
                                    
                    where 
                    cli.customer = true                                  
            """
            
            if rel_obj.company_id:
                sql += """
                    and c.id = """ + str(rel_obj.company_id.id)
           
            if rel_obj.partner_id:
                sql += """
                    and cli.id = """ + str(rel_obj.partner_id.id)
                     
            if rel_obj.municipio_id:
                sql += """
                    and spu.id = """ + str(rel_obj.municipio_id.id)
                    
            if rel_obj.estado_id:
                sql += """
                    and se.id = """ + str(rel_obj.estado_id.id)
            
            if rel_obj.user_id:
                sql += """
                    and u.id = """ + str(rel_obj.user_id.id)   
                    
            sql += """
                    order by
                        rp.name, se.nome, u.name, spu.nome, cli.name   

                    ;"""
                                    
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')
            
            linhas = []
            for empresa, cliente, email, bairro, fone, endereco, ativo, representante, municipio, estado in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['cliente'] = cliente
                linha['email'] = email
                linha['bairro'] = bairro
                linha['fone'] = fone
                linha['endereco'] = endereco
                linha['ativo'] = ativo
                linha['representante'] = representante
                linha['municipio'] = municipio
                linha['estado'] = estado
                linhas.append(linha)
                


            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Clientes por Estado'
            rel.colunas = [
                ['cliente' , 'C', 40, u'Código', False],
                ['municipio','C', 20, u'Cidade', False],
                ['bairro' , 'C', 15, u'Bairro', False],
                ['email', 'C', 25, u'Email', False],
                ['fone' , 'C', 15, u'Fone', False],
                ['endereco' , 'C', 30, u'Endereco', False],
                ['ativo' , 'C', 8, u'Situacão', False],                
            ]

            rel.monta_detalhe_automatico(rel.colunas)
            
            rel.grupos = [
                ['empresa', u'Empresa', False],             
                ['estado', u'Estado', False],             
                ['representante', u'Representate', False],
            ]            
                        
            rel.monta_grupos(rel.grupos)
            
            
            if rel_obj.company_id:
                company_id = rel_obj.company_id.id
            else:
                company_id = 1
            
            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa: ' + company_obj.partner_id.name

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': u'clientes_por_estado.pdf',
                'arquivo': base64.encodestring(pdf),
            }
            rel_obj.write(dados)

        return True 
 
      

asp_relatorio()

