# -*- coding: utf-8 -*-
#
# Geração do arquivo do SPED Fiscal
#

from __future__ import division, print_function, unicode_literals

import os
import StringIO
from pybrasil.data import hoje, parse_datetime, data_hora_horario_brasilia
from pybrasil.valor.decimal import Decimal as D
from copy import copy
from pybrasil.inscricao import limpa_formatacao
from osv import osv, fields
from pybrasil.valor import formata_valor
from sped.constante_tributaria import *
from sped.models.sped_calcula_impostos import calcula_item
from time import time
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import datetime


def formata_valor_sped(numero, decimais=2):
    numero = D(numero)

    if decimais:
        numero = numero.quantize(D('0.' + ''.zfill(decimais-1) + '1'))

    return formata_valor(numero, casas_decimais=decimais, separador_milhar='')


class SPEDEcd(object):
    def __init__(self):
        self.finalidade = '0'
        self.filial = None
        self.data_inicial = hoje()
        self.data_final = hoje()
        self.data_final = None
                
        self.movimentos_blocos = {
            '0': True,
            'I': False,
            'J': False,            
            '9': True,
        }
        self.totais_registros = {
            'geral': 0
        }
    
    def gera_arquivo(self, nome_arquivo=''):
        #self._arq = file(nome_arquivo, 'w')
        self._arq = StringIO.StringIO()
        
        #
        # Abertura do arquivo
        #
        self.registro_0000()
        #
        # Bloco 0
        #
        self.registro_inicial_bloco('0')
        self.registro_0007()  # Outras Inscrições
        self.registro_0020()  # Filiais 
        #self.registro_0035()  # cadastro participante da SCP
        #self.registro_0150()  # Participantes 
        #self.registro_0180()  # Relacionamento com participantes        
        self.registro_final_bloco('0')

        #
        # Bloco I
        #
        self.registro_inicial_bloco('I')
        self.registro_I010()
        #self.registro_I012() livro auxliar
        #self.registro_I015()
        #self.registro_I020() campos adicionais
        self.registro_I030()
        self.registro_I050()
        #self.registro_I051()
        #self.registro_I052()
        #self.registro_I053()
        self.registro_I075()
        self.registro_I100()
        self.registro_I150()
        #self.registro_I151()
        self.registro_I155()
        #self.registro_I157()
        self.registro_I200()
        #self.registro_I300()
        #self.registro_I310()
        #self.registro_I350()
        #self.registro_I355()
        #self.registro_I355()
        #self.registro_I500()
        #self.registro_I510()
        #self.registro_I550()
        #self.registro_I555()        
        self.registro_final_bloco('I')

        #
        # Bloco J
        #
        self.registro_inicial_bloco('J')        
        #self.registro_J100()
        #self.registro_J150()
        #self.registro_J200()
        #self.registro_J210()
        #self.registro_J215()
        #self.registro_J800()        
        self.registro_J900()        
        #self.registro_J930()        
        #self.registro_J935()                    
        self.registro_final_bloco('J')

        #
        # Bloco 9
        #
        self.registro_inicial_bloco('9')
        self.registro_9900()
        self.registro_final_bloco('9')

        #
        # Encerramento do arquivo
        #
        self.registro_9999()
        
        self.arquivo = self._arq.getvalue()             
        arquivo = self.arquivo.decode('iso-8859-1')
                     

        arquivo = arquivo.replace('TOTAL_J900', str(self.totais_registros['geral']))
        arquivo = arquivo.replace('TOTAL_I030', str(self.totais_registros['geral']))
        
        self.arquivo = arquivo.encode('iso-8859-1')
        
        self._arq.close()

    def _grava_registro(self, registro):
        self._arq.write(registro.encode('iso-8859-1'))

    def registro_inicial_bloco(self, bloco):
        self.totais_registros['geral'] += 1
        self.totais_registros[bloco + '001'] = 1

        reg = '|' + bloco + '001'

        if self.movimentos_blocos[bloco] and bloco == 'J001':
            reg += '|0'
        else:
            reg += '|1'

        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_final_bloco(self, bloco):
        self.totais_registros['geral'] += 1
        self.totais_registros[bloco + '990'] = 1

        reg = '|' + bloco + '990'
        
        total = 0  
        for tipo_registro, quantidade in self.totais_registros.iteritems():
            if tipo_registro[0] == bloco:
                total += quantidade
                
        reg += '|' + unicode(total)
        reg += '|\r\n'        
        self._grava_registro(reg)            

    def _busca_ids(self, sql, dados={}, varios_campos=False):
        dados_sql = {
            'cnpj': self.filial_a_gerar.cnpj_cpf,
            'data_inicial': self.data_inicial.strftime('%Y-%m-%d'),
            'data_final': self.data_final.strftime('%Y-%m-%d'),                    
        }
        dados_sql.update(dados)
        sql_gerar = sql.format(**dados_sql)
        sql_gerar = sql_gerar.replace(', )', ')')
        sql_gerar = sql_gerar.replace(',)', ')')

        print(sql_gerar)

        self.cr.execute(sql_gerar)

        dados = self.cr.fetchall()
        ids = []

        if not varios_campos:
            for id, in dados:
                if id not in ids:
                    ids.append(id)
        else:
            ids = dados

        return ids

    #
    # Bloco 0
    # Abertura, identificação e referências
    #
    def registro_0000(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0000'] = 1
        self.filial_a_gerar = self.filial
        self.prepara_ids()

        reg = '|0000'
        reg += '|LECD'         
        reg += '|' + self.data_inicial.strftime('%d%m%Y')
        reg += '|' + self.data_final.strftime('%d%m%Y')
        reg += '|' + self.filial.razao_social.strip()

        #
        # CNPJ ou CPF
        #
        reg += '|' + limpa_formatacao(self.filial.cnpj_cpf)
        reg += '|' + self.filial.estado
        reg += '|' #+ limpa_formatacao(self.filial.ie or '').strip()
        reg += '|' + self.filial.municipio_id.codigo_ibge[:7]
        reg += '|' + limpa_formatacao(self.filial.im or '').strip()
        reg += '|'
        reg += '|' + self.finalidade
        
        if self.filial.nire:
            reg += '|1'
            reg += '|0'
        else:    
            reg += '|0'
            reg += '|0'
            
        reg += '|'
        reg += '|'
        reg += '|0'
        reg += '|0'
        reg += '|'                       
        reg += '|N'                       
        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_0007(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0007'] = 1

        reg = '|0007'
        reg += '|' 
        reg += '|' 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_0020(self):
        if len(self.filiais_ids) == 0:
            return ''

        self.totais_registros['0020'] = 0
        partner_pool = self.filial.pool.get('res.partner')
        
        ja_foi = []
        for filial in partner_pool.browse(self.cr, 1, self.filiais_ids):
            if filial.cnpj_cpf in ja_foi:
                continue

            ja_foi.append(filial.cnpj_cpf)
            self.totais_registros['geral'] += 1
            self.totais_registros['0020'] += 1            
        
            reg = '|0020'
            reg += '|0'
            reg += '|' + limpa_formatacao(filial.cnpj_cpf)  
            reg += '|' + filial.estado     
            reg += '|' + limpa_formatacao(filial.ie or '').strip()
            reg += '|' + filial.municipio_id.codigo_ibge[:7]
            reg += '|' + limpa_formatacao(filial.im or '').strip()
            reg += '|' + limpa_formatacao(filial.nire or '').strip()            
            reg += '|\r\n'
            self._grava_registro(reg)

    def registro_0035(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0035'] = 1
        
        reg = '|0035'
        reg += '|' 
        reg += '|' 
        reg += '|\r\n'
        self._grava_registro(reg)
        

    def registro_0150(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0150'] = 1
        
        reg = '|0150'
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_0180(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0180'] = 1
        
        reg = '|0180'
        reg += '|' 
        reg += '|' 
        reg += '|\r\n'
        self._grava_registro(reg)

    #
    # Bloco I
    # Identificação da escrituração contábil
    #
    def registro_I010(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I010'] = 1
        
        reg = '|I010'
        reg += '|G' 
        reg += '|4.00' 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I012(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I012'] = 1
        
        reg = '|I012'
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|'         
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I015(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I015'] = 1
        
        reg = '|I015'
        reg += '|'         
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I020(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I020'] = 1
        
        reg = '|I020'
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|' 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I030(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I030'] = 1
        
        reg = '|I030'
        reg += '|TERMO DE ABERTURA' 
        reg += '|1' # Numero de ordem 
        reg += '|ESCRITURACAO CONTABIL' 
        reg += '|TOTAL_I030' #QUANTIDE DE LINHAS REG
        reg += '|' + self.filial.razao_social.strip() 
        reg += '|' + limpa_formatacao(self.filial.nire or '').strip() 
        reg += '|' + limpa_formatacao(self.filial.cnpj_cpf)
        reg += '|' 
        reg += '|' 
        reg += '|' + self.filial.municipio_id.nome
        reg += '|' + self.data_final.strftime('%d%m%Y')
        reg += '|\r\n'
        self._grava_registro(reg)
        

    def registro_I050(self): 
        
        if len(self.contas_ids) == 0:
            return ''

        self.totais_registros['I050'] = 0
        conta_pool = self.filial.pool.get('finan.conta')       

        for conta in conta_pool.browse(self.cr, 1, self.contas_ids):
     
            self.totais_registros['geral'] += 1
            self.totais_registros['I050'] += 1
            
            reg = '|I050'
            if conta.data:
                reg += '|' + parse_datetime(conta.data).date().strftime('%d%m%Y')
            else:
                raise osv.except_osv((u'Inválido !'), (u'Conta: {a}, deve ter obrigatoriamente uma Data.'.format(a=conta.codigo_completo)))
            
            if conta.tipo == 'A':
                reg += '|01' 
            elif conta.tipo == 'P':
                reg += '|02'
            elif conta.tipo == 'PL':
                reg += '|03'                            
            elif conta.tipo in ['R','C','D']:
                reg += '|04'             
            elif conta.tipo == '5':
                reg += '|04'             
            elif conta.tipo == 'O':
                reg += '|09' 
            
            if conta.sintetica:
                reg += '|S'
            else:  
                reg += '|A'
            if conta.nivel_conta > 4:
                reg += '|' + '4' 
            else:        
                reg += '|' + str(conta.nivel_conta) 
            reg += '|' + conta.codigo_completo
            if conta.parent_id:
                reg += '|' + conta.parent_id.codigo_completo
            else:
                reg += '|' 
            reg += '|' + conta.nome
            reg += '|\r\n'
            self._grava_registro(reg)
    
    def registro_I051(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I051'] = 1
        
        reg = '|I051'
        reg += '|'         
        reg += '|'         
        reg += '|'         
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I052(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I052'] = 1
        
        reg = '|I052'
        reg += '|'         
        reg += '|'                 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I053(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I053'] = 1
        
        reg = '|I053'
        reg += '|'         
        reg += '|'                 
        reg += '|'                 
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I075(self):        
        
        historico_pool = self.filial.pool.get('finan.historico')
        historico_ids = historico_pool.search(self.cr, 1, [])        
        
        if len(historico_ids) == 0:
            return ''
        self.totais_registros['I075'] = 0               

        for historico_obj in historico_pool.browse(self.cr, 1, historico_ids):
    
            self.totais_registros['geral'] += 1
            self.totais_registros['I075'] += 1
            
            reg = '|I075'
            reg += '|' + str(historico_obj.codigo)
            if historico_obj.nome:         
                reg += '|' + historico_obj.nome
            else:                                            
                reg += '|' 
            reg += '|\r\n'
            self._grava_registro(reg)
        
    def registro_I100(self):                
        cc_pool = self.filial.pool.get('finan.centrocusto')
        cc_ids = cc_pool.search(self.cr, 1, [('tipo','=','C')])        
        
        if len(cc_ids) == 0:
            return ''
        self.totais_registros['I100'] = 0
                
        for cc_obj in cc_pool.browse(self.cr, 1, cc_ids):
            self.totais_registros['geral'] += 1
            self.totais_registros['I100'] += 1
            
            reg = '|I100'
            if cc_obj.data:
                reg += '|' + parse_datetime(cc_obj.data).date().strftime('%d%m%Y')
            else:
                raise osv.except_osv((u'Inválido !'), (u'O Centro de Custo: {a},  deve ter obrigatoriamente uma Data.'.format(a=cc_obj.codigo)))
            reg += '|' + str(cc_obj.codigo_completo)
            reg += '|' + cc_obj.nome
            reg += '|\r\n'
            self._grava_registro(reg)
    
    def registro_I150(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I150'] = 1
        
        reg = '|I150'
        reg += '|' + self.data_inicial.strftime('%d%m%Y')
        reg += '|' + self.data_final.strftime('%d%m%Y')                    
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I151(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I151'] = 1
        
        reg = '|I151'
        reg += '|'                     
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_I155(self):        
                
        conta_pool = self.filial.pool.get('finan.conta')
        
        sql = """select 
            l.conta_id,
            coalesce((select
                    coalesce(sum(es.saldo),0)  as saldo_anterior    
                    from ecd_saldo es                                       
                    where                
                    es.data = cast('{data_inicial}' as date) + interval '-1 day'
                    and es.conta_id = l.conta_id                                
                    and es.cnpj_cpf = l.cnpj_cpf ),0) as saldo_anterior,    
            sum(l.vr_debito) as vr_debito,
            sum(l.vr_credito) as vr_credito    
            
        from ecd_razao_view l       
        where 
            l.cnpj_cpf like '{cnpj_raiz}%'
            and l.data_lancamento between '{data_inicial}' and '{data_final}'
            group by 
                l.cnpj_cpf,
                l.codigo_completo,
                l.conta_id
            order by
            codigo_completo;            
        """        
        
        sql = sql.format(cnpj_raiz=self.filial.cnpj_cpf[:11],data_inicial=self.data_inicial, data_final=self.data_final)        
        self.cr.execute(sql)
        dados = self.cr.fetchall()
        
        if len(dados) == 0:
             return ''
        self.totais_registros['I155'] = 0
        
        for conta_id, saldo_anterior, total_debito, total_credito in dados:
            self.totais_registros['geral'] += 1
            self.totais_registros['I155'] += 1
            
            conta_obj = conta_pool.browse(self.cr, 1, conta_id)
            saldo_atual = saldo_anterior + total_debito - total_credito
            
            reg = '|I155'
            reg += '|' + conta_obj.codigo_completo                    
            reg += '|'                     
            reg += '|' + str(formata_valor_sped(saldo_anterior)).replace('-', '')
            if saldo_anterior >= 0 :
                reg += '|D'                     
            else:
                reg += '|C'                     
                                   
            reg += '|' + str(formata_valor_sped(total_debito)).replace('-', '')                    
            reg += '|' + str(formata_valor_sped(total_credito)).replace('-', '')
            reg += '|' + str(formata_valor_sped(saldo_atual)).replace('-', '')
            
            if saldo_atual >= 0:
                reg += '|D'                     
            else:
                reg += '|C'         
                            
            reg += '|\r\n'
            self._grava_registro(reg)
            
    def registro_I157(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I157'] = 1
        
        reg = '|I157'
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|\r\n'
        self._grava_registro(reg)
    
    def registro_I200(self):                          
        if len(self.lancamentos_ids) == 0:
            return ''
        self.totais_registros['I200'] = 0
        self.totais_registros['I250'] = 0
        lancamento_pool = self.filial.pool.get('ecd.lancamento.contabil')
                
        for lancamento_obj in lancamento_pool.browse(self.cr, 1, self.lancamentos_ids):
            self.totais_registros['geral'] += 1
            self.totais_registros['I200'] += 1
            
            valor =D(0)
            for partida in lancamento_obj.partida_ids:
                valor += D(partida.vr_debito)
                    
            reg = '|I200'
            reg += '|' + str(lancamento_obj.codigo)
            reg += '|' + parse_datetime(lancamento_obj.data).date().strftime('%d%m%Y')
            reg += '|' +   str(formata_valor_sped(valor))
            reg += '|' +  lancamento_obj.tipo            
            reg += '|\r\n'
            self._grava_registro(reg)
            
            for partida in lancamento_obj.partida_ids:
                self.totais_registros['geral'] += 1
                self.totais_registros['I250'] += 1
                
                reg = '|I250'
                reg += '|' + partida.conta_id.codigo_completo
                
                if partida.centrocusto_id:
                    reg += '|' + partida.centrocusto_id.codigo_completo
                else:
                    reg += '|'
                
                if partida.tipo == 'D':
                    reg += '|' + str(formata_valor_sped(partida.vr_debito))
                    reg += '|D' 
                else:
                    reg += '|' + str(formata_valor_sped(partida.vr_credito))
                    reg += '|C'
                      
                reg += '|'
                 
                if partida.historico_id.codigo:
                    reg += '|' + str(partida.historico_id.codigo)
                else:
                    reg += '|'
                     
                reg += '|' + partida.historico
                reg += '|' 
                reg += '|\r\n'
                self._grava_registro(reg)
                
    def registro_I300(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I300'] = 1
        
        reg = '|I300'
        reg += '|' + self.data_inicial.strftime('%d%m%Y')                    
        reg += '|\r\n'
        self._grava_registro(reg)       
        
    def registro_I310(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I310'] = 1
        
        reg = '|I310'
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I350(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I350'] = 1
        
        reg = '|I350'
        reg += '|' + self.data_inicial.strftime('%d%m%Y')
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I355(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I355'] = 1
        
        reg = '|I355'
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|'                     
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I500(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I500'] = 1
        
        reg = '|I500'
        reg += '|10'                                              
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I510(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I510'] = 1
        
        reg = '|I510'
        reg += '|'                                              
        reg += '|'                                              
        reg += '|'                                              
        reg += '|'                                              
        reg += '|'                                              
        reg += '|'                                              
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I550(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I550'] = 1
        
        reg = '|I550'
        reg += '|'                                              
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_I555(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['I555'] = 1
        
        reg = '|I555'
        reg += '|'                                              
        reg += '|\r\n'
        self._grava_registro(reg)
                
    def registro_J005(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J005'] = 1
        
        reg = '|J005'
        reg += '|' + self.data_inicial.strftime('%d%m%Y')                                         
        reg += '|' + self.data_final.strftime('%d%m%Y')                                         
        reg += '|1'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_J010(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J010'] = 1
        
        reg = '|J010'
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_J150(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J150'] = 1
        
        reg = '|J150'
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_J200(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J200'] = 1
        
        reg = '|J200'
        reg += '|'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_J210(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J210'] = 1
        
        reg = '|J210'
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
               
    def registro_J215(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J215'] = 1
        
        reg = '|J215'
        reg += '|'                                          
        reg += '|'                                          
        reg += '|'                                          
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_J800(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J800'] = 1
        
        reg = '|J800'
        reg += '|'                                          
        reg += '|'                                                                                      
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_J900(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J900'] = 1
        
        reg = '|J900'        
        reg += '|TERMO DE ENCERRAMENTO'
        reg += '|' + str(self.numero_livro)
        reg += '|DIARIO GERAL' 
        reg += '|' + self.filial.razao_social.strip()                                         
        reg += '|TOTAL_J900' 
        reg += '|' + self.data_inicial.strftime('%d%m%Y')                                         
        reg += '|' + self.data_final.strftime('%d%m%Y')                                                                                       
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_J930(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J930'] = 1
        
        reg = '|J930'
        reg = '|'                                                                                               
        reg += '|\r\n'
        self._grava_registro(reg)
        
    def registro_J935(self):        
        self.totais_registros['geral'] += 1
        self.totais_registros['J935'] = 1
        
        reg = '|J935'
        reg = '|'                                                                                               
        reg += '|\r\n'
        self._grava_registro(reg)
    #
    #
    #
    #
    # Bloco 9
    # Controle e encerramento do arquivo digital
    #
    def registro_9900(self):
        #
        # Temos que considerar o total dos registros 9990 e 9999 também
        #
        self.totais_registros['9900'] = 0
        self.totais_registros['9990'] = 1
        self.totais_registros['9999'] = 1

        tipos_registro = self.totais_registros.keys()
        #tipos_registro.sort()

        for tipo_registro in tipos_registro:
            if (tipo_registro != 'geral') and (tipo_registro != '9900'):
                self.totais_registros['geral'] += 1
                self.totais_registros['9900'] += 1
                reg = '|9900'
                reg += '|' + tipo_registro
                reg += '|' + unicode(self.totais_registros[tipo_registro])
                reg += '|\r\n'
                self._grava_registro(reg)

        self.totais_registros['geral'] += 1
        self.totais_registros['9900'] += 1
        reg = '|9900'
        reg += '|9900'
        reg += '|' + unicode(self.totais_registros['9900'])
        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_9999(self):
        self.totais_registros['geral'] += 1
        reg = '|9999'
        reg += '|' + unicode(self.totais_registros['geral'])
        reg += '|\r\n'
        self._grava_registro(reg)
                

    def prepara_ids(self):
        #
        # Filiais
        #
        
        self.sql_filiais = """       
        select distinct
            rp.id
        from res_company c
        join res_partner rp on rp.id = c.partner_id
        where 
            rp.cnpj_cpf like '{cnpj_raiz}%' 
            and rp.cnpj_cpf not ilike '{cnpj_matriz}%';
        """        
        
        self.filiais_ids = self._busca_ids(self.sql_filiais, {'cnpj_raiz': self.filial.cnpj_cpf[:11],'cnpj_matriz': self.filial.cnpj_cpf[:15]})
        
        self.sql_contas = """       
        select distinct
            fc.id
        from finan_conta fc 
        join ecd_plano_conta ep on ep.id = fc.plano_id
        join res_company c on c.plano_id = ep.id
        join res_partner rp on rp.id = c.partner_id
        where 
            rp.cnpj_cpf like '{cnpj_raiz}%';            
        """        
        
        self.contas_ids = self._busca_ids(self.sql_contas, {'cnpj_raiz': self.filial.cnpj_cpf[:11]})
        
        
        self.sql_lancamento = """       
        select distinct 
            l.id 
        from ecd_lancamento_contabil l
        join ecd_partida_lancamento pl on pl.lancamento_id = l.id and pl.cnpj_cpf = l.cnpj_cpf
        
        where 
        pl.cnpj_cpf like '{cnpj_raiz}%'
         and l.data between '{data_inicial}' and '{data_final}';            
        """        
        
        self.lancamentos_ids = self._busca_ids(self.sql_lancamento, {'cnpj_raiz': self.filial.cnpj_cpf[:11],'data_inicial': self.data_inicial, 'data_final': self.data_final })
        
       
      