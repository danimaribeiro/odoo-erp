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


class CAGEDEstabelecimento(object):
    def __init__(self, *args, **kwargs):
        self.tipo_identificador = '1'
        self.cnpj = ''
        self.primeira_declaracao = False
        self.tipo_alteracao = '1'
        self.cep = ''
        self.razao_social = ''
        self.endereco = ''
        self.bairro = ''
        self.estado = ''
        self.total_empregados_primeiro_dia = 0
        self.porte = '3'
        self.cnae = ''
        self.telefone = ''
        self.email = ''
        self.empregados = []

    def registro(self, sequencia):
        reg = 'B'
        reg += self.tipo_identificador
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += str(sequencia).zfill(5)[:5]
        reg += '1' if self.primeira_declaracao else '2'
        reg += self.tipo_alteracao
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += ''.ljust(5)
        reg += limpa_caged(self.razao_social).ljust(39)[:39]
        reg += limpa_caged(self.endereco).ljust(41)[:41]
        reg += limpa_caged(self.bairro).ljust(20)[:20]
        reg += self.estado
        reg += str(self.total_empregados_primeiro_dia).zfill(5)[:5]
        reg += self.porte
        reg += limpa_formatacao(self.cnae).zfill(7)[:7]
        reg += limpa_fone(self.telefone).zfill(12)[:12]
        reg += self.email.strip().ljust(50)[:50]
        reg += ''.ljust(27)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class CAGEDEmpregado(object):
    def __init__(self, *args, **kwargs):
        self.estabelecimento = CAGEDEstabelecimento()
        self.pis = ''
        self.sexo = 'M'
        self.data_nascimento = hoje()
        self.grau_instrucao = '1'
        self.salario_mensal = 0
        self.horas_trabalhadas_semana = 44
        self.data_admissao = hoje()
        self.tipo_movimento = '20'
        self.tipo_movimento_admissao = '20'
        self.dia_desligamento = 0
        self.nome = ''
        self.carteira_trabalho_numero = ''
        self.carteira_trabalho_serie = ''
        self.carteira_trabalho_estado = ''
        self.raca_cor = '9'
        self.deficiencia = False
        self.cbo = ''
        self.aprendiz = False
        self.tipo_deficiencia = ' '
        self.cpf = ''
        self.cep = ''
        self.rescisao_mesmo_mes_admissao = False

    def registro(self, sequencia):
        if self.rescisao_mesmo_mes_admissao:
            reg = self._registro(sequencia)
            reg += self._registro(sequencia, demissao=True)
            return reg

        else:
            return self._registro(sequencia)

    def _registro(self, sequencia, demissao=False):
        if self.estabelecimento.tipo_alteracao != '1':
            reg = 'X'
        else:
            reg = 'C'

        reg += self.estabelecimento.tipo_identificador
        reg += limpa_formatacao(self.estabelecimento.cnpj).zfill(14)[:14]
        reg += str(sequencia).zfill(5)[:5]
        reg += limpa_formatacao(self.pis).zfill(11)[:11]
        reg += '1' if self.sexo == 'M' else '2'
        reg += self.data_nascimento.strftime('%d%m%Y')
        reg += self.grau_instrucao
        reg += ''.ljust(4)
        reg += str(int(self.salario_mensal * 100)).zfill(8)[:8]
        reg += str(int(self.horas_trabalhadas_semana)).zfill(2)[:2]
        reg += self.data_admissao.strftime('%d%m%Y')

        if self.rescisao_mesmo_mes_admissao:
            if demissao:
                reg += self.tipo_movimento
                reg += '  ' if self.dia_desligamento == 0 else str(int(self.dia_desligamento)).zfill(2)[:2]
            else:
                reg += self.tipo_movimento_admissao
                reg += '  '

        else:
            reg += self.tipo_movimento
            reg += '  ' if self.dia_desligamento == 0 else str(int(self.dia_desligamento)).zfill(2)[:2]

        reg += limpa_caged(self.nome).ljust(40)[:40]
        reg += limpa_caged(self.carteira_trabalho_numero).strip().zfill(8)[:8]
        reg += limpa_caged(self.carteira_trabalho_serie).strip().zfill(4)[:4]
        reg += ''.ljust(7)
        reg += self.raca_cor
        reg += '1' if self.deficiencia else '2'
        reg += self.cbo.strip().zfill(6)[:6]
        reg += '1' if self.aprendiz else '2'
        reg += self.carteira_trabalho_estado
        reg += self.tipo_deficiencia
        reg += limpa_formatacao(self.cpf).zfill(11)[:11]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += ''.ljust(81)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class CAGED(object):
    def __init__(self, *args, **kwargs):
        self.ano = mes_passado()[0]
        self.mes = mes_passado()[1]
        self.tipo_alteracao = '1'
        self.tipo_identificador = '1'
        self.cnpj = ''
        self.razao_social = ''
        self.endereco = ''
        self.cep = ''
        self.estado = ''
        self.telefone = ''
        self.ramal = ''
        self.estabelecimentos = []

    def registro(self):
        reg = 'A'
        reg += 'L2009'
        reg += ''.ljust(3)
        reg += str(self.mes).zfill(2)
        reg += str(self.ano).zfill(4)
        reg += self.tipo_alteracao
        reg += '1'.zfill(5)
        reg += self.tipo_identificador
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += limpa_caged(self.razao_social).ljust(35)[:35]
        reg += limpa_caged(self.endereco).ljust(40)[:40]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += self.estado
        fone = limpa_fone(self.telefone).zfill(10)[:10]
        reg += fone[:2] + '  ' + fone[2:]
        reg += self.ramal.zfill(4)[:4]
        #
        # Total de estabelecimentos informados
        #
        reg += str(len(self.estabelecimentos)).zfill(5)[:5]
        total_geral = 0
        for estabelecimento in self.estabelecimentos:
            total_geral += len(estabelecimento.empregados)
        reg += str(total_geral).zfill(6)[:6]
        reg += ''.ljust(92)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg
