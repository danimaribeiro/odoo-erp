# -*- coding: utf-8 -*-

from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje 



def limpa_nfes(texto):
    probibidos = u'.,-_;:?!=+*/&#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


class REGISTRO_1(object):
    def __init__(self, *args, **kwargs):
        self.tipo_registro = '1'
        self.incricao_contribuinte = ''
        self.versao_layout = 'PMB002'
        self.indentificador_remessa = 0
        self.fim_linha = ''
        
    def registro(self):
        reg = self.tipo_registro
        reg += self.incricao_contribuinte[:7]
        reg += self.versao_layout.ljust(6)
        reg += str(self.indentificador_remessa).zfill(11)[:11]
        reg += self.fim_linha
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class REGISTRO_2(object):
    def __init__(self, *args, **kwargs):
        
        self.tipo_registro = '2'
        self.tipo_rps = 'RPS'
        self.serie_rps = ''
        self.serie_nfe = ''
        self.numero_rps = 0
        self.data_emissao_rps = hoje()
        self.hora_rps = hoje()
        self.situacao_rps = 'E'
        self.codigo_motivo_cancelamento = ''
        self.numero_nf_cancelada = 0
        self.serie_nf_cancelada = ''
        self.data_emissao_nfe_cancelada = ''
        self.descricao_cancelamento = ''
        self.codigo_servico_prestado = 0
        self.local_prestacao_servico = ''
        self.servico_prestado_via_publica = '2' 
        
        self.endereco_servico_prestado = ''  
        self.numero_servico_prestado = ''  
        self.complemento_servico_prestado = ''  
        self.bairro_servico_prestado = ''  
        self.cidade_servico_prestado = ''  
        self.uf_servico_prestado = ''  
        self.cep_servico_prestado = ''
        self.quantidade_servico_prestado = 0
        self.valor_servico_prestado = 0
        self.reservado = ''
        self.valor_total_retencoes = 0
        
        self.tomador_estrangeiro = '2'         
        self.pais_nacionalidade_tomador_estrangeiro = '001' 
        self.servico_exportacao = '2' 
        self.indicador_tomador = '2'  
        self.cpf_cnpj_tomador = ''  
        self.razao_social_tomador = ''  
        self.endereco_tomador = ''  
        self.numero_tomador = ''  
        self.complemento_tomador = ''  
        self.bairro_tomador = ''  
        self.cidade_tomador = ''  
        self.uf_tomador = ''  
        self.cep_tomador = ''  
        self.email_tomador = ''  
        self.numero_fatura = 0  
        self.valor_fatura = 0  
        self.forma_pagamento = ''  
        self.discriminacao_servico = ''  
        self.fim_linha = ''  
                
               
    def registro(self):
       
        reg = self.tipo_registro # 1-1 tipo registro
        reg += self.tipo_rps.ljust(5) # 2-6 RPS
        reg += self.serie_rps.ljust(4)[:4] # 7-10 série do RPS    
        reg += self.serie_nfe.ljust(5)[:5] # 11-15 série do nfe
        reg += str(self.numero_rps).zfill(10)[:10] # 16-25 numero rps        
        reg += self.data_emissao_rps.strftime('%Y%m%d') # 26-33 data emissao rps
        reg += self.hora_rps.strftime('%H%M%S') # 34-39 hora emissao rps
        reg += self.situacao_rps.ljust(1) # 40-40 situacao E enviado C cancelado
        
        if self.situacao_rps == 'C':
            reg += self.codigo_motivo_cancelamento.ljust(2)[:2] # 41-42 motivo cancelamento 
            reg += str(self.numero_nf_cancelada).zfill(7)[:7] # 43-49 numero nf cancelada
            reg += self.serie_nf_cancelada.ljust(5)[:5] # 50-54 serie nf cancelada
            reg += self.data_emissao.strftime('%Y%m%d') # 55-62  data emissao nfe cancelada  
            reg += self.descricao_cancelamento.ljust(180)[:180] # 63-242 descrisacao cancelamento
        else:
            reg += self.codigo_motivo_cancelamento.ljust(2)
            reg += str(self.numero_nf_cancelada).zfill(7)[:7]
            reg += self.serie_nf_cancelada.ljust(5)[:5]
            reg += self.data_emissao_nfe_cancelada.ljust(8)[:8]                                    
            reg += self.descricao_cancelamento.ljust(180)[:180]
            
        reg += str(self.codigo_servico_prestado).zfill(9)[:9] # 243-251 codigo serviço
        reg += self.local_prestacao_servico.ljust(1) # 252-252 local prestacao
        reg += self.servico_prestado_via_publica.ljust(1) # 253-253 servico prestado em via publica
        reg += self.endereco_servico_prestado.ljust(75)[:75] # 254-328 endereco local servico prestado
        reg += self.numero_servico_prestado.ljust(9)[:9] # 329-337 numero local servico prestado
        reg += self.complemento_servico_prestado.ljust(30)[:30] # 338-367 complemento local servico prestado 
        reg += self.bairro_servico_prestado.ljust(40)[:40] # 368-407 bairro local servico prestado
        reg += self.cidade_servico_prestado.ljust(40)[:40] # 408-447 bairro local servico prestado
        reg += self.uf_servico_prestado.ljust(2) # 448-449 uf local servico prestado 
        reg += limpa_formatacao(self.cep_servico_prestado).ljust(8)[:8] # 450-457 cep local servico prestado
        reg += str(int(self.quantidade_servico_prestado)).zfill(6)[:6] # 458-463 quantidade servico prestado
        reg += str(int(self.valor_servico_prestado) * 100).zfill(15)[:15] # 464-478 valor servico prestado 
        reg += self.reservado.ljust(5) # 479-483 reservado
        reg += str(int(self.valor_total_retencoes) * 100).zfill(15)[:15] # 484-498 valor total retencoes         
        reg += self.tomador_estrangeiro.ljust(1) # 499-499 tomador estrangeiro ? 1 : 2
        reg += self.pais_nacionalidade_tomador_estrangeiro.zfill(3) # 500-502 pais tomador estrangeiro 
        reg += self.servico_exportacao.zfill(1) # 503-503 servico prestado exportacao
        reg += self.indicador_tomador.zfill(1) # 504-504 indicador cpf 1 : cnpj  2 
        reg += limpa_formatacao(self.cpf_cnpj_tomador).zfill(14)[:14] # 505 518 cnpj 
        reg += self.razao_social_tomador.ljust(60)[:60] # 519-578 razao social tomador
        reg += self.endereco_tomador.ljust(75)[:75] # 579-653 endereço tomador
        reg += self.numero_tomador.ljust(9)[:9] # 654-662 numero tomador
        reg += self.complemento_tomador.ljust(30)[:30] # 663-692 complemento tomador  
        reg += self.bairro_tomador.ljust(40)[:40] # 693-732 bairro tomador 
        reg += self.cidade_tomador.ljust(40)[:40] # 733-772 cidade tomador
        reg += self.uf_tomador.ljust(2)[:2] # 773-774 uf tomador
        reg += limpa_formatacao(self.cep_tomador).ljust(8) # 775-782 cep tomador
        reg += self.email_tomador.strip().ljust(152)[:152] # 783-934 email tomador
        reg += str(self.numero_fatura).zfill(6)[:6] # 935-940 numero fatura
        reg += str(int(self.valor_fatura * 100)).zfill(15)[:15] # 941-955 valor fatura
        reg += self.forma_pagamento.ljust(15)[:15] # 956-970 forma de pagamento
        reg += self.discriminacao_servico.ljust(1000)[:1000] # 971-1970 discriminção serviço 
        reg += self.fim_linha
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class REGISTRO_3(object):
    def __init__(self, *args, **kwargs):
        
        self.tipo_registro = '3'
        self.codigo_outros_valores = ''
        self.valor = 0
        self.fim_linha = ''
        
    def registro(self):
        reg = self.tipo_registro
        reg += self.codigo_outros_valores.zfill(2)[:2]
        reg += str(int(self.valor * 100 )).zfill(15)[:15]
        reg += self.fim_linha
        reg += '\r\n'
        #reg = tira_acentos(reg).upper()
        return reg

class REGISTRO_9(object):
    def __init__(self, *args, **kwargs):
        
        self.tipo_registro = '9'
        self.numero_total_linha = 0        
        self.valor_total_servico = 0
        self.valor_total_servico_registro3 = 0
        self.fim_linha = ''
        
    def registro(self):
        reg = self.tipo_registro[:1]
        reg += str(self.numero_total_linha).zfill(7)[:7]
        reg += str(int(self.valor_total_servico * 100)).zfill(15)[:15]
        reg += str(int(self.valor_total_servico_registro3 * 100)).zfill(15)[:15]        
        reg += self.fim_linha
        reg += '\r\n'        
        return reg
