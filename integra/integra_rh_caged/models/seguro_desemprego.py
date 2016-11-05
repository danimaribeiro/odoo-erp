# -*- coding: utf-8 -*-

from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje



TIPO_DECLARACAO = [
    ('1', u'1ª declaração'),
    ('2', u'Redeclaração'),
]

TIPO_ALTERACAO = [
    ('1', u'Nada'),
    ('2', u'Dados cadastrais'),
    ('3', u'Fechamento do estabelecimento'),
]


def limpa_caged(texto):
    probibidos = u'.,-_;:?!=+*/&#$%{}[]()<>|@"\´`~^¨' + u"'"

    for c in probibidos:
        texto = texto.replace(c, ' ')

    while '  ' in texto:
        texto = texto.replace('  ', ' ')

    return texto


class REGISTRO_HEADER(object):
    def __init__(self, *args, **kwargs):
        self.tipo_registro = '00'
        self.tipo_identificador = '1'
        self.cnpj_empresa = ''
        self.versao_layout = '001'
        self.empregados = []

    def registro(self):
        reg = self.tipo_registro
        reg += self.tipo_identificador
        reg += limpa_formatacao(self.cnpj_empresa).zfill(14)[:14]
        reg += self.versao_layout
        reg += ''.ljust(280)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class REGISTRO_REQUERIMENTO(object):
    def __init__(self, *args, **kwargs):
        self.tipo_registro = 01
        self.cpf = ''
        self.nome = ''
        self.endereco = ''
        self.complemento = ''
        self.cep = ''
        self.uf = ''
        self.telefone = ''
        self.nome_mae = ''
        self.pis = ''
        self.carteira_trabalho_numero = ''
        self.carteira_trabalho_serie = ''
        self.carteira_trabalho_estado = ''
        self.cbo = ''
        self.data_admissao = hoje()
        self.data_demissao = hoje()
        self.sexo = 'M'
        self.grau_instrucao = '01'
        self.data_nascimento = hoje()
        self.horas_trabalhadas_semana = 44
        self.remuneracao_antepenultimo_salario = 0
        self.remuneracao_penultimo_salario = 0
        self.ultimo_salario = 0
        self.numero_meses_trabalhados = '00'
        self.recebeu_6_salario = '0'
        self.aviso_previo_indenizado = '1'
        self.codigo_banco = ''
        self.codigo_agencia = ''
        self.codigo_agencia_digito = ''

    def registro(self):
        reg = str(self.tipo_registro).zfill(2)[:2]
        reg += limpa_formatacao(self.cpf).zfill(11)[:11]
        reg += limpa_caged(self.nome).ljust(40)[:40]
        reg += limpa_caged(self.endereco).ljust(40)[:40]
        reg += limpa_caged(self.complemento).ljust(16)[:16]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += self.uf.ljust(2)[:2]
        reg += limpa_fone(self.telefone).zfill(10)[:10]
        reg += limpa_caged(self.nome_mae).ljust(40)[:40]
        reg += limpa_formatacao(self.pis).zfill(11)[:11]
        reg += limpa_caged(self.carteira_trabalho_numero).strip().zfill(8)[:8]
        reg += limpa_caged(self.carteira_trabalho_serie).strip().zfill(5)[:5]
        reg += self.carteira_trabalho_estado[:2]
        reg += self.cbo.strip().zfill(6)[:6]
        reg += self.data_admissao.strftime('%d%m%Y')
        reg += self.data_demissao.strftime('%d%m%Y')
        reg += '1' if self.sexo == 'M' else '2'
        reg += self.grau_instrucao.zfill(2)
        reg += self.data_nascimento.strftime('%d%m%Y')
        reg += str(int(self.horas_trabalhadas_semana)).zfill(2)[:2]
        reg += str(int(self.remuneracao_antepenultimo_salario * 100)).zfill(10)[:10]
        reg += str(int(self.remuneracao_penultimo_salario * 100)).zfill(10)[:10]
        reg += str(int(self.ultimo_salario * 100)).zfill(10)[:10]
        reg += str(self.numero_meses_trabalhados).zfill(2)[:2]
        reg += str(self.recebeu_6_salario).zfill(1)[:1]
        reg += self.aviso_previo_indenizado[:1]
        reg += self.codigo_banco.zfill(3)[:3]
        reg += self.codigo_agencia.zfill(4)[:4]
        reg += self.codigo_agencia_digito.zfill(1)[:1]
        reg += ''.ljust(28)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class REGISTRO_TRAILLER(object):
    def __init__(self, *args, **kwargs):

        self.tipo_registro = '99'

    def registro(self, sequencia):
        reg = self.tipo_registro
        reg += str(sequencia).zfill(5)[:5]
        reg += ''.ljust(293)
        reg += '\r\n'
        return reg
