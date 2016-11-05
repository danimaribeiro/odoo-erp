# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from relatorio import *
from finan.wizard.relatorio import FinanRelatorioAutomaticoRetrato

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {
                'variants': fields.char(u'Marca', 120),
                'user_id': fields.many2one('res.users', u'Usuário'),
                'category_id':fields.many2one('product.category', u'Categoria'), 
    }

    _defaults = {
               
    }


    def gera_relatorio_curva_abc_asp(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        sql_total = """
        select distinct
            sum(coalesce(sdi.vr_fatura, 0)) as valor_fatura
            
            from sped_documento sd
            join res_partner rp on rp.id = sd.partner_id            
            join sped_documentoitem sdi on sdi.documento_id = sd.id
            join product_product pp on pp.id = sdi.produto_id            
            
            where sd.company_id = {company_id}
            and sd.state = 'autorizada'
            and sd.emissao = '0'            
            and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
            """
               
        if rel_obj.variants:
            sql_total += """
                and pp.variants like '""" + rel_obj.variants + """%'
                ;"""
                  
        sql_total = sql_total.format(company_id=company_id, data_inicial=str(data_inicial), data_final=str(data_final))  
        print(sql_total)
        cr.execute(sql_total)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')
        
        valor_total = D(0)
        for valor in dados:        
            valor_total = D(valor[0] or 0)
        
        sql = """
            select distinct
                pp.variants,
                rp.name as cliente,
                rp.cnpj_cpf as cnpj_cpf,
                sum(coalesce(sdi.vr_fatura, 0)) as valor_fatura
            
            from 
                sped_documento sd
                join res_partner rp on rp.id = sd.partner_id
                join sped_documentoitem sdi on sdi.documento_id = sd.id
                join product_product pp on pp.id = sdi.produto_id
               
            where
                sd.company_id = {company_id}
                and sd.state = 'autorizada'
                and sd.emissao = '0'                          
                and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'  
            """
            
        if rel_obj.variants:
            sql += """
                  and pp.variants like '""" + rel_obj.variants + """%'"""
                
        sql += """
            group by
                pp.variants,
                cliente,
                cnpj_cpf            
            
            order by
                valor_fatura desc;"""
                
        sql = sql.format(company_id=company_id, data_inicial=str(data_inicial), data_final=str(data_final))  
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        for variants, cliente, cnpj_cpf, valor_fatura in dados:
            linha = DicionarioBrasil()
            linha['variants'] = variants
            linha['cliente'] = cliente
            linha['cnpj_cpf'] = cnpj_cpf
            linha['valor_fatura'] = D(valor_fatura or 0) 
            porcentagem = D(valor_fatura) / valor_total * 100            
            linha['porcentagem'] = porcentagem.quantize(D('0.001'))            
            linhas.append(linha)


        rel = FinanRelatorioAutomaticoRetrato()
        rel.title = u'Curva Abc Financeiro'
        rel.colunas = [
            ['cnpj_cpf' , 'C', 15, u'CNPJ/CPF', False],
            ['cliente' , 'C', 50, u'Clientes', False],
            ['valor_fatura', 'F', 15, u'Valor Faturado', True],
            ['porcentagem' , 'F', 10, u'%', True],           
        ]

        rel.monta_detalhe_automatico(rel.colunas)
        
        if rel_obj.variants:
            rel.grupos = [
                    ['variants', u'Marca', False],
                ]
            rel.monta_grupos(rel.grupos)
                

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        rel.band_page_header.elements[-1].text = u'EMPRESA: ' + company_obj.partner_id.name + u' - PERÍODO: ' + formata_data(data_inicial) + u' a ' + formata_data(data_final)

        pdf = gera_relatorio(rel, linhas)

        dados = {
            'nome': u'Curva_abc_clientes_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf),
        }
        rel_obj.write(dados)

        return True 

    def gera_relatorio_vendedor_produto(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

                
        sql = """
             select distinct
            ru.name as vendedor,
            pc.name as categoria,
            pt.name as produto, 
            count(so.id) as vendas,
            sum(sdi.quantidade) as quantidado_produto,
            sum(sdi.vr_unitario) as unitario_produto,                        
            sum(sdi.vr_nf) as valor
            
            
            from sped_documento sd
            join sped_documentoitem sdi on sdi.documento_id = sd.id
            join sale_order_sped_documento spd on spd.sped_documento_id = sd.id
            join sale_order so on so.id = spd.sale_order_id  
            join product_product pp on pp.id = sdi.produto_id
            join product_template pt on pt.id = pp.product_tmpl_id
            join product_category pc on pc.id = pt.categ_id
            join res_users ru on ru.id = so.user_id
            
            join res_company c on c.id = sd.company_id
            join res_partner rp on rp.id = c.partner_id
    
            where
            sd.state = 'autorizada'
            and sd.modelo = '55'             
            and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'  
            and c.id = {company_id}
            and so.user_id is not null
            """             
            
        if rel_obj.category_id:
            sql += """
                   and pc.id = """ + str(rel_obj.category_id.id)  

        if rel_obj.user_id:
            sql += """
                and so.user_id = """ +  str(rel_obj.user_id.id)      
                    
        sql +="""
            group by 
            vendedor,
            categoria,
            produto
                              
            order by
                ru.name, pt.name;"""
                
                
        sql = sql.format(company_id=company_id, data_inicial=str(data_inicial), data_final=str(data_final))  
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        linhas = []
        for vendendor, categoria, produto, quantidade_vendas, quantidade_produto, unitario_produto, valor_venda  in dados:
            linha = DicionarioBrasil()
            linha['vendendor'] = vendendor
            linha['categoria'] = categoria
            linha['produto'] = produto
            linha['quantidade_vendas'] = quantidade_vendas
            linha['quantidade_produto'] = D(quantidade_produto or 0) 
            valor_medio = D(unitario_produto) / quantidade_vendas             
            linha['valor_medio'] = D(valor_medio)          
            linha['valor_venda'] = D(valor_venda or 0) 
            linhas.append(linha)


        rel = FinanRelatorioAutomaticoRetrato()
        rel.title = u'Relatório Vendedor x Produto'
        rel.colunas = [
            ['produto' , 'C', 70, u'Produto', False],
            ['quantidade_vendas' , 'I', 10, u'Qtd.Vendas', False],
            ['quantidade_produto', 'F', 10, u'Qtd.Prod', True],
            ['valor_medio' , 'F', 15, u'Vl.Médio', True],           
            ['valor_venda', 'F', 15, u'Vl.Total', True],
        ]

        rel.monta_detalhe_automatico(rel.colunas)
        
        rel.grupos = [
                ['vendendor', u'Vendedor', False],
                ['categoria', u'Categoria', False],
            ]
        rel.monta_grupos(rel.grupos)
                

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        rel.band_page_header.elements[-1].text = u'EMPRESA: ' + company_obj.partner_id.name + u' - PERÍODO: ' + formata_data(data_inicial) + u' a ' + formata_data(data_final)

        pdf = gera_relatorio(rel, linhas)

        dados = {
            'nome': u'Vendedor_x_produto' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf),
        }
        rel_obj.write(dados)

        return True 


finan_relatorio()
