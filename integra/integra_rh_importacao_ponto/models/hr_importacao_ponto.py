# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
import os
import base64
from datetime import date
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes, parse_datetime, formata_data, agora, hoje, idade_anos
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.relatorio import *

MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

def primeiro_ultimo_dia_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = primeiro_dia + relativedelta(months=+1, days=-1)
    return str(primeiro_dia)[:10], str(ultimo_dia)[:10]


class hr_importacao_ponto(osv.Model):
    _description = u'Importação Cartão Ponto'
    _name = 'hr.importacao.ponto'
    _rec_name = 'company_id'
    _order = 'data_inicial desc, data_final desc'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = exp_obj.id

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'data': fields.date(u'Data do Arquivo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),        
        'arquivo_binario': fields.binary(u'Arquivo'),
        'processado_item_ids': fields.one2many('hr.processado.ponto', 'ponto_id', u'Pontos Processados'),
        'rejeitado_item_ids': fields.one2many('hr.rejeitado.ponto', 'ponto_id', u'Pontos Rejeitados'),
        'input_ids': fields.one2many('hr.payslip.input', 'ponto_id', u'Entradas variáveis'),
        'importado': fields.boolean(u'Importador'),       
        'nome_conferencia': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo_conferencia': fields.binary(u'Arquivo', readonly=True),         
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.importacao.ponto', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'data': fields.date.today,
        'ano': lambda *args, **kwargs: mes_passado().year,
        'mes': lambda *args, **kwargs: str(mes_passado().month),
    }
    
    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        return retorno
    
    def processar_retorno(self, cr, uid, id, context=None):
        processado_pool = self.pool.get('hr.processado.ponto')
        rejeitado_pool = self.pool.get('hr.rejeitado.ponto')

        if isinstance(id, list):
            id = id[0]
        
        retorno_obj = self.browse(cr, uid, id)
        
        cr.execute('delete from hr_processado_ponto where ponto_id = {id}'.format(id=retorno_obj.id))
        cr.execute('delete from hr_rejeitado_ponto where ponto_id = {id}'.format(id=retorno_obj.id))

        if not retorno_obj.arquivo_binario:
            raise osv.except_osv(u'Erro!', u'Nenhum arquivo informado!')

        arquivo_texto = base64.decodestring(retorno_obj.arquivo_binario)
        arquivo = StringIO()
        arquivo.write(arquivo_texto)
        arquivo.seek(0)
        
        for linha in arquivo.readlines():
            pis = linha[1:12]
            rule_id = int(linha[12:17])                          
            hora = int(linha[17:22]) 
            minutos = int(linha[22:24]) / 60
            horas = hora + minutos
            
            sql = """
                select distinct
                    co.id 
                from hr_contract co
                    join hr_employee e on e.id = co.employee_id
                    
                where 
                    (co.date_end is null 
                    or 
                    date_end between '{data_inicial}' and '{data_final}')
                    and e.nis = '{pis}'
                    limit 1"""
                    
            sql = sql.format(data_inicial=retorno_obj.data_inicial,data_final=retorno_obj.data_final, pis=pis) 
                      
            cr.execute(sql)
            dados = cr.fetchall()
            
            contract_id = False            
            for id in dados:
                contract_id = id[0]
            
            rule_id = self.pool.get('hr.salary.rule').search(cr, 1 , [('id','=', rule_id)])           
                
            if not contract_id or len(rule_id) == 0:   
                texto = u''
                if not contract_id:
                    texto += u'Pis não cadastrado! ' 
                
                if len(rule_id) == 0:
                    texto += u'Rúbrica não cadastrada! ' 
                                                           
                rejeitado_pool.create(cr,uid, {'ponto_id': retorno_obj.id,'pis': pis, 'linha': linha, 'causa': texto})                             
            else:                                
                dados = {
                    'ponto_id': retorno_obj.id,
                    'contract_id': contract_id,
                    'rule_id': rule_id[0],
                    'horas': horas,                         
                } 
                processado_pool.create(cr, uid, dados) 
    
    def confirmar_lancamento(self, cr, uid, ids, context={}):
        input_pool = self.pool.get('hr.payslip.input')
        
        for ponto_obj in self.browse(cr, uid, ids):
            
            for item_obj in ponto_obj.processado_item_ids:
                dados = {                   
                    'ponto_id': ponto_obj.id,
                    'company_id': ponto_obj.company_id.id,
                    'contract_id': item_obj.contract_id.id, 
                    'employee_id': item_obj.contract_id.employee_id.id,
                    'rule_id': item_obj.rule_id.id,                                                         
                    'data_inicial': ponto_obj.data_inicial,
                    'data_final': ponto_obj.data_final,                    
                    'amount': item_obj.horas or 0                    
                }                    
                input_pool.create(cr,uid, dados) 
            
            ponto_obj.write({'importado': True})
        
        return True
    
    def gera_relatorio_conferencia(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            
            processados_ids = []
            for processados_id in rel_obj.processado_item_ids:
                processados_ids.append(processados_id.id)
                
            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Confência Ponto'
            rel.monta_contagem = True
            rel.colunas = [                
                ['contract_id.descricao' , 'C', 80, u'Contrato', False],
                ['rule_id.descricao', 'C', 30, u'Rúbrica' , False],
                ['horas', 'F', 10, u'Horas', False],                
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [                
            #    ['employee_id.nome', u'Funcionário', False],
            #]
            #rel.monta_grupos(rel.grupos)

            processados_objs = self.pool.get('hr.processado.ponto').browse(cr, uid, processados_ids)
            
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + rel_obj.company_id.name + u' -  PERIODO ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final)


            pdf = gera_relatorio(rel, processados_objs)

            dados = {
                'nome_conferencia': 'Conferencia_Ponto.pdf',
                'arquivo_conferencia': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True
                 
    
hr_importacao_ponto()

class hr_processado_ponto(osv.Model):
    _description = u'Pontos Processados'
    _name = 'hr.processado.ponto'

    _columns = {
        'ponto_id': fields.many2one('hr.importacao.ponto', u'Arquivo ponto', ondelete='cascade'),        
        'contract_id': fields.many2one('hr.contract', u'Contrato'),        
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'horas': fields.float(u'Horas'),        
    }


hr_processado_ponto()

class hr_rejeitado_ponto(osv.Model):
    _description = u'Pontos Rejeitados'
    _name = 'hr.rejeitado.ponto'

    _columns = {
        'ponto_id': fields.many2one('hr.importacao.ponto', u'Arquivo ponto',  ondelete='cascade'),
        'pis': fields.char(u'Pis', size=11),
        'linha': fields.char(u'Linha', size=40),
        'causa': fields.char(u'Causa da rejeição', size=180),                        
    }

hr_rejeitado_ponto()

class hr_payslip_input(osv.Model):    
    _name = 'hr.payslip.input'
    _inherit = 'hr.payslip.input'
    
    _columns = {
        'ponto_id': fields.many2one('hr.importacao.ponto', u'Arquivo ponto'),
    }   

hr_payslip_input()
