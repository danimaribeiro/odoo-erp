# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
from pybrasil.telefone.telefone import separa_fone
from integracao_questor import integracao_questor, integracao_questor_fiscal_A, integracao_questor_fiscal_B, integracao_questor_fiscal_C, integracao_questor_fiscal_D, integracao_questor_fiscal_E, integracao_questor_fiscal_F, integracao_questor_fiscal_G, integracao_questor_fiscal_H, integracao_questor_fiscal_J, integracao_questor_fiscal_K, integracao_questor_fiscal_KI, integracao_questor_fiscal_L, integracao_questor_fiscal_L, integracao_questor_fiscal_M, integracao_questor_fiscal_N, integracao_questor_fiscal_O, integracao_questor_fiscal_R
import base64
import os
from pybrasil.inscricao import limpa_formatacao
from sped.constante_tributaria import *


MODELO_FISCAL_QUESTOR = [
         ('1', 'Emissão Própria'),
         ('2', 'Emissão Terceiros'),
]


class questor_fiscal(osv.Model):
    _description = u'Exportação Fiscal'
    _name = 'questor.fiscal'
    _rec_name = 'nome'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = exp_obj.id

        return res


    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'arquivo_texto': fields.text(u'Arquivo'),
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'codigo_empresa_questor': fields.integer(string='Código da empresa no Questor'),
        'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão'),
        'modelo_fiscal': fields.selection(MODELO_FISCAL, u'Modelo Fiscal'),
        'forca_unidade': fields.boolean(u'Forçar somente a unidade?'),
        'centro_custo': fields.boolean(u' Gerar Bloco O (Centro de Custo)?')
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'emissao': '0',
        'modelo_fiscal': '55',
        'forca_unidade': False,
    }


    def gera_exportacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for export_obj in self.browse(cr, uid, ids):

            sql = u"""
            select
                sd.id
            from
                     sped_documento sd
                join res_company c on c.id = sd.company_id
                join res_partner rp on rp.id = c.partner_id

            where
            """

            if export_obj.forca_unidade:
                sql += """c.id = {company_id}"""
            else:
                sql += """c.cnpj_cpf = '{cnpj_cpf}'"""

            sql += """
                and sd.emissao = '{emissao}'
                and sd.modelo = '{modelo}'
                --and sd.situacao in ('00', '01')
                and (
                    (sd.emissao = '0' and sd.state = 'autorizada' and sd.modelo in ('55','SE'))
                    or
                    (sd.emissao = '1')
                    or
                    (sd.modelo not in ('55','SE'))
                )
                and (
                    (       sd.emissao = '0'
                        and sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
                    ) or
                    (       sd.emissao = '1'
                        and sd.data_entrada_saida_brasilia between '{data_inicial}' and '{data_final}'
                    )
                )

            order by
                c.name,
                sd.data_emissao_brasilia,
                sd.numero;
            """

            filtro = {
                'data_inicial': export_obj.data_inicial,
                'data_final': export_obj.data_final,
                'cnpj_cpf': export_obj.company_id.cnpj_cpf,
                'emissao': export_obj.emissao,
                'modelo': export_obj.modelo_fiscal,
                'company_id': export_obj.company_id.id,
            }

            cr.execute(sql.format(**filtro))

            dados = cr.fetchall()

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe documentos nos parâmetros informados!')

            documento_ids = []
            for ret in dados:
                documento_ids.append(ret[0])

            documento_objs = self.pool.get('sped.documento').browse(cr, 1, documento_ids)

            arquivo_text = u''

            #
            # Gerar bloco A
            #
            for documento_obj in documento_objs:

                registro_a = integracao_questor_fiscal_A()

                if documento_obj.partner_id.razao_social:
                    registro_a.nomepessoa = documento_obj.partner_id.razao_social
                else:
                    registro_a.nomepessoa = documento_obj.partner_id.name or u''

                if len(documento_obj.partner_id.cnpj_cpf or '') == 18:
                    registro_a.tipoinscr = 2
                else:
                    registro_a.tipoinscr = 1

                registro_a.inscrfederal = limpa_formatacao(documento_obj.partner_id.cnpj_cpf or '')
                registro_a.enderecopessoa =  documento_obj.partner_id.endereco or ''
                registro_a.numenderpessoa =  documento_obj.partner_id.numero or ''
                registro_a.complenderpessoa = documento_obj.partner_id.complemento or ''
                registro_a.bairroenderpessoa = documento_obj.partner_id.bairro or ''
                registro_a.siglaestado = documento_obj.partner_id.estado or ''

                if documento_obj.partner_id.municipio_id.codigo_ibge:
                    registro_a.codigomunic = documento_obj.partner_id.municipio_id.codigo_ibge[:7] or ''
                registro_a.cependerpessoa = documento_obj.partner_id.cep or ''

                ddd, fone = separa_fone(documento_obj.partner_id.fone or '')
                registro_a.dddfone = ddd or ''
                registro_a.numerofone = fone or ''

                registro_a.produtrural = 'N'
                registro_a.inscrprod = ''
                registro_a.inscrestad = documento_obj.partner_id.ie or ''
                registro_a.email = ''
                registro_a.paginainternet = ''
                if documento_obj.partner_id.im:
                    registro_a.inscrmunic = documento_obj.partner_id.im or ''
                registro_a.codigoativfederal = ''

                arquivo_text += registro_a.registro_A()

            registros_b = []
            for documento_obj in documento_objs:

                for documentoitem_obj in documento_obj.documentoitem_ids:

                    if documentoitem_obj.produto_id.id:
                        if documentoitem_obj.produto_id.id not in registros_b:
                            registro_b = integracao_questor_fiscal_B()
                            registro_b.codigoempresa = export_obj.codigo_empresa_questor
                            registro_b.referenproduto = documentoitem_obj.produto_id.id
                            registro_b.codigogrupoproduto = 1
                            registro_b.descrproduto = documentoitem_obj.produto_id.name or ''

                            if documentoitem_obj.produto_id.ncm_id:
                                ncm = documentoitem_obj.produto_id.ncm_id.codigo or ''
                                registro_b.codigoncm = ncm[0:4] + '.' + ncm[4:6] + '.' + ncm[6:8]

                            if documentoitem_obj.produto_id.uom_id:
                                registro_b.unidademedida = documentoitem_obj.produto_id.uom_id.name or ''

                            registro_b.dacon = 1
                            #registro_b.dacontiporeceita = 1
                            registro_b.indicadortipo = documentoitem_obj.produto_id.tipo or '00'
                            registro_b.tipomedicamento = ''
                            registro_b.incentivofis = ''
                            registro_b.tipocredito = ''
                            registro_b.tipodebito = ''

                            arquivo_text += registro_b.registro_B()
                            registros_b.append(documentoitem_obj.produto_id.id)

            for documento_obj in documento_objs:
                #
                # Registro C
                #
                regist_c = True
                registro_c = integracao_questor_fiscal_C()

                registro_c.codigoestab = limpa_formatacao(documento_obj.company_id.partner_id.cnpj_cpf)
                registro_c.codigopessoa = limpa_formatacao(documento_obj.partner_id.cnpj_cpf)
                registro_c.numeronf = documento_obj.numero
                registro_c.numeronffinal = documento_obj.numero
                registro_c.especienf = documento_obj.modelo
                registro_c.serienf = documento_obj.serie or ''
                registro_c.subserienf = documento_obj.subserie or ''
                registro_c.datalctofis = parse_datetime(documento_obj.data_emissao_brasilia).date()
                registro_c.valorcontabil = D(documento_obj.vr_nf or 0).quantize(D('0.01'))
                registro_c.basecalculoipi = D(documento_obj.bc_ipi or 0).quantize(D('0.01'))
                registro_c.valoripi = D(documento_obj.vr_ipi or 0).quantize(D('0.01'))
                registro_c.isentasipi = 0
                registro_c.outrasipi = 0
                registro_c.contribuinte = 'N'
                registro_c.acrescimofinanceiro = 0
                if documento_obj.emissao == '0':
                    registro_c.siglaestadoorigem = documento_obj.company_id.partner_id.estado or ''
                else:
                    registro_c.siglaestadoorigem = documento_obj.partner_id.estado or ''

                if documento_obj.emissao == '0':
                    registro_c.codigomunicorigem = documento_obj.company_id.partner_id.cidade or ''
                else:
                    registro_c.codigomunicorigem = documento_obj.partner_id.cidade or ''

                registro_c.complhist = ''

                registro_c.codigotipodctosintegra = 01

                if documento_obj.emissao == '0':
                    registro_c.emitentenf = 'P'
                else:
                    registro_c.emitentenf = 'T'

                registro_c.modalidadefrete = 1
                registro_c.adicionaliss = ''

                if documento_obj.situacao in ['02','03']:
                    registro_c.cancelada = 'S'


                registro_c.conciliada = 'N'
                registro_c.chaveorigem = ''
                registro_c.desfeitonegocio = ''

                registro_c.vlrdesc = D(documento_obj.vr_desconto or 0).quantize(D('0.01'))
                registro_c.vlrabatntrib = 0
                registro_c.vlrfrete = D(documento_obj.vr_frete or 0).quantize(D('0.01'))
                registro_c.vlrseguro = D(documento_obj.vr_seguro or 0).quantize(D('0.01'))
                registro_c.vlroutrdesp = D(documento_obj.vr_outras or 0).quantize(D('0.01'))
                registro_c.cdmodelo = documento_obj.modelo
                registro_c.chavenfesai = documento_obj.chave or ''
                registro_c.chavenfesairef = ''
                registro_c.cdsituacao = documento_obj.situacao
                registro_c.indpagto = ''
                arquivo_text += registro_c.registro_C()

                registros_d = {}
                for documentoitem_obj in documento_obj.documentoitem_ids:
                    if documentoitem_obj.produto_id.id:
                        chave_d = str(documentoitem_obj.cfop_id.codigo or 0)
                        chave_d += '_'

                        if documento_obj.modelo == 'SE':
                            chave_d += str(documentoitem_obj.al_iss or 0)
                        else:
                            chave_d += str(documentoitem_obj.al_icms_proprio or 0)

                        if chave_d in registros_d:
                            registro_d = registros_d[chave_d]
                        else:
                            registro_d = integracao_questor_fiscal_D()
                            registros_d[chave_d] = registro_d

                            if documentoitem_obj.cfop_id:
                                registro_d.codigocfop = D(documentoitem_obj.cfop_id.codigo or 0)
                            else:
                                registro_d.codigocfop = 0

                            if documento_obj.modelo == 'SE':
                                registro_d.tipoimposto = 2
                            else:
                                registro_d.tipoimposto = 1

                            if documento_obj.modelo == 'SE':
                                registro_d.aliqimposto = D(documentoitem_obj.al_iss or 0).quantize(D('0.01'))
                            else:
                                registro_d.aliqimposto = D(documentoitem_obj.al_icms_proprio or 0).quantize(D('0.01'))

                        registro_d.valorcontabilimposto += D(documentoitem_obj.vr_nf or 0).quantize(D('0.01'))

                        if documento_obj.modelo == 'SE':
                            registro_d.basecalculoimposto = D(documento_obj.bc_iss or 0).quantize(D('0.01'))
                            registro_d.valorimposto = D(documento_obj.vr_iss or 0).quantize(D('0.01'))
                        else:
                            registro_d.basecalculoimposto += D(documentoitem_obj.bc_icms_proprio or 0).quantize(D('0.01'))
                            registro_d.valorimposto += D(documentoitem_obj.vr_icms_proprio or 0).quantize(D('0.01'))

                        registro_d.isentasimposto = 0

                        if documento_obj.modelo == 'RL':
                            registro_d.outrasimposto += D(documentoitem_obj.bc_iss or 0).quantize(D('0.01'))
                        #else:
                            #registro_d.outrasimposto += D(documentoitem_obj.bc_icms_proprio or 0).quantize(D('0.01'))

                        registro_d.valorexvaloradicional = 0
                        registro_d.codigotabctbfis = 0

                for chave_d in registros_d:
                    arquivo_text += registros_d[chave_d].registro_D()

                sequencia = 1
                for documentoitem_obj in documento_obj.documentoitem_ids:
                    if documentoitem_obj.produto_id.id:
                        registro_f = integracao_questor_fiscal_F()

                        registro_f.seq = sequencia
                        sequencia += 1

                        if documentoitem_obj.cfop_id:
                            registro_f.codigocfop = D(documentoitem_obj.cfop_id.codigo or 0).quantize(D('0.01'))
                        else:
                            registro_f.codigocfop = 0


                        registro_f.codigoproduto = str(documentoitem_obj.produto_id.id)
                        registro_f.codigosituacaotribut = D(documentoitem_obj.cst_icms or 0).quantize(D('0.01'))

                        if documentoitem_obj.produto_id.uom_id:
                            registro_f.unidademedida = documentoitem_obj.produto_id.uom_id.name or ''

                        registro_f.quantidade = D(documentoitem_obj.quantidade or 0).quantize(D('0.01'))
                        registro_f.valorunitario = D(documentoitem_obj.vr_unitario or 0).quantize(D('0.01'))
                        registro_f.valortotal = D(documentoitem_obj.vr_produtos or 0).quantize(D('0.01'))
                        registro_f.basecalculoicms = D(documentoitem_obj.bc_icms_proprio or 0).quantize(D('0.01'))
                        registro_f.aliqicms = D(documentoitem_obj.al_icms_proprio or 0).quantize(D('0.01'))
                        registro_f.valoricms = D(documentoitem_obj.vr_icms_proprio or 0).quantize(D('0.01'))
                        registro_f.isentasicms = 0
                        registro_f.outrasicms = 0
                        registro_f.basecalculoipi = D(documentoitem_obj.bc_ipi or 0).quantize(D('0.01'))
                        registro_f.aliqipi = D(documentoitem_obj.al_ipi or 0).quantize(D('0.01'))
                        registro_f.valoripi = D( documentoitem_obj.vr_ipi or 0).quantize(D('0.01'))
                        registro_f.isentasipi = 0
                        registro_f.outrasipi = 0
                        registro_f.basecalculoiss = D(documentoitem_obj.bc_iss or 0).quantize(D('0.01'))
                        registro_f.aliqiss = D(documentoitem_obj.al_iss or 0).quantize(D('0.01'))
                        registro_f.valoriss = D(documentoitem_obj.vr_iss or 0).quantize(D('0.01'))
                        registro_f.isentasiss = 0
                        registro_f.outrasiss = 0
                        registro_f.basecalculosubtribut = D(documentoitem_obj.bc_icms_st or 0).quantize(D('0.01'))
                        registro_f.aliqsubtribut = D(documentoitem_obj.al_icms_st or 0).quantize(D('0.01'))
                        registro_f.valorsubtribut = D(documentoitem_obj.vr_icms_st or 0).quantize(D('0.01'))
                        registro_f.valordesconto = D(documentoitem_obj.vr_desconto or 0).quantize(D('0.01'))
                        registro_f.valordespesa = D(documentoitem_obj.vr_outras or 0).quantize(D('0.01'))
                        registro_f.tipoestoque = 1
                        registro_f.cstipi = documentoitem_obj.cst_ipi or 0
                        registro_f.cstiss = documentoitem_obj.cst_iss or 0
                        registro_f.cststicms = 00
                        registro_f.qtdeseloipi = 0
                        registro_f.vlrfrete = D(documentoitem_obj.vr_frete or 0).quantize(D('0.01'))
                        registro_f.vlrseguro = D(documentoitem_obj.vr_seguro or 0).quantize(D('0.01'))
                        registro_f.abatnaotrib = 0
                        registro_f.outrassubtrib = 0
                        registro_f.isentassubtrib = 0
                        registro_f.indmov = ''

                        arquivo_text += registro_f.registro_F()

                for documentoitem_obj in documento_obj.documentoitem_ids:

                    if documentoitem_obj.produto_id.id:

                        #
                        # Registro G
                        #

                        registro_g = integracao_questor_fiscal_G()

                        registro_g.codigoproduto = str(documentoitem_obj.produto_id.id)

                        if documentoitem_obj.cfop_id:
                            registro_g.codigocfop = D(documentoitem_obj.cfop_id.codigo or 0).quantize(D('0.01'))
                        else:
                            registro_g.codigocfop = 0
                        if documento_obj.emissao == 0 and documento_obj.entrada_saida == '0':
                            registro_g.receitapiscofins = documento_objs.vr_pis_proprio + documento_objs.vr_cofins_proprio
                        elif documento_obj.emissao == 1 and documentoitem_obj.credita_pis_cofins:
                            registro_g.receitapiscofins = documento_objs.vr_pis_proprio + documento_objs.vr_cofins_proprio
                        else:
                            registro_g.receitapiscofins = 0

                        registro_g.basecalculopiscofins = D(documentoitem_obj.bc_pis_proprio or 0).quantize(D('0.01'))

                        registro_g.aliqpis = D(documentoitem_obj.al_pis_proprio or 0).quantize(D('0.01'))
                        registro_g.valorpis = D(documentoitem_obj.vr_pis_proprio or 0).quantize(D('0.01'))
                        registro_g.aliqcofins = D(documentoitem_obj.al_cofins_proprio or 0).quantize(D('0.01'))
                        registro_g.valorcofins = D(documentoitem_obj.vr_cofins_proprio or 0).quantize(D('0.01'))

                        if documentoitem_obj.md_pis_proprio == MODALIDADE_BASE_PIS_QUANTIDADE:
                            registro_g.quantidade =  documentoitem_obj.quantidade
                        else:
                            registro_g.quantidade = 0

                        registro_g.cdsituatributpis = D(documentoitem_obj.cst_pis or 0).quantize(D('0.01'))
                        registro_g.cdsituatributcofins = D(documentoitem_obj.cst_cofins or 0).quantize(D('0.01'))
                        registro_g.pissubstrib = D(documentoitem_obj.vr_pis_st or 0).quantize(D('0.01'))
                        registro_g.cofinssubstrib = D( documentoitem_obj.vr_cofins_st or 0).quantize(D('0.01'))
                        registro_g.tipodebito = ''

                        arquivo_text += registro_g.registro_G()

                for documentoitem_obj in documento_obj.documentoitem_ids:

                    if documentoitem_obj.produto_id.id:

                        #
                        # Registro H
                        #

                        registro_h = integracao_questor_fiscal_H()

                        registro_h.codigoestab = limpa_formatacao(documento_obj.company_id.partner_id.cnpj_cpf)
                        registro_h.valordespesa = D(documentoitem_obj.vr_outras or 0).quantize(D('0.01'))
                        registro_h.codigoantecipacao = 0
                        registro_h.codigooperacaofis = 0
                        registro_h.basecalculosubtribut= D(documentoitem_obj.bc_icms_st or 0).quantize(D('0.01'))
                        registro_h.valorsubtribut = D(documentoitem_obj.vr_icms_st or 0).quantize(D('0.01'))
                        registro_h.basecalcicmsprop = D(documentoitem_obj.bc_icms_proprio or 0).quantize(D('0.01'))
                        registro_h.valoricmsprop = D(documentoitem_obj.vr_icms_proprio or 0).quantize(D('0.01'))
                        registro_h.siglaestado = ''
                        registro_h.codigoobs = ''
                        registro_h.complobs = ''

                        if documentoitem_obj.cfop_id:
                            registro_h.codigocfop = D(documentoitem_obj.cfop_id.codigo or 0).quantize(D('0.01'))
                        else:
                            registro_h.codigocfop = 0

                        registro_h.codigoproduto = str(documentoitem_obj.produto_id.id)

                        if documento_obj.modelo == 'SE':
                            registro_h.aliqimpostocfop = D(documentoitem_obj.al_iss or 0).quantize(D('0.01'))
                        else:
                            registro_h.aliqimpostocfop = D(documentoitem_obj.al_icms_proprio or 0).quantize(D('0.01'))

                        arquivo_text += registro_h.registro_H()


                #
                # Registro O
                #
                registro_o = integracao_questor_fiscal_O()

                if export_obj.centro_custo:
                    #
                    # Verifica se o último campo no nome da empresa é um nº;
                    # se for, usa como código do centro de custo
                    #
                    tmp = documento_obj.company_id.name.split()
                    if tmp[-1].isdigit():
                        registro_o.codigocentrocusto = tmp[-1]

                    else:
                        registro_o.codigocentrocusto = documento_obj.company_id.id

                    registro_o.percentual = 100

                arquivo_text += registro_o.registro_O()


                #
                # Registro R
                #
                registro_r = integracao_questor_fiscal_R()

                #Órgãos, Autarquias e Fundacoes Federais=1;
                #Demais Entidades da Administração Pública Federal=2;
                #Pessoas Jurídicas de Direito Privado=3;
                #Órgãos, Autarquias e Fundacoes dos Estados, Distrito Federal e Municípios=4;
                #Sociedade Cooperativa=5;
                #Fabricantes de Veículos e Máquinas=6;

                if documento_obj.partner_id.eh_orgao_publico:
                    registro_r.tiporetencao = 4
                elif documento_obj.partner_id.eh_cooperativa:
                    registro_r.tiporetencao = 5
                else:
                    registro_r.tiporetencao = 3

                if not documento_obj.vr_irrf:
                    documento_obj.al_irrf = 0
                    documento_obj.bc_irrf = 0
                    documento_obj.vr_irrf = 0

                if not documento_obj.vr_previdencia:
                    documento_obj.al_previdencia = 0
                    documento_obj.vr_previdencia = 0
                    documento_obj.bc_previdencia = 0

                if not documento_obj.vr_iss_retido:
                    documento_obj.al_iss = 0
                    documento_obj.vr_iss_retido = 0
                    documento_obj.bc_iss_retido = 0

                if not documento_obj.vr_pis_retido:
                    documento_obj.al_pis_retido = 0
                    documento_obj.vr_pis_retido = 0
                    documento_obj.bc_pis_proprio = 0

                if not documento_obj.vr_cofins_retido:
                    documento_obj.al_cofins_retido = 0
                    documento_obj.vr_cofins_retido = 0
                    documento_obj.bc_cofins_proprio = 0

                if not documento_obj.vr_csll:
                    documento_obj.al_csll = 0
                    documento_obj.vr_csll = 0

                registro_r.basecalculoinss = documento_obj.bc_previdencia
                registro_r.aliqinss = documento_obj.al_previdencia
                registro_r.valorinss = documento_obj.vr_previdencia
                registro_r.basecalculoirpj = 0
                registro_r.aliqirpj = 0
                registro_r.valorirpj = 0
                registro_r.basecalculoissqn = documento_obj.bc_iss_retido
                registro_r.aliqissqn = documento_obj.vr_iss_retido / (documento_obj.bc_iss_retido or 1) * 100
                registro_r.valorissqn = documento_obj.vr_iss_retido
                registro_r.basecalculoirrf = documento_obj.bc_irrf
                registro_r.aliqirrf = documento_obj.al_irrf
                registro_r.valorirrf = documento_obj.vr_irrf
                registro_r.codigoimpostoirrf = 0
                registro_r.variacaoimpostoirrf = 0
                #registro_r.dataprevirrfirpj = ''
                #registro_r.datapgtoirrfirpj = ''
                registro_r.totalpiscofinscsll = D(documento_obj.vr_pis_retido + documento_obj.vr_cofins_retido + documento_obj.vr_csll or 0).quantize(D('0.01'))
                registro_r.basecalculopis = documento_obj.bc_pis_proprio
                registro_r.aliqpis = documento_obj.al_pis_retido
                registro_r.valorpis = documento_obj.vr_pis_retido
                registro_r.codigoimpostopis = 0
                registro_r.variacaoimpostopis = 0
                registro_r.basecalculocofins = documento_obj.bc_cofins_proprio
                registro_r.aliqcofins = documento_obj.al_cofins_retido
                registro_r.valorcofins = documento_obj.vr_cofins_retido
                registro_r.codigoimpostocofins = 0
                registro_r.variacaoimpostocofins = 0

                if documento_obj.vr_csll:
                    registro_r.basecalculocsll = D(documento_obj.vr_operacao or 0).quantize(D('0.01'))
                    registro_r.aliqcsll = documento_obj.al_csll
                    registro_r.valorcsll = documento_obj.vr_csll
                else:
                    registro_r.basecalculocsll = 0
                    registro_r.aliqcsll = 0
                    registro_r.valorcsll = 0

                registro_r.codigoimpostocsll = 0
                registro_r.variacaoimpostocsll = 0
                #registro_r.dataprevpiscofinscsll = ''
                #registro_r.datapgtopiscofinscsll = ''
                registro_r.conciliada = ''
                #registro_r.dataprevissqn = ''
                #registro_r.datapgtoissqn = ''

                arquivo_text += registro_r.registro_R()


        cnpj = limpa_formatacao(export_obj.company_id.partner_id.cnpj_cpf)
        nome_arquivo =  cnpj + '_' + str(hoje()) + u'.txt'

        print(arquivo_text)
        dados = {
            'nome': nome_arquivo,
            'arquivo_texto': arquivo_text,
            'arquivo': base64.encodestring(arquivo_text),
        }
        export_obj.write(dados)


questor_fiscal()
