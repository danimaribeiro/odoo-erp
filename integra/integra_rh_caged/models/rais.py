# -*- coding: utf-8 -*-

from collections import OrderedDict
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.inscricao import limpa_formatacao
from pybrasil.telefone.telefone import limpa_fone
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
from caged import limpa_caged
from integra_rh import constantes_rh


#
########################### ARQUIVO RAIS LAYOUT 2013 ############################
#

class RAIS(object):
    def __init__(self, *args, **kwargs):
        self.sequencial = 0
        self.prefixo = '00'
        self.cnpj = ''
        self.constante = 1
        self.cpf_cnpj_responsavel = ''
        self.tipo_inscricao = ''
        self.razao_social_responsavel = ''
        self.razao_social = ''
        self.endereco = ''
        self.numero = ''
        self.complemento = ''
        self.bairro = ''
        self.cep = ''
        self.codigo_municipio = ''
        self.nome_municipio = ''
        self.estado = ''
        self.telefone = ''
        self.indetificado_retificacao = 2
        self.data_retificacao = hoje()
        self.data_geracao = hoje()
        self.email = ''
        self.nome_responsavel = ''
        self.cpf_responsavel = ''
        self.crea_retificado = ''
        self.data_nasc_resp = hoje()

        self.total_reg_1 = 0
        self.total_reg_2 = 0
        self.prefixo_ultimo = '00'
        self.estabelecimentos = []


#
####################### REGISTRO TIPO-0 (ABERTURA DO ARQUIVO) ################################
#

    def registro_0(self):
        reg = str(self.sequencial).zfill(6) # 001-006 sequencia do registro do arquivo
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14] # 007-020 inscri. CNPJ
        reg += self.prefixo.ljust(2) # 021-22 prefixo
        reg += '0' # 023-023 tipo registro
        reg += str(self.constante).zfill(1) # 024-024 constante
        reg += limpa_formatacao(self.cpf_cnpj_responsavel).zfill(14) # 025-038 cpf/cnpj do responsavel
        reg += self.tipo_inscricao.zfill(1) # 039-039 tipo de inscri.do responsavel
        reg += limpa_caged(self.razao_social_responsavel).ljust(40)[:40] # 040-079 razao social do responsavel
        reg += limpa_caged(self.endereco).ljust(40)[:40] # 080-119 endereço
        reg += self.numero.ljust(6)[:6] # 120-125 numero
        reg += limpa_caged(self.complemento).ljust(21)[:21] # 126-146 complemeto
        reg += limpa_caged(self.bairro).ljust(19)[:19] # 147-165 Bairro
        reg += limpa_formatacao(self.cep).zfill(8)[:8] # 166-173 CEP
        reg += self.codigo_municipio.zfill(7)[:7] # 174-180 codigo municipio
        reg += limpa_caged(self.nome_municipio).ljust(30)[:30] # 181-210 nome municipio
        reg += self.estado # 211-212 uf
        reg += limpa_fone(self.telefone).ljust(11)[:11] # 213-223 telefone
        reg += self.indetificado_retificacao # 224-224 retificacao

        if self.indetificado_retificacao == '1':
            reg += self.data_retificacao.strftime('%d%m%Y')
        else:
            reg += ''.ljust(8) # 225-232 data retificacao

        reg += self.data_geracao.strftime('%d%m%Y') # 233-240  data de geração do arquivo
        reg += self.email.strip().ljust(45)[:45] # 241-285 email responsavel
        reg += limpa_caged(self.nome_responsavel).ljust(52)[:52] # 286-337 nome responsavel
        reg += ''.ljust(24) # 338-361 espaços
        reg += limpa_formatacao(self.cpf_responsavel).zfill(11)[:11] # 362-372 cpf do responsavel
        reg += limpa_formatacao(self.crea_retificado).zfill(12)[:12] # 373- 384 registro CREA
        reg += self.data_nasc_resp.strftime('%d%m%Y') # 285-392  data de nasc. responsavel
        reg += ''.ljust(159)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        for estabelecimento in self.estabelecimentos:
            reg += estabelecimento.registro_1()
        return reg

#
####################### REGISTRO TIPO-9 (FECHAMENTO DO ARQUIVO) ################################
#

    def registro_9(self,sequencial, total_reg_1, total_reg_2 ):
        reg = str(sequencial).zfill(6) # 001-006 sequencia do registro do arquivo
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14] # 007-020 inscri. CNPJ
        reg += self.prefixo_ultimo.ljust(2) # 021-022 numero do ultimoprefixo
        reg += '9' # 023-023 tipo registro
        reg += str(total_reg_1).zfill(6)
        reg += str(total_reg_2).zfill(6)
        reg += ''.ljust(516)
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        return reg



#
####################### REGISTRO TIPO-1 ################################
#

class RAIS_Estabelecimento(object):
    def __init__(self, *args, **kwargs):
        self.sequencial = 0
        self.prefixo = '00'
        self.cnpj = ''
        self.razao_social = ''
        self.endereceo = ''
        self.numero = ''
        self.complemento = ''
        self.bairro = ''
        self.cep = ''
        self.codigo_municipio = 0
        self.nome_municipio = ''
        self.estado = ''
        self.telefone = ''
        self.email = ''
        self.cnae = ''
        self.natureza_juridica = ''
        self.numero_proprietarios = 0
        self.data_base = ''
        self.tipo_incr = 1
        self.tipo_rais = 0
        self.numero_cei = ''
        self.data_geracao = '2015'
        self.porte_empresa = '3'
        self.opt_simples = '2'
        self.indicador_pat = '2'
        self.pat_trabalhador = 0
        self.pat_trabalhador_acima = 0
        self.por_servico_proprio = 0
        self.por_adm_cozinha = 0
        self.por_ref_conv = 0
        self.por_ref_transp = 0
        self.por_cesta_alime= 0
        self.por_cesta_alime= 0
        self.por_vale_alimentacao_conv = 0
        self.indic_encer_ativ = '2'
        self.data_encer_ativ = ''
        self.cnpj_contr_patro = ''
        self.valor_contr_associativa = 0
        self.cnpj_contr_sindical = ''
        self.valor_contr_sindical = 0
        self.cnpj_contr_assintencial = ''
        self.valor_contr_assintencial = 0
        self.cnpj_contr_confederativa = ''
        self.valor_contr_confederativa = 0
        self.atividade_ano_base = '1'
        self.centralizado_pagto_contr_sindical = '2'
        self.cnpj_centralizado_contr_sindical = ''
        self.filiado_sindicato = '2'
        self.tipo_contr_ponto = '02'
        self.empregados = []


    def registro_1(self):
        reg = str(self.sequencial).zfill(6) # 001-006 sequencia do registro do arquivo
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14] # 007-020 inscri. CNPJ
        reg += self.prefixo.ljust(2) # 021-22 prefixo
        reg += '1' # 023-023 tipo registro
        reg += limpa_caged(self.razao_social).ljust(52)[:52] # 024-075 razao social
        reg += limpa_caged(self.endereco).ljust(40)[:40] # 076-115 endereço
        reg += str(self.numero).zfill(6)[:6] # 116-121 numero
        reg += limpa_caged(self.complemento).ljust(21)[:21] # 122-142 complemeto
        reg += limpa_caged(self.bairro).ljust(19)[:19] # 143-161 Bairro
        reg += limpa_formatacao(self.cep).zfill(8)[:8] # 162-169 CEP
        reg += str(self.codigo_municipio).zfill(7)[:7] # 170-176 codigo municipio
        reg += limpa_caged(self.nome_municipio).ljust(30)[:30] # 176-206 nome municipio
        reg += self.estado # 207-208 uf
        reg += limpa_fone(self.telefone).ljust(11)[:11] # 209-219 telefone
        reg += self.email.strip().ljust(45)[:45] # 220-264 email responsavel
        reg += limpa_formatacao(self.cnae).zfill(7)[:7] # 265-271 CNAE
        reg += str(self.natureza_juridica).zfill(4)[:4] # 272-275 NATUREZA JURIDICA
        reg += str(self.numero_proprietarios).zfill(4)[:4] # 276-279 numero de proprietarios
        reg += self.data_base.ljust(2)# 280-281  data base
        reg += str(self.tipo_incr).zfill(1) # 282-282  tipo inscricao
        reg += str(self.tipo_rais).zfill(1) # 283-283  tipo inscricao
        reg += ''.zfill(2) # 284-285
        reg += limpa_formatacao(self.numero_cei).zfill(12) # 286-297
        reg += self.data_geracao # 298-301 numero
        reg += self.porte_empresa.zfill(1) # 302-302 porte empresa
        reg += self.opt_simples.zfill(1) # 303-303 indicador op. simples
        reg += self.indicador_pat.zfill(1) # 304-304 ind. pat
        reg += str(self.pat_trabalhador).zfill(6) # 305-310 pat trabalhador
        reg += str(self.pat_trabalhador_acima).zfill(6) # 311-316 pat trabalhador acima de 5 mil
        reg += str(self.por_servico_proprio).zfill(3) # 317-319 pat trabalhador acima de 5 mil
        reg += str(self.por_adm_cozinha).zfill(3) # 320-322 porc.de adm cozinha
        reg += str(self.por_ref_conv).zfill(3) # 323-325 porc.de refeicao convenio
        reg += str(self.por_ref_transp).zfill(3) # 326-328 porc.de refeicoes transportadoras
        reg += str(self.por_cesta_alime).zfill(3) # 329-331 porc.de cesta alimentação
        reg += str(self.por_vale_alimentacao_conv).zfill(3) # 332-334 porc.de alimentação convenio
        reg += self.indic_encer_ativ.zfill(1) # 335-335 indic.encerramento ativ.

        if self.indic_encer_ativ == '1':
            reg += self.data_encer_ativ.strftime('%d%m%Y') # 336-343 data de enceramento
        else:
            reg += ''.zfill(8)

        reg += limpa_formatacao(self.cnpj_contr_patro).zfill(14)[:14] # 344-357 inscri. CNPJ patronal
        reg += str(self.valor_contr_associativa).zfill(9) # 358-366 valor contr. associativa patronal
        reg += limpa_formatacao(self.cnpj_contr_sindical).zfill(14)[:14] # 367-380 inscri. CNPJ contr. sindical
        reg += str(self.valor_contr_sindical).zfill(9) # 381-389 valor contr. sindical
        reg += limpa_formatacao(self.cnpj_contr_assintencial).zfill(14)[:14] # 390-403inscri. CNPJ contr. assintecial
        reg += str(self.valor_contr_assintencial).zfill(9) # 404-412 valor contr. assintecial
        reg += limpa_formatacao(self.cnpj_contr_confederativa).zfill(14)[:14] # 413-426  inscri. CNPJ contr. confederativa
        reg += str(self.valor_contr_confederativa).zfill(9) # 427-435 valor contr. confederativa
        reg += self.atividade_ano_base # 436-436 esteve em atividade ano Base
        reg += self.centralizado_pagto_contr_sindical # 437-437 centralizacao de contribuição sindical
        reg += limpa_formatacao(self.cnpj_centralizado_contr_sindical).zfill(14)[:14] # 438-451  CNPJ contr. sindical centralizado
        reg += self.filiado_sindicato # 452-452 Filiado ao sindicato?
        reg += self.tipo_contr_ponto # 453-454 Filiado ao sindicato?
        reg += ''.ljust(85) # 455-539 espaços
        reg += ''.ljust(12) #
        reg += '\r\n'
        reg = tira_acentos(reg).upper()
        for empregado in self.empregados:
            reg += empregado.registro_2()
        return reg

class RAIS_Empregado(object):
    def __init__(self, *args, **kwargs):
        self.rais_empresa = RAIS_Estabelecimento()
        self.sequencial = 0
        self.prefixo = '00'
        self.cnpj = ''
        self.cod_pis_pasep = ''
        self.nome_empregado = ''
        self.data_nascimento = hoje()
        self.nacionalidade = '10'
        self.ano_chegada = hoje()
        self.grau_instrucao = '01'
        self.cpf = ''
        self.ctps_numero = ''
        self.ctps_serie = ''
        self.data_admissao = hoje()
        self.tipo_admissao = '02'
        self.salario_contratual = 0
        self.tipo_salario_contratual = '1'
        self.horas_semanais = '44'
        self.numero_cbo = 0
        self.vinculo_empregaticio = 0
        self.codigo_desligamento = '10'
        self.data_desligamento = None
        self.remuneracao_janeiro = 0
        self.remuneracao_fevereiro = 0
        self.remuneracao_marco = 0
        self.remuneracao_abril = 0
        self.remuneracao_maio = 0
        self.remuneracao_junho = 0
        self.remuneracao_julho = 0
        self.remuneracao_agosto = 0
        self.remuneracao_setembro = 0
        self.remuneracao_outubro= 0
        self.remuneracao_novembro = 0
        self.remuneracao_dezembro = 0
        self.remuneracao_13_adiantamento = 0
        self.mes_13_adiantamento = 0
        self.remuneracao_13 = 0
        self.mes_13 = 0
        self.raca_cor = 0
        self.indicador_deficiencia = 2
        self.tipo_deficiencia = '0'
        self.indicador_alvara = 2
        self.aviso_previo_indenizado = 0
        self.sexo = 0
        self.motivo_primeiro_afastamento = 0
        self.data_inicio_primeiro_afastamento = None
        self.data_final_primeiro_afastamento = None
        self.motivo_segundo_afastamento = 0
        self.data_inicio_segundo_afastamento = None
        self.data_final_segundo_afastamento = None
        self.motivo_terceiro_afastamento = 0
        self.data_inicio_terceiro_afastamento = None
        self.data_final_terceiro_afastamento = None
        self.quantidade_dias_afastamento = 0
        self.valor_ferias_indenizadas = 0
        self.valor_banco_horas = 0
        self.quantidade_meses_banco_horas = 0
        self.valor_dissidio_coletivo = 0
        self.quantidade_meses_dissidio_coletivo = 0
        self.valor_gratificoes = 0
        self.quantidade_meses_gratificoes = 0
        self.valor_multa_rescisao_sem_justa_causa = 0
        self.cnpj_contribuicao_associativa_1 = ''
        self.valor_contribuicao_associativa_1 = 0
        self.cnpj_contribuicao_associativa_2 = ''
        self.valor_contribuicao_associativa_2 = 0
        self.cnpj_contribuicao_sindical = ''
        self.valor_contribuicao_sindical = 0
        self.cnpj_contribuicao_assistencial = ''
        self.valor_contribuicao_assistencial = 0
        self.cnpj_contribuicao_confederativa = ''
        self.valor_contribuicao_confederativa = 0
        self.municipio_local = 0
        self.horas_extras_trabalhadas_janeiro = ''
        self.horas_extras_trabalhadas_fevereiro = ''
        self.horas_extras_trabalhadas_marco = ''
        self.horas_extras_trabalhadas_abril = ''
        self.horas_extras_trabalhadas_maio = ''
        self.horas_extras_trabalhadas_junho = ''
        self.horas_extras_trabalhadas_julho = ''
        self.horas_extras_trabalhadas_agosto = ''
        self.horas_extras_trabalhadas_setembro = ''
        self.horas_extras_trabalhadas_outubro= ''
        self.horas_extras_trabalhadas_novembro = ''
        self.horas_extras_trabalhadas_dezembro = ''
        self.numero_indicador_sindicato = '2'
        self.informacao_empresa = ''

    def registro_2(self):
        reg = str(self.sequencial).zfill(6)[:6] # 001-006 sequencia do registro do arquivo
        reg += limpa_formatacao(self.cnpj).zfill(14)[:14] # 007-020 inscri. CNPJ
        reg += self.prefixo.ljust(2)[:2] # 021-22 prefixo
        reg += '2' # 023-023 tipo registro
        reg += limpa_formatacao(self.cod_pis_pasep).zfill(11)[:11] # 24-34  pis pasep
        reg += limpa_caged(self.nome_empregado).ljust(52)[:52]# 35-86 nome empregado
        reg += self.data_nascimento.strftime('%d%m%Y') # 87- 94 data nasc
        reg += str(self.nacionalidade).zfill(2)[:2]# 95-97 nacionalidade

        if self.nacionalidade != 10:
            reg += self.ano_chegada.strftime('%Y')[:4]# 98-100
        else:
            reg += ''.ljust(4)# 98-100

        reg += self.grau_instrucao.zfill(2)[:2]# 101-102
        reg += limpa_formatacao(self.cpf).zfill(11)[:11] # 103-113 cpf
        reg += limpa_formatacao(self.ctps_numero).zfill(8)[:8] # 114-121 ctps numero
        reg += limpa_formatacao(self.ctps_serie).zfill(5)[:5] # 122-126 ctps serie
        reg += self.data_admissao.strftime('%d%m%Y') # 127-134 data admissao
        reg += self.tipo_admissao.zfill(2)[:2] # 135-136 tipo admissao
        reg += str(int(self.salario_contratual * 100)).zfill(9)[:9] # 137-145 salario contratual
        reg += self.tipo_salario_contratual.zfill(1)[:1] # 146-146 tipo salario contratual
        reg += str(self.horas_semanais).zfill(2)[:44] # 147-148 horas semanais
        reg += str(self.numero_cbo).zfill(6)[:6] # 149-154 CBO
        reg += str(self.vinculo_empregaticio).zfill(2)[:2] # 155-156 Vinculo emppregaticio

        if self.data_desligamento:
            reg += str(self.codigo_desligamento).zfill(2)[:2] # 157-158 Codigo desligamento
            reg += self.data_desligamento.strftime('%d%m')[:4] # 159-162 data desligamento
        else:
            reg += ''.zfill(2) # 157-158 Codigo desligamento
            reg += ''.ljust(4) # 159-162 data desligamento

        reg += str(int(self.remuneracao_janeiro * 100)).zfill(9)[:9] # 163-171 remnumeraçao de janeiro
        reg += str(int(self.remuneracao_fevereiro * 100)).zfill(9)[:9] # 172-180 remnumeraçao de fevereiro
        reg += str(int(self.remuneracao_marco * 100)).zfill(9)[:9] # 181-189 remnumeraçao de março
        reg += str(int(self.remuneracao_abril * 100)).zfill(9)[:9] # 190-198 remnumeraçao de abril
        reg += str(int(self.remuneracao_maio * 100)).zfill(9)[:9] # 199-207 remnumeraçao de maio
        reg += str(int(self.remuneracao_junho * 100)).zfill(9)[:9] # 208-216 remnumeraçao de junho
        reg += str(int(self.remuneracao_julho * 100)).zfill(9)[:9] # 217-225 remnumeraçao de julho
        reg += str(int(self.remuneracao_agosto * 100)).zfill(9)[:9] # 226-234 remnumeraçao de agosto
        reg += str(int(self.remuneracao_setembro * 100)).zfill(9)[:9] # 235-243 remnumeraçao de setembro
        reg += str(int(self.remuneracao_outubro * 100)).zfill(9)[:9] # 244-252 remnumeraçao de outubro
        reg += str(int(self.remuneracao_novembro * 100)).zfill(9)[:9] # 253-261 remnumeraçao de novembro
        reg += str(int(self.remuneracao_dezembro * 100)).zfill(9)[:9] # 262-270 remnumeraçao de dezembro
        reg += str(int(self.remuneracao_13_adiantamento * 100)).zfill(9)[:9] # 271-279 remnumeraçao de 13º adiantamento
        reg += str(self.mes_13_adiantamento).zfill(2)[:2] # 280-281 mes de 13º adiantamento
        reg += str(int(self.remuneracao_13 * 100)).zfill(9)[:9] # 282-290 remnumeraçao de 13º
        reg += str(self.mes_13).zfill(2)[:2] # 291-292 mes de 13º
        reg += str(self.raca_cor).zfill(1)[:1] # 293-293 raça/cor
        reg += str(self.indicador_deficiencia).zfill(1)[:1] # 294-294 indicador deficiencia
        reg += self.tipo_deficiencia.zfill(1)[:1] # 295-295 tipo deficiencia
        reg += str(self.indicador_alvara).zfill(1)[:1] # 296-296 indicador alvara
        reg += str(int(self.aviso_previo_indenizado * 100)).zfill(9)[:9] # 297-305 aviso previo indenizado
        reg += str(self.sexo).zfill(1)[:1] # 306-306 sexo

        if self.data_inicio_primeiro_afastamento:
            reg += str(self.motivo_primeiro_afastamento).zfill(2)[:2] # 307-308 motivo primeiro afastamento
            reg += self.data_inicio_primeiro_afastamento.strftime('%d%m')[:4] # 309-312 data inicio primeiro afastamento
        else:
            reg += ''.ljust(2)
            reg += ''.ljust(4)

        if self.data_final_primeiro_afastamento:
            reg += self.data_final_primeiro_afastamento.strftime('%d%m')[:4] # 313-316 data final primeiro afastamento
        else:
            reg += ''.ljust(4)


        if self.data_inicio_segundo_afastamento:
            reg += str(self.motivo_segundo_afastamento).zfill(2)[:2] # 317-318 motivo segundo afastamento
            reg += self.data_inicio_segundo_afastamento.strftime('%d%m')[:4] # 319-322 data inicio segundo afastamento
        else:
            reg += ''.ljust(2)
            reg += ''.ljust(4)

        if self.data_final_segundo_afastamento:
            reg += self.data_final_segundo_afastamento.strftime('%d%m')[:4] # 323-326 data final segundo afastamento
        else:
            reg += ''.ljust(4)

        if self.data_inicio_terceiro_afastamento:
            reg += str(self.motivo_terceiro_afastamento).zfill(2)[:2] # 327-328 motivo terceiro afastamento
            reg += self.data_inicio_terceiro_afastamento.strftime('%d%m')[:4] # 329-332 data inicio terceiro afastamento
        else:
            reg += ''.ljust(2)
            reg += ''.ljust(4)

        if self.data_final_terceiro_afastamento:
            reg += self.data_final_terceiro_afastamento.strftime('%d%m')[:4] # 333-336 data final terceiro afastamento
        else:
            reg += ''.ljust(4)

        reg += str(self.quantidade_dias_afastamento).zfill(3)[:3] # 337-339 quantidade dias afastamento
        reg += str(int(self.valor_ferias_indenizadas * 100)).zfill(8)[:8] # 340-347 valor férias indenizadas
        reg += str(self.valor_banco_horas).zfill(8)[:8] # 348-355 valor banco de horas
        reg += str(self.quantidade_meses_banco_horas).zfill(2)[:2] # 356-357 quantidade de meses banco de hora
        reg += str(self.valor_dissidio_coletivo).zfill(8)[:8] # 358-365 valor dissidio coletivo
        reg += str(self.quantidade_meses_dissidio_coletivo).zfill(2) # 365-366 quantidade de meses dissidio coletivo
        reg += str(int(self.valor_gratificoes * 100)).zfill(8)[:8] # 367-375 valor gratificacoes
        reg += str(self.quantidade_meses_gratificoes).zfill(2)[:2] # 376-377 quantidade meses gratificacoes
        reg += str(int(self.valor_multa_rescisao_sem_justa_causa * 100 )).zfill(8)[:8] # 378-385 valor multa rescisao sem justa causa
        reg += limpa_formatacao(self.cnpj_contribuicao_associativa_1).zfill(14)[:14] # 386-399 cnpj contribuicao associativa 1 ocorrencia
        reg += str(int(self.valor_contribuicao_associativa_1 * 100)).zfill(8)[:8] # 400-407 valor contribuicao associativa 1 ocorrencia
        reg += limpa_formatacao(self.cnpj_contribuicao_associativa_2).zfill(14)[:14] # 408-421 cnpj contribuicao associativa 2 ocorrencia
        reg += str(int(self.valor_contribuicao_associativa_2 * 100)).zfill(8)[:8] # 422-429 valor contribuicao associativa 2 ocorrencia
        reg += limpa_formatacao(self.cnpj_contribuicao_sindical).zfill(14)[:14] # 430-443 cnpj contribuicao sindical
        reg += str(int(self.valor_contribuicao_sindical * 100)).zfill(8)[:8] # 444-451 valor contribuicao sindical
        reg += limpa_formatacao(self.cnpj_contribuicao_assistencial).zfill(14)[:14] # 452-465 cnpj contribuicao assintencial
        reg += str(int(self.valor_contribuicao_assistencial * 100)).zfill(8)[:8] # 466-473 valor contribuicao assintencial
        reg += limpa_formatacao(self.cnpj_contribuicao_confederativa).zfill(14)[:14] # 474-487 cnpj contribuicao confederativa
        reg += str(int(self.valor_contribuicao_confederativa * 100)).zfill(8)[:8] # 488-495 valor contribuicao confederativa
        reg += str(self.municipio_local).zfill(7)[:7] # 496-502 municipio loca de trabalho
        reg += str(self.horas_extras_trabalhadas_janeiro).zfill(3)[:3] # 163-171 horasextras trabalhadas de janeiro
        reg += str(self.horas_extras_trabalhadas_fevereiro).zfill(3)[:3] # 172-180 horasextras trabalhadas de fevereiro
        reg += str(self.horas_extras_trabalhadas_marco).zfill(3)[:3] # 181-189 horasextras trabalhadas de março
        reg += str(self.horas_extras_trabalhadas_abril).zfill(3)[:3] # 190-198 horasextras trabalhadas de abril
        reg += str(self.horas_extras_trabalhadas_maio).zfill(3)[:3] # 199-207 horasextras trabalhadas de maio
        reg += str(self.horas_extras_trabalhadas_junho).zfill(3)[:3] # 208-216 horasextras trabalhadas de junho
        reg += str(self.horas_extras_trabalhadas_julho).zfill(3)[:3] # 217-225 horasextras trabalhadas de julho
        reg += str(self.horas_extras_trabalhadas_agosto).zfill(3)[:3] # 226-234 horasextras trabalhadas de agosto
        reg += str(self.horas_extras_trabalhadas_setembro).zfill(3)[:3] # 235-243 horasextras trabalhadas de setembro
        reg += str(self.horas_extras_trabalhadas_outubro).zfill(3)[:3] # 244-252 horasextras trabalhadas de outubro
        reg += str(self.horas_extras_trabalhadas_novembro).zfill(3)[:3] # 253-261 horasextras trabalhadas de novembro
        reg += str(self.horas_extras_trabalhadas_dezembro).zfill(3)[:3] # 262-270 horasextras trabalhadas de dezembro
        reg += str(self.numero_indicador_sindicato).zfill(1)[:1] # 262-270 indicador filiação no sindicato
        reg += self.informacao_empresa.ljust(12)[:12] # 262-270 informacao empresa
        reg += '\r\n'
        reg = tira_acentos(reg).upper()

        return reg
