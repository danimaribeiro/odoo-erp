# -*- coding: utf-8 -*-

from collections import OrderedDict
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
from caged import limpa_caged
from integra_rh import constantes_rh
#from openerp.pychart.svgcanvas import self


class Empresa(object):
    def __init__(self, *args, **kwargs):
        self.tipo_inscricao = '1'
        self.cnpj = ''
        self.razao_social = ''
        self.endereceo = ''
        self.bairro = ''
        self.cep = ''
        self.cidade = ''
        self.estado = ''
        self.telefone = ''
        self.cnae = ''
        self.simples = '1'
        self.codigo_fpas = ''

    def registro_10(self):
        reg = u'10'
        reg += self.tipo_inscricao
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += ''.zfill(36)
        reg += limpa_caged(self.razao_social).ljust(40)[:40]
        reg += limpa_caged(self.endereco).ljust(50)[:50]
        reg += limpa_caged(self.bairro).ljust(20)[:20]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += limpa_caged(self.cidade).ljust(20)[:20]
        reg += self.estado
        reg += limpa_fone(self.telefone).zfill(12)[:12]
        reg += limpa_formatacao(self.cnae).zfill(7)[:7]
        reg += self.simples
        reg += self.codigo_fpas
        reg += ''.ljust(143)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class GRRF(object):
    def __init__(self, *args, **kwargs):
        self.tipo_remessa = '2'
        self.tipo_inscricao = '1'
        self.cnpj = ''
        self.razao_social = ''
        self.contato = ''
        self.endereceo = ''
        self.bairro = ''
        self.cep = ''
        self.cidade = ''
        self.estado = ''
        self.telefone = ''
        self.email = ''
        self.data_recolhimento_grrf = hoje()
        self.tipo_inscricao_fornecedor_sistema = '1'
        self.cnpj_fornecedor_sistema = '14817848000112'
        self.alteracao_endereco = False
        self.alteracao_cnae = False
        self.codigo_outras_entidades = ''
        self.codigo_recolhimento_gps = ''
        self.empresa = Empresa()
        self.empregados = OrderedDict()

    def registro(self):
        reg = u'00'
        reg += ''.ljust(51)
        reg += self.tipo_remessa
        reg += self.tipo_inscricao
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += limpa_caged(self.razao_social).ljust(30)[:30]
        reg += limpa_caged(self.contato).ljust(20)[:20]
        reg += limpa_caged(self.endereco).ljust(50)[:50]
        reg += limpa_caged(self.bairro).ljust(20)[:20]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += limpa_caged(self.cidade).ljust(20)[:20]
        reg += self.estado
        reg += limpa_fone(self.telefone).zfill(12)[:12]
        reg += self.email.strip().ljust(60)[:60]
        reg += self.data_recolhimento_grrf.strftime('%d%m%Y')
        reg += ''.ljust(60)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

    def registro_10(self):
        return self.empresa.registro_10()

    def registro_90(self):
        reg = u'90'
        reg += ''.zfill(51).replace('0', '9')
        reg += ''.ljust(306)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class Empregado(object):
    def __init__(self, *args, **kwargs):
        self.grrf = GRRF()
        self.tipo_iscr_tomador_cv = '' # Tipo de incricão tomador empresa de Constr.Civil
        self.iscricao_tomador_cv = '' # Incrição de tomador empresa de Constr.Civil
        self.nis = '' #numero do pis/pasp
        self.data_admissao = hoje() #Data de Admissão
        self.categoria_trabalhador = '01' #Categoria Trabalhor
        self.nome = '' #Nome
        self.carteira_trabalho_numero = '' #Numero da carteira CTPS
        self.carteira_trabalho_serie = '' #Serie da carteira CTPS
        self.sexo = 'M' #Sexo
        self.grau_instrucao = '01' #Grau de Instrução
        self.data_nascimento = hoje() #Data Nascimento
        self.horas_trabalhadas_semana = 44 # Horas Trabalhadas Semana
        self.cbo = '' # CBO
        self.data_opcao_fgts = hoje() #Data de opção do FGTS
        self.codigo_movimentacao = '' # codigo de afastamento
        self.data_movimentacao = hoje() # data de afastamento
        self.codigo_saque = '01' #Codigo Saque
        self.aviso_previo = '3' #Aviso Previo
        self.data_inicio_aviso = None #Data do Inicio do Aviso Prévio
        self.reposicao = False #Reposição Vaga
        self.data_homologacao_dissidio = None #Data Homologação Dissídio Coletivo
        self.valor_dissidio = 0 # Valor Dissidio
        self.remuneracao_mes_anterior = 0 #Remuneração Mês Anterior da Rescisão
        self.remuneracao_mes_rescisao = 0 #Remuneração Mês da Rescisão
        self.valor_aviso_previo = 0 #Aviso Previo Iindenizado
        self.indic_pensao_alimenticia = 'N' # Indicativo Pensão Alimentícia
        self.percentual_pensao = 0 # Percentual de Pensão Alimentícia
        self.valor_pensao_alim = 0 # Valor de Pensão Alimentícia
        self.cpf = '' #CPF
        self.banco_trabalhador = '000' # Banco da conta do trabalhador
        self.agencia_trabalhador = '' # Agência da conta do trabalhador
        self.conta_corrente = '' # Conta Corrente
        self.saldo_rescisao = 0 # Saldo para fins Rescisórios


    def registro_40(self):
        reg = u'40'
        reg += self.grrf.tipo_inscricao
        reg += limpa_formatacao(self.grrf.cnpj).zfill(14)[:14]

        #if self.sefip.codigo_recolhimento == '150':
        #    reg += self.tomador.tipo_inscricao
        #    reg += limpa_formatacao(self.tomador.cnpj).zfill(14)[:14]
        #else:
        reg += '0'
        reg += ''.zfill(14)

        reg += limpa_caged(self.nis).strip().zfill(11)[:11]

        if self.categoria_trabalhador not in ['13']:
            reg += self.data_admissao.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += self.categoria_trabalhador
        reg += limpa_caged(self.nome).ljust(70)[:70]

        if self.categoria_trabalhador in ['01', '03', '04', '06', '07', '26']:
            reg += limpa_caged(self.carteira_trabalho_numero).replace(' ', '').zfill(7)[:7]
            reg += limpa_caged(self.carteira_trabalho_serie).replace(' ', '').zfill(5)[:5]
        else:
            reg += ''.zfill(7)
            reg += ''.zfill(5)

        if self.sexo == 'M':
            reg += '1'
        else:
            reg += '2'

        reg += self.grau_instrucao

        if self.categoria_trabalhador in ['01', '03', '04', '06', '07', '12', '19', '20', '21', '26']:
            reg += self.data_nascimento.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += str(int(self.horas_trabalhadas_semana)).zfill(2)[:2]
        reg += self.cbo[:4].zfill(6)[:6]
        reg += self.data_opcao_fgts.strftime('%d%m%Y')
        reg += self.codigo_movimentacao.ljust(2)
        reg += self.data_movimentacao.strftime('%d%m%Y')
        reg += self.codigo_saque.ljust(3)[:3]
        reg += self.aviso_previo

        if self.data_inicio_aviso:
            reg += self.data_inicio_aviso.strftime('%d%m%Y')
        else:
            reg += ''.zfill(8)

        reg += 'S' if self.reposicao else 'N'

        if self.data_homologacao_dissidio:
            reg += self.data_homologacao_dissidio.strftime('%d%m%Y')
            reg += str(int(self.valor_dissidio * 100)).zfill(15)[:15]
        else:
            reg += ''.ljust(8)
            reg += ''.zfill(15)

        reg += str(int(self.remuneracao_mes_anterior * 100)).zfill(15)[:15]
        reg += str(int(self.remuneracao_mes_rescisao * 100)).zfill(15)[:15]
        reg += str(int(self.valor_aviso_previo * 100)).zfill(15)[:15]
        reg += self.indic_pensao_alimenticia
        reg += str(int(self.percentual_pensao * 100)).zfill(5)[:5]
        reg += str(int(self.valor_pensao_alim * 100)).zfill(15)[:15]
        reg += limpa_formatacao(self.cpf)
        reg += self.banco_trabalhador.zfill(3)[:3]
        reg += limpa_caged(self.agencia_trabalhador).replace(' ', '').zfill(4)[:4]
        reg += limpa_caged(self.conta_corrente).replace(' ', '').zfill(13)[:13]
        reg += str(int(self.saldo_rescisao * 100)).zfill(15)[:15]
        reg += ''.ljust(39)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()

        return reg
