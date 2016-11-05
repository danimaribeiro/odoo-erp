# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from sql_relatorio_estrutura import SQL_FINAN_ESTRUTURA_DEMONSTRATIVO
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
    ('DREG', u'DEMONSTRAÇÃO RESULTADO DO EXERCÍCIO'),             
]


class finan_estrutura_analise(osv.Model):
    _name = 'finan.estrutura.analise'
    _description = u'Análise Financeira Gerencial'
    _order = 'data_inicial desc, data_final desc, data desc, descricao'
    _rec_name = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=120, select=True),
        'company_id': fields.many2one('res.company', u'Empresa/Unidade', ondelete='restrict'),    
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.datetime(u'Data de geração'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),        
        'item_ids': fields.one2many('finan.estrutura.analise.item', 'analise_estrutura_id', u'Itens da análise'),
        'item_ids_view': fields.one2many('finan.estrutura.analise.item.view', 'analise_estrutura_id', u'Itens da análise'),
        'tipo_demonstrativo': fields.selection(ESTRUTURA, u'Tipo de demonstrativo'),
        'somente_cnpj': fields.boolean(u'Somente CNPJ?'),
        'sintetica': fields.boolean(u'Sintético?'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),                   
    }
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.estrutura.analise', context=c),
        'somente_cnpj': True,
        'formato': 'pdf',
    }
      
    
    def gera_analise(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('finan.estrutura.analise.item')
        estrutura_pool = self.pool.get('finan.estrutura.demonstrativo')

        for analise_obj in self.browse(cr, uid, ids):
            
                
            
            dados = {
                'company_id': analise_obj.company_id.id,
                'centrocusto_id': '',
                'data_inicial': analise_obj.data_inicial,
                'data_final': analise_obj.data_final,
                'tipo_demonstrativo': analise_obj.tipo_demonstrativo,
            }
            
            if analise_obj.centrocusto_id:
                dados['centrocusto_id'] = 'and p.centrocusto_id = ' + str(analise_obj.centrocusto_id.id)
                        
            sql = SQL_FINAN_ESTRUTURA_DEMONSTRATIVO.format(**dados)
                
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

            FROM finan_estrutura_analise ea
                join finan_estrutura_analise_item l on l.analise_estrutura_id = ea.id                
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
            
            if analise_obj.tipo_demonstrativo == 'DREG':
                rel = Report(u'DEMONSTRAÇÃO RESULTADO DO EXERCÍCIO GERENCIAL', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_dre_gerencial.jrxml')
                nome_rel = u'' + str(agora())[:10].replace(' ','_' ).replace('-','_') + '.' + analise_obj.formato
                                
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
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.estrutura.analise'), ('res_id', '=', analise_obj.id), ('name', '=', nome_rel)])
            attachment_pool.unlink(cr, uid, attachment_ids)
            
            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_rel,
                'datas_fname': nome_rel,
                'res_model': 'finan.estrutura.analise',
                'res_id': analise_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)
            
            analise_obj.write({'data': str(datetime.now())[:19]})
    
        return True         
            

finan_estrutura_analise()

NIVEL = [
    ('1', u'1'),
    ('2', u'2',),
    ('3', u'3'),
    ('4', u'4'),    
]

class finan_estrutura_analise_item(osv.Model):
    _name = 'finan.estrutura.analise.item'
    _description = u'Finan item da Estrutura de Análise'
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
        'analise_estrutura_id': fields.many2one('finan.estrutura.analise', u'Análise da Estrutura'),
        'estrutura_id': fields.many2one('finan.estrutura.demonstrativo', u'Estrutura'),
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
    
finan_estrutura_analise_item()

class finan_estrutura_analise_item_view(osv.Model):
    _name = 'finan.estrutura.analise.item.view'
    _description = u'Finan item da Estrutura de Análise VIEW' 
    _order = 'codigo_completo'
    _auto = False
    
    _columns = {
        'analise_estrutura_id': fields.many2one('finan.estrutura.analise', u'Análise da Estrutura'),        
        'codigo_completo': fields.char(u'Código', size=40),
        'nome_estrutura': fields.char(u'Drescição', size=180),        
        'valor_nivel_4': fields.float(u'Nível 4'),
        'valor_nivel_3': fields.float(u'Nível 3'),
        'valor_nivel_2': fields.float(u'Nível 2'),
        'valor_nivel_1': fields.float(u'Nível 1'),
        'valor': fields.float(u'Valor'),                
    }
    
finan_estrutura_analise_item_view()   


