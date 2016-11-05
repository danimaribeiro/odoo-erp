# -*- coding: utf-8 -*-

from collections import OrderedDict
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
from pybrasil.valor.decimal import Decimal as D
from caged import limpa_caged


INDICADOR_RECOLHIMENTO_FGTS = (
    ('0', u'0 - Não informado'),
    ('1', u'1 - GRF no prazo'),
    ('2', u'2 - GRF em atraso'),
    ('3', u'3 - GRF em atraso - ação fiscal'),
)

INDICADOR_RECOLHIMENTO_GPS = (
    ('1', u'1 - GPS no prazo'),
    ('2', u'2 - GPS em atraso'),
    ('3', u'3 - Não gera GPS'),
)

MODALIDADE_ARQUIVO_SEFIP = (
    ('0', u'0 - Recolhimento ao FGTS e Declaração à Previdência'),
    ('1', u'1 - Declaração ao FGTS e à Previdência'),
    ('9', u'9 - Confirmação de informações anteriores'),
)

CENTRALIZA_FGTS = (
    ('0', u'0 - Não centraliza'),
    ('1', u'1 - Centralizadora'),
    ('2', u'2 - Centralizada'),
)


class SEFIP(object):
    def __init__(self, *args, **kwargs):
        self.tipo_remessa = '1'
        self.tipo_inscricao = '1'
        self.cnpj_responsavel = ''
        self.razao_social_responsavel = ''
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
        self.ano = mes_passado()[0]
        self.mes = mes_passado()[1]
        self.codigo_recolhimento = '115'
        self.indicador_recolhimento_fgts = '1'
        self.modalidade_arquivo = '1'
        self.data_recolhimento_fgts = None
        self.indicador_recolhimento_gps = '1'
        self.data_recolhimento_gps = None
        self.tipo_inscricao_fornecedor_sistema = '1'
        self.cnpj_fornecedor_sistema = '14817848000112'
        self.alteracao_endereco = False
        self.cnae = ''
        self.alteracao_cnae = False
        self.aliquota_rat = 0
        self.centralizadora = '0'
        self.simples = '1'
        self.codigo_fpas = ''
        self.codigo_outras_entidades = ''
        self.codigo_recolhimento_gps = ''
        self.isencao_filantropia = 0
        self.salario_familia = 0.00
        self.salario_maternidade = 0.00
        self.cooperativas = 0.00
        self.tomadores = OrderedDict()
        self.empregados = OrderedDict()

        self.processo_numero = ''
        self.processo_ano = ''
        self.processo_vara= ''
        self.processo_inicial = ''
        self.processo_final = ''

    def registro(self):
        reg = u'00'
        reg += ''.ljust(51)
        reg += self.tipo_remessa
        reg += self.tipo_inscricao
        reg += limpa_formatacao(self.cnpj_responsavel).zfill(14)[:14]
        reg += limpa_caged(self.razao_social_responsavel).ljust(30)[:30]
        reg += limpa_caged(self.contato).ljust(20)[:20]
        reg += limpa_caged(self.endereco).ljust(50)[:50]
        reg += limpa_caged(self.bairro).ljust(20)[:20]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += limpa_caged(self.cidade).ljust(20)[:20]
        reg += self.estado
        reg += limpa_fone(self.telefone).zfill(12)[:12]
        reg += self.email.strip().ljust(60)[:60]
        reg += str(self.ano).zfill(4)
        reg += str(self.mes).zfill(2)
        reg += self.codigo_recolhimento
        reg += ' ' if self.indicador_recolhimento_fgts == '0' else self.indicador_recolhimento_fgts
        reg += ' ' if self.modalidade_arquivo == '0' else self.modalidade_arquivo

        if self.data_recolhimento_fgts and self.indicador_recolhimento_fgts in ['2', '3', '5', '6']:
            reg += self.data_recolhimento_fgts.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += self.indicador_recolhimento_gps

        if self.data_recolhimento_gps and self.indicador_recolhimento_gps == '2':
            reg += self.data_recolhimento_gps.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        #
        # Índice de recolhimento em atraso
        #
        reg += ''.ljust(7)
        reg += self.tipo_inscricao_fornecedor_sistema
        reg += self.cnpj_fornecedor_sistema
        reg += ''.ljust(18)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

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
        reg += 'S' if self.alteracao_endereco else 'N'
        reg += limpa_formatacao(self.cnae).zfill(7)[:7]
        reg += 'S' if self.alteracao_cnae else 'N'
        reg += str(int(self.aliquota_rat * 10)).zfill(2)[:2]
        reg += self.centralizadora
        reg += self.simples
        reg += self.codigo_fpas
        reg += self.codigo_outras_entidades.ljust(4)
        reg += self.codigo_recolhimento_gps
        reg += ''.ljust(5) if self.isencao_filantropia == 0 else str(int(self.isencao_filantropia * 100)).zfill(5)[:5]

        if self.mes == 13:
            reg += ''.zfill(15)
            reg += ''.zfill(15)
        else:
            reg += str(int(self.salario_familia * 100)).zfill(15)[:15]
            reg += str(int(self.salario_maternidade * 100)).zfill(15)[:15]

        reg += ''.zfill(15) # contribuição descontada do empregado
        reg += ''.zfill(1) # valor negativo ou positivo
        reg += ''.zfill(14) # valor devido à Previdência
        reg += ''.ljust(3) # banco
        reg += ''.ljust(4) # agência
        reg += ''.ljust(9) # conta corrente
        reg += ''.zfill(45)
        reg += ''.ljust(4)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

    def registro_12(self):
        reg = u'12'
        reg += self.tipo_inscricao
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += ''.zfill(36)

        if self.mes == 13:
            reg += str(int(self.salario_maternidade * 100)).zfill(15)[:15]
        else:
            reg += ''.zfill(15) # dedução 13º licença maternidade

        reg += ''.zfill(15) # receita evento esportivo
        reg += ' ' # origem da receita do evento esportivo
        reg += ''.zfill(15) # comercialização da produção - pessoa física
        reg += ''.zfill(15) # comercialização da produção - pessoa jurídica

        if self.codigo_recolhimento in ['650', '660']:
            reg += self.processo_numero.zfill(11)[:11] # outras informações processo
            reg += self.processo_ano.zfill(4)[:4] # outras informações processo - ano

            if self.processo_vara != '0':
                reg += self.processo_vara.zfill(5)[:5] # outras informações processo - vara
            else:
                reg += ''.ljust(5) # outras informações processo - vara

            reg += self.processo_inicial.zfill(6)[:6] # outras informações processo - data início AAAAMM
            reg += self.processo_final.zfill(6)[:6] # outras informações processo - data início AAAAMM
        else:
            reg += ''.ljust(11) # outras informações processo
            reg += ''.ljust(4) # outras informações processo - ano
            reg += ''.ljust(5) # outras informações processo - vara
            reg += ''.ljust(6) # outras informações processo - data início AAAAMM
            reg += ''.ljust(6) # outras informações processo - data início AAAAMM

        reg += ''.zfill(15) # compensação
        reg += ''.ljust(6) # compensação - data início AAAAMM
        reg += ''.ljust(6) # compensação - data fim AAAAMM
        reg += ''.zfill(15) # competências anteriores
        reg += ''.zfill(15) # competências anteriores
        reg += ''.zfill(15) # competências anteriores
        reg += ''.zfill(15) # competências anteriores
        reg += ''.zfill(15) # competências anteriores
        reg += ''.zfill(15) # parcelamento FGTS
        reg += ''.zfill(15) # parcelamento FGTS
        reg += ''.zfill(15) # parcelamento FGTS
        reg += str(int(self.cooperativas * 100)).zfill(15)
        reg += ''.zfill(45) # implementação futura
        reg += ''.ljust(6)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

    def registro_90(self):
        reg = u'90'
        reg += ''.zfill(51).replace('0', '9')
        reg += ''.ljust(306)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

    def reordena_tomadores(self):
        cnpjs = []

        for cnpj in self.tomadores:
            cnpjs.append(cnpj)

        cnpjs.sort()

        novos_tomadores = OrderedDict()
        for cnpj in cnpjs:
            self.tomadores[cnpj].reordena_empregados()
            novos_tomadores[cnpj] = self.tomadores[cnpj]

        self.tomadores = novos_tomadores


class Tomador(object):
    def __init__(self, *args, **kwargs):
        self.sefip = SEFIP()
        self.tipo_inscricao = '1'
        self.cnpj = ''
        self.razao_social = ''
        self.endereceo = ''
        self.bairro = ''
        self.cep = ''
        self.cidade = ''
        self.estado = ''
        self.codigo_recolhimento_gps = ''
        self.salario_familia = 0
        self.valor_retido = 0
        self.valor_faturado = 0
        self.empregados = OrderedDict()

    def registro(self):
        reg = u'20'
        reg += self.sefip.tipo_inscricao
        reg += limpa_formatacao(self.sefip.cnpj).zfill(14)[:14]
        reg += self.tipo_inscricao
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14]
        reg += ''.zfill(21)
        reg += limpa_caged(self.razao_social).ljust(40)[:40]
        reg += limpa_caged(self.endereco).ljust(50)[:50]
        reg += limpa_caged(self.bairro).ljust(20)[:20]
        reg += limpa_formatacao(self.cep).zfill(8)[:8]
        reg += limpa_caged(self.cidade).ljust(20)[:20]
        reg += self.estado
        reg += self.codigo_recolhimento_gps.ljust(4)
        reg += str(int(self.salario_familia * 100)).zfill(15)[:15]
        reg += ''.zfill(15)
        reg += '0'
        reg += ''.zfill(14)
        reg += str(int(self.valor_retido * 100)).zfill(15)[:15]
        reg += str(int(self.valor_faturado * 100)).zfill(15)[:15]
        reg += ''.zfill(45)
        reg += ''.ljust(42)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg

    def reordena_empregados(self):
        niss = []

        for nis in self.empregados:
            niss.append(nis)

        niss.sort()

        novos_empregados = OrderedDict()
        for nis in niss:
            novos_empregados[nis] = self.empregados[nis]

        self.empregados = novos_empregados


class Empregado(object):
    def __init__(self, *args, **kwargs):
        self.sefip = SEFIP()
        self.tomador = Tomador()
        self.nis = ''
        self.data_admissao = hoje()
        self.categoria_trabalhador = ''
        self.nome = ''
        self.matricula = ''
        self.carteira_trabalho_numero = ''
        self.carteira_trabalho_serie = ''
        self.data_opcao_fgts = hoje()
        self.data_nascimento = hoje()
        self.cbo = ''
        self.salario_liquido = 0
        self.decimo_terceiro_liquido = 0
        self.classe_contribuicao = ''
        self.ocorrencia = ''
        self.valor_inss = 0
        self.valor_inss_decimo_terceiro = 0
        self.base_inss = 0
        self.base_decimo_terceiro_rescisao = 0
        self.base_decimo_terceiro = 0
        self.salario_familia = 0
        self.salario_maternidade = 0
        self.movimentacoes = OrderedDict()

    def registro(self):
        reg = u'30'
        reg += self.sefip.tipo_inscricao
        reg += limpa_formatacao(self.sefip.cnpj).zfill(14)[:14]

        if self.sefip.codigo_recolhimento == '150':
            reg += self.tomador.tipo_inscricao
            reg += limpa_formatacao(self.tomador.cnpj).zfill(14)[:14]
        else:
            reg += ' '
            reg += ''.ljust(14)

        if '_' in self.nis:
            nis = self.nis.split('_')[0]
        else:
            nis = self.nis
        reg += limpa_caged(nis).strip().zfill(11)[:11]

        if self.categoria_trabalhador not in ['13']:
            reg += self.data_admissao.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += self.categoria_trabalhador
        reg += limpa_caged(self.nome).ljust(70)[:70]

        if self.categoria_trabalhador in ['06', '13', '14', '15', '16', '17', '18', '22', '23', '24', '25']:
            reg += ''.ljust(11)
        else:
            reg += self.matricula.strip().zfill(11)

        if self.categoria_trabalhador in ['01', '03', '04', '06', '07', '26']:
            reg += limpa_caged(self.carteira_trabalho_numero).replace(' ', '').zfill(7)[:7]
            reg += limpa_caged(self.carteira_trabalho_serie).replace(' ', '').zfill(5)[:5]
            reg += self.data_opcao_fgts.strftime('%d%m%Y')
        else:
            reg += ''.ljust(7)
            reg += ''.ljust(5)
            reg += ''.ljust(8)

        if self.categoria_trabalhador in ['01', '03', '04', '06', '07', '12', '19', '20', '21', '26']:
            reg += self.data_nascimento.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += self.cbo[:4].zfill(5)[:5]

        if self.salario_liquido < D('0.01') and self.sefip.mes != 13:
            self.salario_liquido = D('0.01')

        reg += str(int(self.salario_liquido * 100)).zfill(15)[:15]
        reg += str(int(self.decimo_terceiro_liquido * 100)).zfill(15)[:15]
        reg += self.classe_contribuicao.ljust(2)
        reg += self.ocorrencia.ljust(2)

        if self.ocorrencia == '05' and self.valor_inss:
            reg += str(int(self.valor_inss * 100)).zfill(15)[:15]
        elif self.sefip.codigo_recolhimento in ('650', '660'):
            reg += str(int((self.valor_inss + self.valor_inss_decimo_terceiro) * 100)).zfill(15)[:15]
        else:
            reg += ''.zfill(15)

        ocorrencias_base_inss = ['O1', 'O2', 'R', 'Z2', 'Z3', 'Z4']
        poe_base_inss = False

        for ocorrencia in ocorrencias_base_inss:
            if ocorrencia in self.movimentacoes:
                poe_base_inss = True

        if poe_base_inss and self.sefip.mes != 13:
            if self.base_inss < D('0.01'):
                self.base_inss = D('0.01')

            reg += str(int(self.base_inss * 100)).zfill(15)[:15]
        else:
            reg += ''.zfill(15)

        reg += str(int(self.base_decimo_terceiro_rescisao * 100)).zfill(15)[:15]

        if self.sefip.mes == 13:
            reg += str(int(self.base_decimo_terceiro * 100)).zfill(15)[:15]
        else:
            reg += ''.zfill(15)

        reg += ''.ljust(98)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg


class Movimentacao(object):
    def __init__(self, *args, **kwargs):
        self.sefip = SEFIP()
        self.empregado = Empregado()
        self.codigo = ''
        self.data = hoje()
        self.indicativo_fgts = ''

    def registro(self):
        reg = u'32'
        reg += self.sefip.tipo_inscricao
        reg += limpa_formatacao(self.sefip.cnpj).zfill(14)[:14]

        if self.sefip.codigo_recolhimento == '150':
            reg += self.empregado.tomador.tipo_inscricao
            reg += limpa_formatacao(self.empregado.tomador.cnpj).zfill(14)[:14]
        else:
            reg += ' '
            reg += ''.ljust(14)

        if '_' in self.empregado.nis:
            nis = self.empregado.nis.split('_')[0]
        else:
            nis = self.empregado.nis
        reg += limpa_caged(nis).strip().zfill(11)[:11]

        if self.empregado.categoria_trabalhador not in ['13']:
            reg += self.empregado.data_admissao.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8)

        reg += self.empregado.categoria_trabalhador
        reg += limpa_caged(self.empregado.nome).ljust(70)[:70]
        reg += self.codigo.ljust(2)[:2]
        reg += self.data.strftime('%d%m%Y')

        if self.codigo in ['I1', 'I2', 'I3', 'I4', 'L']:
            reg += 'S'
        else:
            reg += self.indicativo_fgts.ljust(1)[:1]

        reg += ''.ljust(225)
        reg += '*'
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg
