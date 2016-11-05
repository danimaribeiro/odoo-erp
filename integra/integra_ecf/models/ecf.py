# -*- coding: utf-8 -*-

from collections import OrderedDict
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
#from openerp.pychart.svgcanvas import self

def limpa_ecf(texto):
    probibidos = u'.,-_;:?!=+*/#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


class ECF_PRE(object):
    
    def __init__(self, *args, **kwargs):
                
        self.numero_pre_venda = ''
        self.data_hora_emissao = hoje()
        self.codigo_externo_cliente = ''
        self.nome_cliente = ''
        self.cnpj_cpf_cliente = ''
        self.codigo_externo_plano_pagto = ''
        self.sub_total = 0
        self.valor_desconto = 0
        self.valor_acrescimo = 0
        self.total_itens = 0
        self.codigo_externo_vendendor = ''
        self.observacao = ''
        self.rg_inscricao_estatual = ''
        self.endereco = ''
        self.numero = ''
        self.complemento = ''
        self.bairro = ''
        self.cidade = ''
        self.uf = ''
        self.cep = ''
        self.nivel_credito = '0' #Valor validos 0 Bloqueado e 9 Cliente vip. 
                  
    def registro_PRE(self):
        campos = [
            u'PRE',
            str(self.numero_pre_venda)[:20],
            self.data_hora_emissao.strftime('%d%m%Y%H%M%S'),
            str(self.codigo_externo_cliente)[:20],
            limpa_ecf(self.nome_cliente)[:50],
            limpa_formatacao(self.cnpj_cpf_cliente)[:20],
            self.codigo_externo_plano_pagto[:10],
            str('%.2f' %self.sub_total)[:15],
            str('%.2f' %self.valor_desconto)[:15],
            str('%.2f' %self.valor_acrescimo)[:15],
            str('%.2f' %self.total_itens)[:15],
            limpa_ecf(self.codigo_externo_vendendor)[:20],
            str(self.observacao)[:200],
            limpa_formatacao(self.rg_inscricao_estatual)[:20],       
            limpa_ecf(self.endereco)[:50],
            limpa_ecf(self.numero)[:10],
            limpa_ecf(self.complemento)[:30],
            limpa_ecf(self.bairro)[:30],
            limpa_ecf(self.cidade)[:30],
            self.uf[:2],
            limpa_formatacao(self.cep)[:10],
            str(self.nivel_credito)[:1],      
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg
        
class ECF_PIT(object):
    
    def __init__(self, *args, **kwargs):       
        self.sequencia = ''        
        self.codigo_externo_produto = ''
        self.quantidade_produto = 0
        self.preco_unitario = 0
        self.valor_desconto = 0
        self.valor_acrescimo = 0
        self.valor_total = 0
        self.codigo_barras = ''
        self.descricao_produto = ''
        self.complemento_produto = ''
        self.unidade_medida = ''
        self.situacao_tributaria = ''
        self.ICMS = 0
        self.calcula_QTD = 'N'
        self.bloqueia_QTD_frac = 'N'
        self.bloqueia_QTD = 'N'
        self.producao_propria = 'N'
        self.QTD_estoque = ''        
        self.desc_adicional = ''
        self.codvendedor = ''
        self.nomevendedor = ''
        self.gtin_contabil = ''
        self.ext_IPI = ''
        self.gtin_tributavel = ''
        self.ID_ICMS = ''
        self.ID_IPI = ''
        self.ID_ISSQN = ''
        self.ID_II = ''
        self.ID_PIS = ''
        self.ID_PIS_CST = ''
        self.ID_COFINS = ''
        self.ID_COFINS_CST = ''
        self.NCM = ''             

    def registro_PIT(self):
        campos = [
            u'PIT',       
            str(self.sequencia),
            str(self.codigo_externo_produto)[:20],
            str('%.3f' %self.quantidade_produto)[:15],
            str('%.3f' %self.preco_unitario)[:15],
            str('%.2f' %self.valor_desconto)[:15],
            str('%.2f' %self.valor_acrescimo)[:15],
            str('%.2f' %self.valor_total)[:15],
            str(self.codigo_barras)[:20],
            limpa_ecf(self.descricao_produto)[:40],
            limpa_ecf(self.complemento_produto)[:40],
            limpa_ecf(self.unidade_medida)[:4],
            str(self.situacao_tributaria)[:15],
            str('%.2f' %self.ICMS)[:15],
            str(self.calcula_QTD)[:1],
            self.bloqueia_QTD_frac[:1],
            self.bloqueia_QTD[:1],
            self.producao_propria[:1],
            str(self.QTD_estoque),
            self.desc_adicional[:40],
            self.codvendedor[:6],
            self.nomevendedor[:30],
            self.gtin_contabil[:20],
            self.ext_IPI[:20],
            self.gtin_tributavel[:20], 
            str(self.ID_ICMS)[:6], 
            str(self.ID_IPI)[:6],
            str(self.ID_ISSQN)[:6],
            str(self.ID_II)[:6],
            str(self.ID_PIS)[:6],
            str(self.ID_PIS_CST)[:6],
            str(self.ID_COFINS)[:6],
            str(self.ID_COFINS_CST)[:6],
            str(self.NCM)[:20],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg    
    

class ECF_PEN(object):
    def __init__(self, *args, **kwargs):
        self.ecf = ECF_PRE()
        self.ecf = ECF_PIT()
        self.tipo_registro_pen = u'PEN'
        self.endereco = ''
        self.numero = ''
        self.complemento = ''
        self.bairro = ''
        self.cidade = ''
        self.uf = ''
        self.cep = ''
        self.obs = ''           
        self.datahora_entrega = hoje()           

    def registro_PEN(self):
        campos = [
            u'PEN',
            limpa_ecf(self.endereco),
            limpa_ecf(str(self.numero)),
            limpa_ecf(self.complemento),
            limpa_ecf(self.bairro),
            limpa_ecf(self.cidade),
            self.uf,
            limpa_formatacao(self.cep).zfill(8)[:8],
            limpa_ecf(self.obs),
            self.datahora_entrega.strftime('%d%m%Y') ,     
            ''.ljust(39),
            '\r\n',
            ]
        reg = '|' + '|'.join(campos) + '|'
        reg = tira_acentos(reg).upper()
        return reg

class ECF_PPA(object):
    def __init__(self, *args, **kwargs):
        self.ecf = ECF_PRE()
        self.ecf = ECF_PIT()
        self.ecf_PEN = ECF_PEN()
        self.vencimento = hoje()
        self.valor = ''
        self.obs = ''

    def registro_PPA(self):
        campos = [
            u'PPA',                          
            self.vencimento.strftime('%d%m%Y'),     
            str('%.2f' %self.valor)[:15],
            tira_acentos(self.obs)[:80],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg)
        return reg    

class ECF_PFP(object):
    def __init__(self, *args, **kwargs):
        self.ecf = ECF_PRE()
        self.ecf = ECF_PIT()
        self.ecf_PEN = ECF_PEN()
        self.ecf_PPA = ECF_PPA()
        self.identificacao_forma_pagto = ''
        self.valor = ''

    def registro_PFP(self):
        campos = [
            u'PFP',       
            limpa_ecf(self.identificacao_forma_pagto),
            str(self.valor),
            ''.ljust(39),
            '\r\n',
            ]
        reg = '|' + '|'.join(campos) + '|'
        reg = tira_acentos(reg).upper()
        return reg 

class ECF_PRG(object):
    def __init__(self, *args, **kwargs):
        self.ecf = ECF_PRE()
        self.ecf = ECF_PIT()
        self.ecf_PEN = ECF_PEN()
        self.ecf_PPA = ECF_PPA()
        self.ecf_PFP = ECF_PFP()        
        self.arquivo_prg = ''        

    def registro_PRG(self):
        campos = [
            self.arquivo_prg,
            ''.ljust(39),
            '\r\n',
            ]
        reg = '|' + '|'.join(campos) + '|'
        reg = tira_acentos(reg).upper()
        return reg 
