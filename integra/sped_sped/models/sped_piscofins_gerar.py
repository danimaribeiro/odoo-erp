# -*- coding: utf-8 -*-
#
# Geração do arquivo do SPED Fiscal PIS-COFINS
#

#from __future__ import division, print_function, unicode_literals

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
from sped_fiscal_gerar import *


class SPEDContribuicoes(SPEDFiscal):
    def __init__(self, *args, **kwargs):
        super(SPEDContribuicoes, self).__init__(*args, **kwargs)

        #
        # Versão do leiaute
        #
        self.versao = '002'

        self.situacao_especial = ''
        self.numero_recibo_anterior = ''
        self.al_pis = D('0.65')

        #
        # Blocos A, F e M exclusivos do PIS-COFINS
        #
        self.movimentos_blocos['A'] = False
        self.movimentos_blocos['C'] = False
        self.movimentos_blocos['D'] = False
        self.movimentos_blocos['E'] = False # Não há bloco E
        self.movimentos_blocos['F'] = False
        self.movimentos_blocos['G'] = False # Não há bloco G
        self.movimentos_blocos['H'] = False # Não há bloco H
        self.movimentos_blocos['M'] = False
        self.movimentos_blocos['1'] = False

        #
        # Lista com as filiais que comporão o arquivo,
        # inclusive a matriz
        #
        self.filiais = {}

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
        #self.registro_0100()
        self.registro_0110()
        self.registro_0140()
        self.registro_final_bloco('0')

        #
        # Bloco A
        #
        self.registro_inicial_bloco('A')
        self.registro_final_bloco('A')

        #
        # Bloco C
        #
        self.registro_inicial_bloco('C')
        self.registro_C010()
        self.registro_final_bloco('C')

        ####
        #### Bloco D
        ####
        ###self.registro_inicial_bloco('D')
        ####self.registro_D100()
        ####self.registro_D500()
        ###self.registro_final_bloco('D')

        ####
        #### Bloco F
        ####
        ###self.registro_inicial_bloco('F')
        ###self.registro_F010()
        ###self.registro_final_bloco('F')

        ####
        #### Bloco M
        ####
        ###self.registro_inicial_bloco('M')
        ###self.registro_final_bloco('M')

        ####
        #### Bloco 1
        ####
        ###self.registro_inicial_bloco('1')
        ###self.registro_1300()
        ###self.registro_1700()
        ###self.registro_final_bloco('1')

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

        self._arq.close()

    #
    # Bloco 0
    # Abertura, identificação e referências
    #
    def registro_0000(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0000'] = 1

        raiz_cnpj = self.filial.cnpj_cpf[:10]

        #
        # Aqui, vamos separar as filiais que comporão o arquivo
        # em ordem de CNPJ
        #
        self.sql_filiais = """
        select
            c.id, p.id, p.cnpj_cpf
        from
            res_company c
            join res_partner p on c.partner_id = p.id
        where
            p.cnpj_cpf like '{raiz_cnpj}/%'
        order by
            p.cnpj_cpf, c.id;
        """
        self.cr.execute(self.sql_filiais.format(raiz_cnpj=raiz_cnpj))
        dados = self.cr.fetchall()
        self.filiais = {}
        self.cnpjs = []

        for company_id, partner_id, cnpj_cpf in dados:
            if cnpj_cpf not in self.filiais:
                self.cnpjs.append(cnpj_cpf)
                self.filiais[cnpj_cpf] = self.filial.pool.get('res.partner').browse(self.cr, 1, partner_id)
                self.filiais[cnpj_cpf].company_ids = []

            self.filiais[cnpj_cpf].company_ids.append(company_id)

        ##
        ## Todos os tipos de documento
        ##
        #self.doc_icms = NotaFiscal.objects.order_by().filter(
            ##filial__in=self.filiais,
            #filial__in=filtro_filiais,
            #data_emissao__range=[self.data_inicial.strftime('%Y-%m-%d'), self.data_final.strftime('%Y-%m-%d')],
            #situacao__in=models.SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO,
        #).exclude(
            ##
            ## Vamos excluir as notas recebidas que ainda não tenham sido processadas
            ##
            #models.Q(emissao=models.TIPO_EMISSAO_TERCEIROS),
            #models.Q(modelo='55'),
            #models.Q(natureza_operacao__isnull=True) | models.Q(itens_originais_processados=False)
        #)
        ##.extra(
           ##where=['("fis_notafiscal"."filial_id" IN (SELECT f.id FROM conf_filial f WHERE f.cnpj_cpf ~ \'^' + unicode(self.filial.cnpj_cpf[:9]) + '.*\'))'],
        ##)


        ##
        ## Filtar por tipo de emissão/documento
        ## Somente emitidos ou somente recebidos
        ##
        #if self.tipo_documento == 'E':
            #self.doc_icms = self.doc_icms.filter(emissao=models.TIPO_EMISSAO_PROPRIA)
        #elif self.tipo_documento == 'R':
            #self.doc_icms = self.doc_icms.filter(emissao=models.TIPO_EMISSAO_TERCEIROS)

        ##
        ## Separa notas fiscais e conhecimentos de transporte
        ##
        ## NFs somente com itens com PIS-COFINS
        ##
        ##self.notasfiscais_gerais = self.doc_icms.filter(models.Q(modelo__in=MODELO_FISCAL_SPED_NF), models.Q(notafiscalitem__al_pis_proprio__gt=0) | models.Q(notafiscalitem__al_cofins_proprio__gt=0)).distinct().order_by('modelo', 'data_emissao', 'serie', 'numero')

        ##self.notasfiscais_gerais = self.doc_icms.filter(modelo__in=MODELO_FISCAL_SPED_NF).extra(
            ##where=['("fis_notafiscal"."id" IN (select nfi.notafiscal_id from fis_notafiscalitem nfi where nfi.cst_pis not in (\'\', \' \', \'  \')))'],
            ##).distinct().order_by('modelo', 'data_emissao', 'serie', 'numero')

        #self.notasfiscais_gerais = self.doc_icms.filter(
            #models.Q(modelo__in=MODELO_FISCAL_SPED_NF),
            #models.Q(id__in=NotaFiscalPISCOFINS.objects.all())
            #).distinct().order_by('modelo', 'data_emissao', 'serie', 'numero')

        #print(self.notasfiscais_gerais.query)
        #self.conhecimentostransporte_gerais = self.doc_icms.filter(modelo__in=MODELO_FISCAL_SPED_TRANSPORTE).order_by('modelo', 'data_emissao', 'serie', 'numero')
        #self.contasenergia_gerais = self.doc_icms.filter(modelo__in=('06', '29', '28')).order_by('modelo', 'data_emissao', 'serie', 'numero')
        #self.contastelefone_gerais = self.doc_icms.filter(modelo__in=('21', '22')).order_by('modelo', 'data_emissao', 'serie', 'numero')

        ##
        ## Retenções de impostos para o governo
        ##
        #self.retencoes_gerais = self.doc_icms.filter(models.Q(emissao=models.TIPO_EMISSAO_PROPRIA, modelo__in=MODELO_FISCAL_SPED_NF), models.Q(vr_pis_retido__gt=0) | models.Q(vr_cofins_retido__gt=0)).distinct().order_by('modelo', 'data_emissao', 'serie', 'numero')

        #self.movimentos_blocos['C'] = self.notasfiscais_gerais.count() or self.contasenergia_gerais.count()
        ##self.movimentos_blocos['D'] = self.conhecimentostransporte_gerais.count() or self.contastelefone_gerais.count()
        #self.movimentos_blocos['F'] = self.retencoes_gerais.count()
        #self.movimentos_blocos['1'] = self.retencoes_gerais.count()

        reg = '|0000'
        reg += '|' + self.versao
        reg += '|' + self.finalidade
        reg += '|' + self.situacao_especial
        reg += '|' + self.numero_recibo_anterior
        reg += '|' + self.data_inicial.strftime('%d%m%Y')
        reg += '|' + self.data_final.strftime('%d%m%Y')
        reg += '|' + self.filial.razao_social.strip()
        reg += '|' + limpa_formatacao(self.filial.cnpj_cpf)
        reg += '|' + self.filial.estado
        reg += '|' + self.filial.municipio_id.codigo_ibge[:7]
        reg += '|' + (self.filial.suframa or '')
        #reg += '|' + self.filial.natureza_juridica
        #reg += '|' + self.filial.tipo_atividade
        reg += '|' + '00' # Fixo: Sociedade empresária geral
        reg += '|' + '2' # Fixo: Comércio

        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_0110(self):
        self.totais_registros['geral'] += 1
        self.totais_registros['0110'] = 1

        reg = '|0110'
        reg += '|' + '1' # Regime não-cumulativo
        reg += '|' + '1' # Método de apropriação direta
        reg += '|' + '1' # Contribuição por alíquota básica
        reg += '|'
        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_0140(self):
        self.totais_registros['0140'] = 0

        for cnpj in self.cnpjs:
            filial = self.filiais[cnpj]
            self.totais_registros['geral'] += 1
            self.totais_registros['0140'] += 1
            reg = '|0140'

            #
            # Código é o CNPJ
            #
            reg += '|' + limpa_formatacao(filial.cnpj_cpf)
            reg += '|' + filial.razao_social.strip()
            reg += '|' + limpa_formatacao(filial.cnpj_cpf)
            reg += '|' + filial.estado
            reg += '|' + (filial.ie or '')
            reg += '|' + filial.municipio_id.codigo_ibge[:7]
            reg += '|' + (filial.im or '')
            reg += '|' + (filial.suframa or '')
            reg += '|\r\n'
            self._grava_registro(reg)

            self.filial_a_gerar = filial
            self.prepara_ids()

            self.registro_0150()
            self.registro_0190()
            self.registro_0200()
            self.registro_0400()

    #
    # Bloco C
    # Documentos Fiscais de mercadorias com ICMS e IPI
    #
    def registro_C010(self):
        if not self.movimentos_blocos['C']:
            return

        self.totais_registros['C010'] = 0

        for cnpj in self.cnpjs:
            filial = self.filiais[cnpj]
            self.filial_a_gerar = filial
            self.prepara_ids()

            #
            # Só envia as filiais que têm notas fiscais
            #
            if len(self.bloco_c100_ids + self.bloco_c500_ids):
                self.totais_registros['geral'] += 1
                self.totais_registros['C010'] += 1

                reg = '|C010'
                reg += '|' + limpa_formatacao(filial.cnpj_cpf)
                reg += '|' + '2' # Apuração detalhada
                reg += '|\r\n'
                self._grava_registro(reg)

                #
                # Chama os registros C100
                #
                self.registro_C100(piscofins=True)
                #self.registro_C500()

    def registro_C500(self):
        if not self.contasenergia.count():
            return ''

        self.totais_registros['C500'] = 0

        for nf in self.contasenergia.select_related('participante__cnpj_cpf').all():
            #
            # Prepara um queryset para uso posterior, retirando os itens
            # que sejam relativos a serviço para a apuração de ICMS e IPI
            #
            nf.itens_sem_servico = nf.notafiscalitem_set.exclude(produtoservico__tipo=models.TIPO_PRODUTO_SERVICO_SERVICOS).defer('infadic')

            self.totais_registros['geral'] += 1
            self.totais_registros['C500'] += 1
            reg = '|C500'
            reg += '|' + nf.participante.cnpj_cpf
            reg += '|' + nf.modelo
            reg += '|' + nf.situacao
            reg += '|' + nf.serie
            reg += '|' + nf.subserie
            reg += '|' + unicode(nf.numero)
            reg += '|' + nf.data_emissao.strftime('%d%m%Y')

            #
            # Envia a data de entrada/saída somente se o mês e ano forem
            # iguais ao mês e ano da data de emissão
            #
            if nf.data_entrada_saida and (unicode(nf.data_emissao.strftime('%Y%m')) == unicode(nf.data_entrada_saida.strftime('%Y%m'))):
                reg += '|' + nf.data_entrada_saida.strftime('%d%m%Y')
            else:
                reg += '|' + nf.data_emissao.strftime('%d%m%Y')

            reg += '|' + locale.format('%.2f', nf.vr_nf, grouping=False)
            reg += '|' + locale.format('%.2f', nf.vr_icms_proprio + nf.vr_icms_sn, grouping=False)
            reg += '|'
            reg += '|' + locale.format('%.2f', nf.vr_nf * D('1.65') / D('100.00'), grouping=False)
            reg += '|' + locale.format('%.2f', nf.vr_nf * D('7.6') / D('100.00'), grouping=False)
            reg += '|\r\n'
            self._grava_registro(reg)
            self.registro_C501(nf)
            self.registro_C505(nf)

    def registro_C501(self, nf):
        if not 'C501' in self.totais_registros.keys():
            self.totais_registros['C501'] = 0

        self.totais_registros['geral'] += 1
        self.totais_registros['C501'] += 1
        reg = '|C501'
        reg += '|50'
        reg += '|' + locale.format('%.2f', nf.vr_nf, grouping=False)

        #
        # Natureza do crédito
        #
        if nf.modelo == '06':
            reg += '|04' # Energia elétrica

        reg += '|' + locale.format('%.2f', nf.vr_nf, grouping=False)
        reg += '|1,65' # Alíquota
        reg += '|' + locale.format('%.2f', nf.vr_nf * D('1.65') / D('100.00'), grouping=False)
        reg += '|'
        reg += '|\r\n'
        self._grava_registro(reg)

    def registro_C505(self, nf):
        if not 'C505' in self.totais_registros.keys():
            self.totais_registros['C505'] = 0

        self.totais_registros['geral'] += 1
        self.totais_registros['C505'] += 1
        reg = '|C505'
        reg += '|50'
        reg += '|' + locale.format('%.2f', nf.vr_nf, grouping=False)

        #
        # Natureza do crédito
        #
        if nf.modelo == '06':
            reg += '|04' # Energia elétrica

        reg += '|' + locale.format('%.2f', nf.vr_nf, grouping=False)
        reg += '|7,6' # Alíquota
        reg += '|' + locale.format('%.2f', nf.vr_nf * D('7.6') / D('100.00'), grouping=False)
        reg += '|'
        reg += '|\r\n'
        self._grava_registro(reg)

    #
    # Bloco F
    # Demais documentos e operações
    #
    def registro_F010(self):
        if not self.movimentos_blocos['F']:
            return

        self.totais_registros['F010'] = 0

        for filial in self.filiais:
            self.retencoes = self.retencoes_gerais.filter(filial=filial)

            #
            # Só envia as filiais que têm notas fiscais
            #
            if self.retencoes.count():
                self.totais_registros['geral'] += 1
                self.totais_registros['F010'] += 1

                reg = '|F010'
                reg += '|' + filial.cnpj_cpf
                reg += '|\r\n'
                self._grava_registro(reg)

                #
                # Chama os registros F600
                #
                if not 'F600' in self.totais_registros.keys():
                    self.totais_registros['F600'] = 0

                self.registro_F600()


    def registro_F600(self):
        if not self.retencoes_gerais.count():
            return

        self.totais_registros['F600'] = 0

        #
        # Soma todos os valores de retenção
        #
        self.soma_retencoes = self.retencoes_gerais.values('participante__cnpj_cpf').annotate(
            soma_bc_irrf=Sum('bc_irrf'),
            soma_vr_irrf=Sum('vr_irrf'),
            soma_vr_cssl=Sum('vr_csll'),
            soma_vr_pis_retido=Sum('vr_pis_retido'),
            soma_vr_cofins_retido=Sum('vr_cofins_retido'),
        ).order_by()
        self.total_pis_retido = 0
        self.total_cofins_retido = 0

        print(self.soma_retencoes)

        for ret in self.soma_retencoes:
            self.totais_registros['geral'] += 1
            self.totais_registros['F600'] += 1
            reg = '|F600'
            #
            # Está fixo aqui como órgão público ou autarquia federal
            #
            reg += '|01'
            reg += '|' + self.data_final.strftime('%d%m%Y')
            reg += '|' + locale.format('%.2f', ret['soma_bc_irrf'], grouping=False)
            reg += '|' + locale.format('%.2f', ret['soma_vr_irrf'], grouping=False)
            reg += '|' # código da receita
            reg += '|1' # Receita cumulativa - alíquotas de 0,65% e 3%
            reg += '|' + ret['participante__cnpj_cpf']
            reg += '|' + locale.format('%.2f', ret['soma_vr_pis_retido'], grouping=False)
            self.total_pis_retido += ret['soma_vr_pis_retido']
            reg += '|' + locale.format('%.2f', ret['soma_vr_cofins_retido'], grouping=False)
            self.total_cofins_retido += ret['soma_vr_cofins_retido']
            reg += '|0' # Beneficiário do recolhimento
            reg += '|\r\n'
            self._grava_registro(reg)


    def registro_1300(self):
        if not self.retencoes_gerais.count():
            return

        self.totais_registros['geral'] += 1
        self.totais_registros['1300'] = 1
        reg = '|1300'

        #
        # Está fixo aqui como órgão público ou autarquia federal
        #
        reg += '|01'
        reg += '|' + self.retencoes_gerais[0].data_emissao.strftime('%m%Y')
        reg += '|' + locale.format('%.2f', self.total_pis_retido, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', self.total_pis_retido, grouping=False)
        reg += '|\r\n'
        self._grava_registro(reg)


    def registro_1700(self):
        if not self.retencoes_gerais.count():
            return

        self.totais_registros['geral'] += 1
        self.totais_registros['1700'] = 1
        reg = '|1700'

        #
        # Está fixo aqui como órgão público ou autarquia federal
        #
        reg += '|01'
        reg += '|' + self.retencoes_gerais[0].data_emissao.strftime('%m%Y')
        reg += '|' + locale.format('%.2f', self.total_cofins_retido, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', 0, grouping=False)
        reg += '|' + locale.format('%.2f', self.total_cofins_retido, grouping=False)
        reg += '|\r\n'
        self._grava_registro(reg)

    def prepara_ids(self):
        #
        # Todos os tipos de documento
        #
        self.sql_doc = """
        select
            d.id
        from
            sped_documento d
            join res_company c on c.id = d.company_id
            join res_partner p on p.id = c.partner_id
        where
            p.cnpj_cpf = '{cnpj}'
            and d.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
            and d.numero > 0
        """

        #
        # Para quem não tem crédito de PIS-COFINS
        # listar somente notas emitidas
        #
        if self.al_pis == D('0.65'):
            self.sql_a100 = self.sql_doc + """
                and d.modelo in ('SE', 'SC')
                and d.emissao = '0' and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_c100 = self.sql_doc + """
                and d.modelo in {MODELO_FISCAL_SPED_NF}
                and d.emissao = '0' and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_c500 = self.sql_doc + """
                and d.modelo in {MODELO_FISCAL_SPED_ENERGIA}
                and d.emissao = '0' and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_d100 = self.sql_doc + """
                and d.emissao = '0'
                and d.modelo in {MODELO_FISCAL_SPED_TRANSPORTE}
                and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_d500 = self.sql_doc + """
                and d.emissao = '0'
                and d.modelo in {MODELO_FISCAL_SPED_TELEFONE}
                and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """
        else:
            self.sql_a100 = self.sql_doc + """
                and d.modelo in ('SE', 'SC')
                and (
                        d.emissao = '0'
                    or d.situacao in ('00', '01')
                )
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_c100 = self.sql_doc + """
                and d.modelo in {MODELO_FISCAL_SPED_NF}
                and (
                        d.emissao = '0'
                    or d.situacao in ('00', '01')
                )
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_c500 = self.sql_doc + """
                and d.modelo in {MODELO_FISCAL_SPED_ENERGIA}
                and d.emissao = '1' and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_d100 = self.sql_doc + """
                and d.emissao = '1'
                and d.modelo in {MODELO_FISCAL_SPED_TRANSPORTE}
                and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

            self.sql_d500 = self.sql_doc + """
                and d.emissao = '1'
                and d.modelo in {MODELO_FISCAL_SPED_TELEFONE}
                and d.situacao in ('00', '01')
            order by
                d.modelo,
                d.data_emissao_brasilia,
                d.serie,
                d.numero;
            """

        self.bloco_a100_ids = self._busca_ids(self.sql_a100)
        self.bloco_a_ids = self.bloco_a100_ids

        self.bloco_c100_ids = self._busca_ids(self.sql_c100)
        self.bloco_c500_ids = self._busca_ids(self.sql_c500)
        self.bloco_c_ids = self.bloco_c100_ids + self.bloco_c500_ids

        self.bloco_d100_ids = self._busca_ids(self.sql_d100)
        self.bloco_d500_ids = self._busca_ids(self.sql_d500)
        self.bloco_d_ids = self.bloco_d100_ids + self.bloco_d500_ids

        #
        # Inventário é obrigatório no mês de fevereiro
        #
        #self.inventario = Inventario.objects.filter(filial=self.filial_id, data_sped__month=self.data_inicial.month, data_sped__year=self.data_inicial.year)
        #if self.inventario.count() != 0:
            #self.movimentos_blocos['H'] = True

        #
        # Participantes de todos os documentos envolvendo ICMS, desde que ativos, ou sejam terceiros no inventário
        #
        self.sql_participantes = """
        select
            p.id
        from
            res_partner p
            join sped_documento d on d.partner_id = p.id
        where
            d.id in {DOC_IDS}
        order by
            p.cnpj_cpf;
        """

        #if (self.inventario.count() == 0) or (self.inventario[0].inventarioitem_set.count() == 0):
        #self.participantes = Participante.objects.filter(fis_notafiscal_participante__in=doc_icms_ativos_participantes).distinct()
        #else:
            #self.participantes = Participante.objects.filter(
                #models.Q(fis_notafiscal_participante__in=doc_icms_ativos_participantes) | models.Q(inventarioitem__in=self.inventario[0].inventarioitem_set.all())).distinct()

        self.participante_ids = self._busca_ids(self.sql_participantes, {'DOC_IDS': tuple(self.bloco_c_ids + self.bloco_d_ids)})

        #notasterceiros = self.notasfiscais.filter(emissao=models.TIPO_EMISSAO_TERCEIROS).only('id')
        #notasterceiros = self.notasfiscais.all().only('id')
        #itensterceiros = NotaFiscalItem.objects.filter(notafiscal__in=notasterceiros).only('produtoservico__id')

        #if (self.inventario.count() == 0) or (self.inventario[0].inventarioitem_set.count() == 0):
            #self.produtos = ProdutoServico.objects.filter(notafiscalitem__in=itensterceiros).distinct()
        #else:
            #self.produtos = ProdutoServico.objects.filter(
                #models.Q(notafiscalitem__in=itensterceiros) | models.Q(inventarioitem__in=self.inventario[0].inventarioitem_set.all())).distinct()

        #
        # Produtos, unidades e naturezas de operação, somente de notas de treceiros
        #
        self.sql_produtos = """
        select
            p.id
        from
            product_product p
            join sped_documentoitem di on di.produto_id = p.id
            join sped_documento d on di.documento_id = d.id
        where
            d.emissao = '1'
            and d.id in {DOC_IDS}
        order by
            p.id;
        """
        self.produto_ids = self._busca_ids(self.sql_produtos, {'DOC_IDS': tuple(self.bloco_c_ids + self.bloco_d_ids)})

        #self.unidades = Unidade.objects.filter(cad_produtoservico_unidade__in=self.produtos).distinct()
        self.sql_unidades = """
        select
            u.id
        from
            product_uom u
            join product_template t on t.uom_id = u.id
            join product_product p on p.product_tmpl_id = t.id
        where
            p.id in {PRODUTO_IDS}
        order by
            u.name;
        """

        if len(self.produto_ids) == 0:
            self.unidade_ids = []
        else:
            self.unidade_ids = self._busca_ids(self.sql_unidades, {'PRODUTO_IDS': tuple(self.produto_ids)})

        #self.naturezas = NaturezaOperacao.objects.filter(notafiscal__in=notasterceiros).distinct()
        self.sql_naturezas = """
        select
            n.id
        from
            sped_naturezaoperacao n
            join sped_documento d on d.naturezaoperacao_id = n.id
        where
            d.emissao = '1'
            and d.id in {DOC_IDS}
        order by
            n.codigo;
        """
        self.natureza_ids = self._busca_ids(self.sql_naturezas, {'DOC_IDS': tuple(self.bloco_c_ids + self.bloco_d_ids)})

        if len(self.bloco_c_ids):
            self.movimentos_blocos['C'] = True
            self.movimentos_blocos['E'] = True

        if len(self.bloco_d_ids):
            self.movimentos_blocos['D'] = True
            self.movimentos_blocos['E'] = True
