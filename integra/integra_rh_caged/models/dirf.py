# -*- coding: utf-8 -*-

from collections import OrderedDict
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje



def limpa_dirf(texto):
    probibidos = u'.,-_;:?!=+*/#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, u' ')

    while u'  ' in texto:
        texto = texto.replace(u'  ', u' ')

    return texto

REGISTRO_DIRF_RUBRICA = {
    'RTRT': ['BASE_INSS', 'BASE_INSS_13'],
    'RTPO': ['INSS','INSS_13', 'INSS_anterior'],
    'RTPP':[''],
    'RTDP': ['DEDUCAO_DEPENDENTES'],
    'RTPA': ['PENSAO_ALIMENTICIA'],
    'RTIRF': ['IRPF', 'IRPF_13', 'IRPF_FERIAS'],
    'CJAC': [''],
    'CJAA': [''],
    'ESRT': [''],
    'ESPO': [''],
    'ESPP': [''],
    'ESDP': [''],
    'ESPA': [''],
    'ESIR': [''],
    'ESDJ': [''],
    'RIDAC': ['ajuda_custo', 'AJUDA_CUSTO'],
    'RIIRP': ['FERIAS_PROPORCIONAL', 'FERIAS_PROPORCIONAL_1_3', 'FERIAS_VENCIDA', 'FERIAS_VENCIDA_1_3'],
    'RIAP': ['ABONO', 'ABONO_1_3'],
    'RIP65': [''],
    'RIO': [''],
}


REGISTRO_DIRF_RUBRICA_ORDEM = [
    'RTRT',
    'RTPO',
    'RTPP',
    'RTDP',
    'RTPA',
    'RTIRF',
   # 'CJAC',
   # 'CJAA',
   # 'ESRT',
   # 'ESPO',
   # 'ESPP',
   # 'ESDP',
   # 'ESPA',
   # 'ESIR',
   # 'ESDJ',
    'RIDAC',
    'RIIRP',
    'RIAP',
    #'RIP65',
   # 'RIO',
]


class DIRF(object):
    def __init__(self, *args, **kwargs):

        self.ano_referencia = 2016
        self.ano_calendario = 2015
        self.indicador_retificadora = 'N'
        self.numero_recibo = ''
        self.identificador_estrutura_leiaute = 'L35QJS2'

        self.cpf_respo = ''
        self.nome_respo = ''
        self.ddd = ''
        self.telefone = ''
        self.ramal = ''
        self.fax = ''
        self.correio_eletronico = ''

    def registro_DIRF(self):
        campos = [
            str(self.ano_referencia)[:4],
            str(self.ano_calendario)[:4],
            self.indicador_retificadora[:1],
            self.numero_recibo.ljust(12)[:12],
            self.identificador_estrutura_leiaute[:7],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(unicode(reg)).upper()
        rege =  u'Dirf|' + reg
        return rege

    def registro_RESPO(self):
        campos = [
            u'RESPO',
            limpa_formatacao(self.cpf_respo)[:11],
            limpa_dirf(self.nome_respo)[:60],
            self.ddd[:2],
            self.telefone.zfill(9)[:9],
            self.ramal[:6],
            self.fax[:9],
            self.correio_eletronico[:50],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg

    def registro_FIM(self):
        campos = [
            u'FIMDirf',
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg)
        return reg


class DIRF_DECPJ(object):
    def __init__(self, *args, **kwargs):
        self.cnpj = ''
        self.nome_empresarial = ''
        self.natureza_declarante = '0'
        self.cpf_responsavel = ''
        self.indicador_socio_ostensivo = 'N'
        self.indicador_declarante_decisao_judicial = 'N'
        self.indicador_instituicao_fundo_investimento = 'N'
        self.indicador_declarante_rendimentos_exterior = 'N'
        self.indicador_privado_assistencia_saude = 'N'
        self.indicador_pagamentos_Copa = 'N'
        self.indicador_pagamentos_jogos_olimpicos = 'N'
        self.indicador_situacao_especial_declaracao = 'N'
        self.data_evento_decpj = ''
        self.codigo_receita_idrec = '0561'

    def registro_DECPJ(self):
        campos = [
            u'DECPJ',
            limpa_formatacao(self.cnpj)[:14],
            limpa_dirf(self.nome_empresarial)[:150],
            self.natureza_declarante[:1],
            limpa_formatacao(self.cpf_responsavel)[:11],
            self.indicador_socio_ostensivo[:1],
            self.indicador_declarante_decisao_judicial[:1],
            self.indicador_instituicao_fundo_investimento[:1],
            self.indicador_declarante_rendimentos_exterior[:1],
            self.indicador_privado_assistencia_saude[:1],
            self.indicador_pagamentos_Copa[:1],
            self.indicador_pagamentos_jogos_olimpicos[:1],
            self.indicador_situacao_especial_declaracao[:1],
            self.data_evento_decpj[:8],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg

    def registro_IDREC(self):
        campos = [
            u'IDREC',
            str(self.codigo_receita_idrec)[:4],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg

class DIRF_BPFDEC(object):
    def __init__(self, *args, **kwargs):
        self.cpf = ''
        self.nome= ''
        self.data_laudo = ''

    def registro(self):
        campos = [
            u'BPFDEC',
            limpa_formatacao(self.cpf)[:11],
            limpa_dirf(self.nome)[:60],
            self.data_laudo[:8],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg
    
class DIRF_PSE(object):
 
    def registro_PSE(self):
        campos = [
            u'PSE',
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg
    
class DIRF_OPSE(object):
    
    def __init__(self, *args, **kwargs):
        self.cnpj_plano = ''
        self.nome_empresa = ''
        self.registro_ans = ''
 
    def registro_OPSE(self):
        campos = [
            u'OPSE',
            limpa_formatacao(self.cnpj_plano)[:14],
            limpa_dirf(self.nome_empresa)[:150],
            self.registro_ans[:6],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg
    
class DIRF_TPSE(object):
    
    def __init__(self, *args, **kwargs):
        self.cpf = ''
        self.nome= ''
        self.valor_pago = 0
    
    def registro_TPSE(self):
        campos = [
            u'TPSE',
            limpa_formatacao(self.cpf)[:11],
            limpa_dirf(self.nome)[:60],
            str(int(self.valor_pago * 100)).zfill(13)[:13],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg
    
class DIRF_DTPSE(object):
    
    def __init__(self, *args, **kwargs):
        self.cpf = ''
        self.data_nascumento = ''
        self.nome = ''
        self.relacao_depencia = ''
        self.valor_pago = 0
    
    def registro_DTPSE(self):
        campos = [
            u'DTPSE',
            limpa_formatacao(self.cpf)[:11],
            self.data_nascumento[:8],
            limpa_dirf(self.nome)[:60],
            self.relacao_depencia[:2],
            str(int(self.valor_pago * 100)).zfill(13)[:13],
            '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg


class DIRF_REGISTROS(object):
    def __init__(self, *args, **kwargs):

        self.codigo_registro = ''
        self.mes_01 = 0
        self.mes_02 = 0
        self.mes_03 = 0
        self.mes_04 = 0
        self.mes_05 = 0
        self.mes_06 = 0
        self.mes_07 = 0
        self.mes_08 = 0
        self.mes_09 = 0
        self.mes_10 = 0
        self.mes_11 = 0
        self.mes_12 = 0
        self.mes_13 = 0

    def registro(self):
        campos = [
            self.codigo_registro[:5],
            ]

        if self.codigo_registro in ('RIDAC','RIIRP','RIAP'):
            campos += [
                str(int(self.mes_01 * 100)).zfill(13)[:13],
                str(int(self.mes_02 * 100)).zfill(13)[:13],
                str(int(self.mes_03 * 100)).zfill(13)[:13],
                str(int(self.mes_04 * 100)).zfill(13)[:13],
                str(int(self.mes_05 * 100)).zfill(13)[:13],
                str(int(self.mes_06 * 100)).zfill(13)[:13],
                str(int(self.mes_07 * 100)).zfill(13)[:13],
                str(int(self.mes_08 * 100)).zfill(13)[:13],
                str(int(self.mes_09 * 100)).zfill(13)[:13],
                str(int(self.mes_10 * 100)).zfill(13)[:13],
                str(int(self.mes_11 * 100)).zfill(13)[:13],
                str(int(self.mes_12 * 100)).zfill(13)[:13],
                '',
                '\r\n',
            ]

        else:
            campos += [
                str(int(self.mes_01 * 100)).zfill(13)[:13],
                str(int(self.mes_02 * 100)).zfill(13)[:13],
                str(int(self.mes_03 * 100)).zfill(13)[:13],
                str(int(self.mes_04 * 100)).zfill(13)[:13],
                str(int(self.mes_05 * 100)).zfill(13)[:13],
                str(int(self.mes_06 * 100)).zfill(13)[:13],
                str(int(self.mes_07 * 100)).zfill(13)[:13],
                str(int(self.mes_08 * 100)).zfill(13)[:13],
                str(int(self.mes_09 * 100)).zfill(13)[:13],
                str(int(self.mes_10 * 100)).zfill(13)[:13],
                str(int(self.mes_11 * 100)).zfill(13)[:13],
                str(int(self.mes_12 * 100)).zfill(13)[:13],
                str(int(self.mes_13 * 100)).zfill(13)[:13],
                '\r\n',
            ]
        reg = '|'.join(campos)
        reg = tira_acentos(unicode(reg)).upper()
        return reg



