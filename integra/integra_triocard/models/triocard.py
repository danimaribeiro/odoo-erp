# -*- coding: utf-8 -*-

from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje

def limpa_ecf(texto):
    probibidos = u'.,-_;:?!=+*/#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


class Header_Envio_Triocard(object):
    
    def __init__(self, *args, **kwargs):
                
        self.data_geracao = hoje()        
        self.cnpj_cpf = ''   
        self.funcionarios = []     
                         
    def registro(self):
        
        texto = u'AA'
        texto += ''.ljust(7)
        texto += self.data_geracao.strftime('%d%m%Y')
        texto += ''.ljust(26)
        texto += '1'
        texto += 'USUARIOS'.ljust(9)
        texto += '1' # Forma de geração do arquivo. 1- Normal 2 – Retransmissão/Atualização
        texto += '07'
        texto += ''.ljust(115)
        texto += limpa_formatacao(self.cnpj_cpf).zfill(14)[:14]
        texto += ''.ljust(48)
        texto += str(1).zfill(5)
        texto += 'CR'
        
        return self.tira_acentos(texto.upper())
    
class Funcionario_Envio(object):
    
    def __init__(self, *args, **kwargs):
                         
        self.matricula = ''
        self.cpf = ''        
        self.nome_funcionario = ''        
        self.valor_premio = 0        
        self.valor_limite_saldo = 0        
        self.codigo_setor = ''        
        self.banco = ''        
        self.agencia = ''        
        self.conta_corrente = ''        
        self.cartao = ''        
        self.valor_limite_credito = 0 
        self.cnpj_sindicato = '' 
        self.sequencial = 0                     
                         
    def registro(self):                
             
        texto = u'B1'
        texto += ''.ljust(2)
        texto += ''.ljust(3)
        texto += limpa_ecf(self.matricula).ljust(10)[:11]
        texto += limpa_formatacao(self.cpf).ljust(11)[:11]
        texto += limpa_ecf(self.nome_funcionario).ljust(35)[:35]
        texto += '00'
        texto += '00'
        texto += str(int(self.valor_premio * 100)).zfill(9)[:9]
        texto += str(int(self.valor_limite_saldo * 100)).zfill(9)[:9]
        texto += ''.ljust(20)
        texto += ''.ljust(9)
        texto += self.codigo_setor.ljust(9)[:9]
        texto += self.banco.ljust(4)        
        texto += self.agencia.ljust(6)       
        texto += self.conta_corrente.ljust(12)        
        texto += self.cartao.ljust(20)
        texto += str(int(self.valor_limite_credito * 100)).zfill(9)[:9]
        texto += ''.ljust(7)
        texto += limpa_formatacao(self.cnpj_sindicato).ljust(14)[:14]
        texto += ''.ljust(33)
        texto += str(sequencia).zfill(5)
        texto += 'CR'   
     
        return self.tira_acentos(texto.upper())

class Trailler_Envio_Triocard(object):
    
    def __init__(self, *args, **kwargs):
                
        self.data_geracao = hoje()
        self.total_reg_funcionario = 0
        self.sequencial = 0                
                         
    def registro(self):
                             
        texto = u'ZZ'
        texto += ''.ljust(7)
        texto += self.data_geracao.strftime('%d%m%Y')
        texto += str(total_reg_funcionario).zfill(7)
        texto += ''.ljust(209)
        texto += str(sequencia).zfill(5)       
        texto += 'CR'     
     
        return self.tira_acentos(texto.upper())  
    
    
class Header_Alteracao_Triocard(object):
    
    def __init__(self, *args, **kwargs):
                
        self.data_geracao = hoje()        
        self.cnpj_cpf = ''   
        self.funcionarios = []     
                         
    def registro(self):
        
        texto = u'AA'
        texto += ''.ljust(7)
        texto += self.data_geracao.strftime('%d%m%Y')
        texto += ''.ljust(26)
        texto += '6'
        texto += 'MANUT'.ljust(9)
        texto += '1' # Forma de geração do arquivo. 1- Normal 2 – Retransmissão/Atualização
        texto += '07'
        texto += ''.ljust(115)
        texto += limpa_formatacao(self.cnpj_cpf).zfill(14)[:14]
        texto += ''.ljust(48)
        texto += str(1).zfill(5)
        texto += 'CR'
        
        return self.tira_acentos(texto.upper())     
    
class Funcionario_Alteracao(object):
    
    def __init__(self, *args, **kwargs):
                
        self.cpf = ''        
        self.nome_funcionario = ''        
        self.valor_premio = 0        
        self.valor_limite_saldo = 0        
        self.valor_limite_credito = 0 
        self.acao = ''         
        self.cnpj_sindicato = '' 
        self.tem_sindicato = '' 
        self.sequencial = 0               
                         
    def registro(self):                
                            
        texto = u'B2'
        texto += ''.ljust(15)
        texto += limpa_formatacao(self.cpf).ljust(11)[:11]
        texto += ''.ljust(3)
        texto += limpa_ecf(self.nome_funcionario).ljust(35)[:35]
        texto += ''.ljust(4)
        texto += str(int(self.valor_premio * 100)).zfill(9)[:9]
        texto += str(int(self.valor_limite_saldo * 100)).zfill(9)[:9]
        texto += ''.ljust(81)
        texto += str(int(self.valor_limite_credito * 100)).zfill(9)[:9]
        texto += ''.ljust(6)
        texto += self.acao.ljust(1) # AÇÃO
                                        #A – Alteração de limite e/ou premio
                                        #B – Bloqueio de CPF
                                        #D – Desbloqueio de CPF
                                        #C – Cancelamento de CPF ******
                                        #L – Alteração de Limite
                                        #P – Alteração de Prêmio
                                        #S – Alteração Sindicato
        texto += limpa_formatacao(self.cnpj_sindicato).ljust(14)[:14]
        texto += self.tem_sindicato.ljust(1) #Preenchido com S ou N. Quando S , indica que o funcionário é sindicalizado                 
        texto += ''.ljust(33)
        texto += str(sequencia).zfill(5)
        texto += 'CR'     
     
        return self.tira_acentos(texto.upper()) 
    
class Trailler_Alteracao_Triocard(object):
    
    def __init__(self, *args, **kwargs):
                
        self.data_geracao = hoje()
        self.total_reg_funcionario = 0
        self.sequencial = 0                
                         
    def registro(self):
                             
        texto = u'ZZ'
        texto += ''.ljust(7)
        texto += self.data_geracao.strftime('%d%m%Y')
        texto += str(total_reg_funcionario).zfill(7)
        texto += ''.ljust(208)
        texto += str(sequencia).zfill(5)       
        texto += 'CR'     
     
        return self.tira_acentos(texto.upper())   
