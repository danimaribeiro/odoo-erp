# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from collections import OrderedDict

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {        
    }

    _defaults = {                
    }

    
    def gera_relatorio_posicao_contas(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')
        formato = context.get('formato')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo[0],
            'rateio': '',
        }

        if situacao == '1':
            sql_situacao = u"('Vencido')"
            SITUACAO = u'Vencido'

        elif situacao == '2':
            sql_situacao = u"('Vencido', 'Vence hoje')"
            SITUACAO = u'Vencido + Hoje'

        elif situacao == '3':
            sql_situacao = u"('A vencer')"
            SITUACAO = u'A Vencer'

        elif situacao == '4':
            sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Todos em aberto'

        elif situacao == '5':
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Liquidadas'

        else:
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Registrados'

        for rel_obj in self.browse(cr, uid, ids):

            texto_filtro = u''
            if len(rel_obj.res_partner_bank_ids):
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    #banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(l.valor_documento, 0.00) {rateio} as valor_documento,
                   coalesce(l.valor_desconto, 0.00) {rateio} as valor_desconto,
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) {rateio} as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) {rateio} as valor_multa,

                   coalesce(l.valor, 0.00) {rateio} as valor,
                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,                                      
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.name, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   coalesce(p.email_nfe, '') as email_nfe,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,                   
                   cf.nome as conta_nome,
                   l.provisionado,
                   case
                   when l.data_vencimento < current_date then
                   current_date - l.data_vencimento
                   else
                   0 end as data_atraso"""
          
            sql_relatorio += """
                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id                   
                   left join finan_conta cf on cf.id = l.conta_id"""
           
            if situacao < '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in '  +  str(tuple(bancos_ids)).replace(',)', ')')
                    
            elif situacao == '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and exists(select lp.id from finan_lancamento lp where lp.lancamento_id = l.id and lp.tipo in ('PP', 'PR') and lp.data_quitacao between '{data_inicial}' and '{data_final}')"""

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in'   +  str(tuple(bancos_ids)).replace(',)', ')')
                    
            else:                
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_documento between '{data_inicial}' and '{data_final}' 
                   and l.situacao in """ + sql_situacao

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """               
            
            if partner_id:
                sql_relatorio += """
                   and l.partner_id = """ + str(partner_id)

            if ativo != provisionado:
                sql_relatorio += """
                   and l.provisionado = """ + str(provisionado)

            if rel_obj.formapagamento_id:
                sql_relatorio += """
                   and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            sql_relatorio += """
                order by c.name, l.situacao, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento, cf.codigo_completo desc;"""
            

            sql_relatorio = sql_relatorio.format(**filtro)            
            #print(sql_relatorio)            
            cr.execute(sql_relatorio)
            dados = cr.fetchall()
            
            dados_relatorio = {
                'data_inicial': formata_data(rel_obj.data_inicial),
                'data_final': formata_data(rel_obj.data_final),
                'banco': texto_filtro, 
                'empresas': [],
                'total_geral': [],                                            
            }
                
            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')
                                                
            else:
                grupos_empresa = {}
                empresas = []
                linhas = []
                empresa_anterior = None                
                               
                for lancamento_id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor , valor_saldo, nosso_numero, cliente, contato, email_nfe, empresa, situacao, codigo_conta, conta_nome, provisionado, data_atraso  in dados:
                        linha = DicionarioBrasil()
                        linha['cliente'] = cliente              
                        linha['numero_documento'] = numero_documento                       
                        linha['data_vencimento'] = formata_data(data_vencimento)                        
                        linha['valor_saldo'] = D(valor_saldo or 0)                                                     
                        linha['valor_saldo_juros'] = D(valor_saldo or 0) + D(valor_juros or 0) + D(valor_multa or 0)             
                        linha['nosso_numero'] = nosso_numero                        
                        linhas.append(linha)
                        
                        if empresa != empresa_anterior:
                            grupo_empresa = DicionarioBrasil()
                            grupo_empresa['nome'] = empresa                            
                            grupo_empresa['linhas'] = [linha]
                            empresas.append(grupo_empresa)
                            grupos_empresa[empresa] = grupo_empresa
                            empresa_anterior = empresa                            
                            
                        else:
                            grupo_empresa = grupos_empresa[empresa]
                            grupo_empresa.linhas.append(linha)
                            
                #
                # soma subtotais aqui
                #             
                                       
                total_geral = DicionarioBrasil()                
                total_geral['valor_saldo'] = D(0)
                total_geral['valor_saldo_juros'] = D(0)                
                        
                for empresa in empresas:
                    empresa['total'] = DicionarioBrasil()                    
                    empresa.total['valor_saldo'] = D(0)
                    empresa.total['valor_saldo_juros'] = D(0)                    
                            
                    for linha in empresa.linhas:                        
                        empresa.total.valor_saldo       += linha.valor_saldo
                        empresa.total.valor_saldo_juros += linha.valor_saldo_juros                      
                                                                                                
                        linha.valor_saldo       = formata_valor(linha.valor_saldo)
                        linha.valor_saldo_juros = formata_valor(linha.valor_saldo_juros)                            
                   
                    total_geral.valor_saldo       += empresa.total.valor_saldo
                    total_geral.valor_saldo_juros += empresa.total.valor_saldo_juros
                    
                    empresa.total.valor_saldo       = formata_valor(empresa.total.valor_saldo)
                    empresa.total.valor_saldo_juros = formata_valor(empresa.total.valor_saldo_juros)
                    
                total_geral.valor_saldo       = formata_valor(total_geral.valor_saldo)                  
                total_geral.valor_saldo_juros = formata_valor(total_geral.valor_saldo_juros)                  
                  
                         
                dados_relatorio['empresas'] = empresas
                dados_relatorio['total_geral'] = total_geral                                
            
            nome_arquivo = JASPER_BASE_DIR + 'finan_relatorio_posicao_contas.ods'
            
            if tipo == 'R':
                dados_relatorio['titulo']= u'RELATÓRIO POSIÇÃO DE CONTAS A RECEBER'
                nome = 'posicao_contas_receber.' + formato 
            else:
                dados_relatorio['titulo']= u'RELATÓRIO POSIÇÃO DE CONTAS A PAGAR'                            
                nome = 'posicao_contas_pagar.' + formato 

            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados_relatorio, formato=formato)
            
            dados = {
                'nome': nome,
                'arquivo': planilha
            }
            rel_obj.write(dados)
    
        return True


    def gera_relatorio_posiscao_contas_receber(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_posicao_contas(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_posicao_contas_pagar(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_posicao_contas(cr, uid, ids, context=context, tipo='P')

finan_relatorio()
