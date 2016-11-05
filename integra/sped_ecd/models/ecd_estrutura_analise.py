# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from sql_relatorio_estrutura import SQL_ESTRUTURA_DEMONSTRATIVO, SQL_ESTRUTURA_DEMONSTRATIVO_GERENCIAL
from pybrasil.data import parse_datetime, formata_data, agora, hoje, mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D
from datetime import datetime
import os
import base64
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)


ESTRUTURA = [
    ('DLPA',u'DEMONSTRAÇÃO DE LUCROS OU PREJUÍZOS ACUMULADOS'),                   
    ('DOAR',u'DEMONSTRAÇÃO DAS ORIGENS E APLICAÇÕES DE RECURSOS'),  
    ('DRE', u'DEMONSTRAÇÃO RESULTADO DO EXERCÍCIO'),
    ('DRA', u'DEMONSTRAÇÃO DO RESULTADO ABRANGENTE'),
    ('DMPL', u'DEMONSTRAÇÃO DAS MUTAÇÕES DO PATRIMÔNIO LÍQUIDO'),
    ('DVA', u'DEMONSTRAÇÃO DO VALOR ADICIONADO'),
    ('EBITDA',u'LUCROS ANTES DE JUROS, IMPOSTOS,DEPRECIAÇÃO E AMORTIZAÇÃO'),         
]


class ecd_estrutura_analise(osv.Model):
    _name = 'ecd.estrutura.analise'
    _description = u'Análise da Estrutura'
    _order = 'data_inicial desc, data_final desc, data desc, descricao'
    _rec_name = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=120, select=True),
        'company_id': fields.many2one('res.company', u'Empresa/Unidade', ondelete='restrict'),
        #'company_ids': fields.many2many('res.company', 'ecd_analise_company', 'analise_estrutura_id', 'company_id', u'Empresas/Unidades'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.datetime(u'Data de geração'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),        
        'item_ids': fields.one2many('ecd.estrutura.analise.item', 'analise_estrutura_id', u'Itens da análise'),
        'item_ids_view': fields.one2many('ecd.estrutura.analise.item.view', 'analise_estrutura_id', u'Itens da análise'),
        'tipo_demonstrativo': fields.selection(ESTRUTURA, u'Tipo de demonstrativo'),
        'somente_cnpj': fields.boolean(u'Somente CNPJ?'),
        'sintetica': fields.boolean(u'Sintético?'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),
        
        'gerencial': fields.boolean(u'Gerencial?'),
        'departmento_ids': fields.many2many('hr.department','ecd_departmento_rateio','ecd_relatorio_id','department_id', u'Departamentos/Postos'),
        'centrocusto_ids': fields.many2many('finan.centrocusto','ecd_centrocusto_rateio', 'ecd_relatorio_id','centrocusto_id', u'Centros de custo'),        
        'contract_ids': fields.many2many('hr.contract','ecd_contrato_rateio', 'ecd_relatorio_id','contract_id', u'Funcionários'),
        'veiculo_ids': fields.many2many('frota.veiculo', 'ecd_frota_rateio', 'ecd_relatorio_id','veiculo_id', u'Veículoa'),                     
        'project_ids': fields.many2many('project.project', 'ecd_project_rateio', 'ecd_relatorio_id','project_id', u'Projetos'),                     
    }
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'somente_cnpj': True,
        'formato': 'pdf',
    }
      
    
    def gera_analise(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('ecd.estrutura.analise.item')
        estrutura_pool = self.pool.get('ecd.estrutura.demonstrativo')

        for analise_obj in self.browse(cr, uid, ids):
            
            descricao = u''
                            
            centrocusto_ids = []
            if len(analise_obj.centrocusto_ids) > 0:    
        
                descricao += u' | Centro de Custos: ' 
                for centrocusto_obj in rel_obj.centrocusto_ids:
                    centrocusto_ids.append(centrocusto_obj.id)
                    descricao += centrocusto_obj.nome
                            
            project_ids = []
            if len(analise_obj.project_ids) > 0:    
        
                descricao += u' | Projeto: ' 
                for project_obj in analise_obj.project_ids:
                    project_ids.append(project_obj.id)
                    descricao += project_obj.name
            
            departmento_ids = []
            if len(analise_obj.departmento_ids) > 0:    
        
                descricao += u'Departamentos/postos: ' 
                for departmento_obj in analise_obj.departmento_ids:
                    departmento_ids.append(departmento_obj.id)
                    descricao += departmento_obj.name
                    
            contract_ids = []
            if len(analise_obj.contract_ids) > 0:    
        
                descricao += u' | Contratos: ' 
                for contract_obj in analise_obj.contract_ids:
                    contract_ids.append(contract_obj.id)
                    descricao += contract_obj.descricao
                            
            veiculo_ids = []
            if len(analise_obj.veiculo_ids) > 0:    
        
                descricao += u' | Veiculos: ' 
                for veiculo_obj in analise_obj.veiculo_ids:
                    veiculo_ids.append(veiculo_obj.id)
                    descricao += veiculo_obj.nome
            
            
            dados = {
                'company_id': analise_obj.company_id.id,
                'data_inicial': analise_obj.data_inicial,
                'data_final': analise_obj.data_final,
                'tipo_demonstrativo': analise_obj.tipo_demonstrativo,
                'departmento_ids': '',
                'centrocusto_ids': '',
                'contract_ids': '',
                'veiculo_ids': '',
                'project_ids': '',
            }

            #company_ids = []
            #for company_obj in analise_obj.company_ids:
            #    company_ids.append(company_obj.id)

            #dados['company_ids'] = str(tuple(company_ids)).replace(',)', ')')
            
            if analise_obj.gerencial:
                
                if len(departmento_ids) > 0:  
                    dados['departmento_ids'] = """and lcr.hr_department_id in """ +  str(tuple(departmento_ids)).replace(',)', ')')
               
                if len(centrocusto_ids) > 0:                      
                    dados['centrocusto_ids'] = """and coalesce(lcr.centrocusto_id, l.centrocusto_id)  in """ +  str(tuple(centrocusto_ids)).replace(',)', ')')
                    
                if len(contract_ids) > 0:  
                    dados['contract_ids'] = """and lcr.hr_contract_id in """ +  str(tuple(contract_ids)).replace(',)', ')')
                    
                if len(veiculo_ids) > 0:  
                    dados['veiculo_ids'] = """and lcr.veiculo_id in """ +  str(tuple(veiculo_ids)).replace(',)', ')')
                
                if len(project_ids) > 0:  
                    dados['project_ids'] = """and lcr.veiculo_id in """ +  str(tuple(project_ids)).replace(',)', ')')
                
                
                sql = SQL_ESTRUTURA_DEMONSTRATIVO_GERENCIAL.format(**dados)
                
            else:
                sql = SQL_ESTRUTURA_DEMONSTRATIVO.format(**dados)
                
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()
            #print('leu analise')

            #
            # Exclui os itens antigos
            #
            for item_obj in analise_obj.item_ids:
                item_obj.unlink()

            linhas_analise = {}
            resumidas = []

            for (estrutura_id, codigo_completo, conta_nome, conta_contabil, resumida, valor_debito, valor_credito) in dados:
                
                
                valor = D(0)
                valor_debito = D(valor_debito)
                valor_credito = D(valor_credito)
                
                if codigo_completo[:2] == '(-)':
                    valor -= valor_credito - valor_debito
                else:  
                    valor += valor_credito - valor_debito 
                
                dados_item = {
                    'analise_estrutura_id': analise_obj.id,
                    'estrutura_id': estrutura_id,
                    'conta_contabil':conta_contabil,                    
                    'valor_debito': valor_debito,
                    'valor_credito':valor_credito,
                    'valor': valor,
                }
                
                estrutura_conta_obj = estrutura_pool.browse(cr, uid, estrutura_id)

                item_pool.create(cr, uid, dados_item)

                if resumida:
                    resumidas.append(estrutura_conta_obj)
                    

                linhas_analise[estrutura_id] = [D(valor_debito), D(valor_credito)]

            #
            # Agora, vamos varrer a lista completa de contas, trazendo as contas
            # que faltam, definindo o valor para 0
            #
            
            for estrutura_id in estrutura_pool.search(cr, uid, [], order='codigo_completo'):
                
                if not estrutura_id in linhas_analise:
                                     
                    estrutura_conta_obj = estrutura_pool.browse(cr, uid, estrutura_id)

                    #
                    # As conta não tem linha de análise, inserir zerada
                    #
                    dados_item = {
                        'analise_estrutura_id': analise_obj.id,
                        'estrutura_id': estrutura_id,
                        'valor_debito': D(0),
                        'valor_credito': D(0),                        
                        'valor': D(0),                        
                    }
                    
                    if estrutura_conta_obj.resumida:
                        resumidas.append(estrutura_conta_obj)
                    else:    
                        item_pool.create(cr, uid, dados_item)

            #
            # Agora, vamos pegar as contas resumidas e fazer as somas e subtrações
            #
            for conta_resumida_obj in resumidas:
                valor = D(0)
                valor_debito = D(0)
                valor_credito = D(0)

                for soma_obj in conta_resumida_obj.resumida_soma:
                    if soma_obj.id in linhas_analise:
                        valor_debito += linhas_analise[soma_obj.id][0]
                        valor_credito += linhas_analise[soma_obj.id][1]

                for subtrai_obj in conta_resumida_obj.resumida_subtrai:
                    if subtrai_obj.id in linhas_analise:
                        valor_debito -= linhas_analise[subtrai_obj.id][0]
                        valor_credito -= linhas_analise[subtrai_obj.id][1]
                        
                if conta_resumida_obj.codigo_completo[:2] == '(-)':
                    valor -= valor_credito - valor_debito
                else:  
                    valor += valor_credito - valor_debito 

                dados_item = {
                        'analise_estrutura_id': analise_obj.id,
                        'estrutura_id': conta_resumida_obj.id,
                        'valor_debito': valor_debito,
                        'valor_credito': valor_credito,                        
                        'valor': valor,                        
                }
                item_pool.create(cr, uid, dados_item)
                linhas_analise[conta_resumida_obj.id] = [valor_debito, valor_credito]
                
            
            sql = """        
            SELECT 
                c.id as company_id,
                coalesce(rp.razao_social,'') as empresa,
                rp.cnpj_cpf,
                l.codigo_completo,
                l.nome,                
                l.sintetica,
                l.resumida,
                l.nivel_estrutura, 
                sum(coalesce(l.valor_debito,0)) as vr_debito,
                sum(coalesce(l.valor_credito,0)) as vr_credito,
                sum(coalesce(l.valor, 0)) as valor

            FROM ecd_estrutura_analise ea
                join ecd_estrutura_analise_item l on l.analise_estrutura_id = ea.id                
                join res_company c on c.id = ea.company_id
                join res_partner rp on rp.id = c.partner_id
          
            where
                ea.tipo_demonstrativo = '{tipo_demonstrativo}' """
                
            if analise_obj.somente_cnpj:
                sql += """               
                and rp.cnpj_cpf = '{cnpj_cpf}' """
            else:
                sql += """               
                and c.id = """ + str(analise_obj.company_id.id)
                                
            sql += """
            
            group by 

                c.id,
                rp.razao_social,
                rp.cnpj_cpf,
                l.codigo_completo,
                l.nome,               
                l.sintetica,
                l.resumida,
                l.nivel_estrutura
                 
            ORDER BY 
                l.codigo_completo
                """               
    
            filtro = {
                'tipo_demonstrativo': analise_obj.tipo_demonstrativo,
                'cnpj_cpf': str(analise_obj.company_id.partner_id.cnpj_cpf),                
            }
    
            sql = sql.format(**filtro)
            data_inicial = parse_datetime(analise_obj.data_inicial).date()
            data_final = parse_datetime(analise_obj.data_final).date()
            
            if analise_obj.tipo_demonstrativo == 'DRE':
                rel = Report(u'DRE - DEMONSTRAÇÃO RESULTADO DO EXERCÍCIO', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'sped_ecd_dre.jrxml')
                nome_rel = u'DRE_' + str(agora())[:10].replace(' ','_' ).replace('-','_') + '.' + analise_obj.formato
                                
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['SQL'] = sql       
            if analise_obj.sintetica:
                rel.parametros['SINTETICA'] = True  
                
            if analise_obj.somente_cnpj:
                rel.parametros['CNPJ'] =  """and rp.cnpj_cpf = '""" + analise_obj.company_id.partner_id.cnpj_cpf + """'"""
            else:
                rel.parametros['CNPJ'] =   'and c.id = ' + str(analise_obj.company_id.id)
                                     
                 
            pdf, formato = rel.execute()
            
            
            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'ecd.estrutura.analise'), ('res_id', '=', analise_obj.id), ('name', '=', nome_rel)])
            attachment_pool.unlink(cr, uid, attachment_ids)
            
            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_rel,
                'datas_fname': nome_rel,
                'res_model': 'ecd.estrutura.analise',
                'res_id': analise_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)
            
            analise_obj.write({'data': str(datetime.now())[:19]})
    
        return True         
            

ecd_estrutura_analise()

NIVEL = [
    ('1', u'1'),
    ('2', u'2',),
    ('3', u'3'),
    ('4', u'4'),    
]

class ecd_estrutura_analise_item(osv.Model):
    _name = 'ecd.estrutura.analise.item'
    _description = u'Item da Estrutura de Análise'
    _order = 'codigo_completo'
    _rec_name = 'nome_completo'
    
        
    def _get_nivel(self, cr, uid, ids, nome_campo, args, context=None):
        
        res = {}                 
        for item_obj in self.browse(cr, uid, ids):
            
            if nome_campo == 'valor_nivel_1' and item_obj.nivel_estrutura == '1':
                res[item_obj.id] = item_obj.valor
               
            elif nome_campo == 'valor_nivel_2' and item_obj.nivel_estrutura == '2':
                res[item_obj.id] = item_obj.valor
               
            elif nome_campo == 'valor_nivel_3' and item_obj.nivel_estrutura == '3':
                res[item_obj.id] = item_obj.valor
               
            elif nome_campo == 'valor_nivel_4' and item_obj.nivel_estrutura == '4':
                res[item_obj.id] = item_obj.valor
                
            else:
                res[item_obj.id] = 0
                    
        return res
    
    _columns = {
        'analise_estrutura_id': fields.many2one('ecd.estrutura.analise', u'Análise da Estrutura', ondelete='cascade'),
        'estrutura_id': fields.many2one('ecd.estrutura.demonstrativo', u'Estrutura', ondelete='restrict'),
        'codigo_completo': fields.related('estrutura_id', 'codigo_completo', string=u'Código', type='char', store=True),
        'nome': fields.related('estrutura_id', 'nome', string=u'Descrição', type='char', store=True),        
        'sintetica': fields.related('estrutura_id', 'sintetica', string=u'Sintetica', type='boolean', store=True),        
        'resumida': fields.related('estrutura_id', 'resumida', string=u'Sintetica', type='boolean', store=True),
        'nivel_estrutura': fields.related('estrutura_id', 'nivel_estrutura', type='selection', selection=NIVEL ,string=u'Nível', store=True),             
        'conta_contabil': fields.many2one('finan.conta', u'Conta Contábil'),        
        'valor_debito': fields.float(u'Valor Debito'),
        'valor_credito': fields.float(u'Valor Credito'),
        'valor': fields.float(u'Valor'),
        'valor_nivel_4': fields.function(_get_nivel, type='float', store=True, digits=(18, 2), string=u'Nível 4'),
        'valor_nivel_3': fields.function(_get_nivel, type='float', store=True, digits=(18, 2), string=u'Nível 3'),
        'valor_nivel_2': fields.function(_get_nivel, type='float', store=True, digits=(18, 2), string=u'Nível 2'),
        'valor_nivel_1': fields.function(_get_nivel, type='float', store=True, digits=(18, 2), string=u'Nível 1'),
    }
    
ecd_estrutura_analise_item()

class ecd_estrutura_analise_item_view(osv.Model):
    _name = 'ecd.estrutura.analise.item.view'
    _description = u'Item da Estrutura de Análise VIEW' 
    _order = 'codigo_completo'
    _auto = False
    
    _columns = {
        'analise_estrutura_id': fields.many2one('ecd.estrutura.analise', u'Análise da Estrutura'),        
        'codigo_completo': fields.char(u'Código', size=40),
        'nome_estrutura': fields.char(u'Drescição', size=180),        
        'valor_nivel_4': fields.float(u'Nível 4'),
        'valor_nivel_3': fields.float(u'Nível 3'),
        'valor_nivel_2': fields.float(u'Nível 2'),
        'valor_nivel_1': fields.float(u'Nível 1'),
        'valor': fields.float(u'Valor'),                
    }
    
ecd_estrutura_analise_item_view()   


