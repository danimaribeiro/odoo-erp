# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from fields import *
import trata_nfe
import trata_nfse
import datetime
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, primeiro_dia_mes, ultimo_dia_mes, formata_data
from pybrasil.inscricao import formata_cnpj
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
import random
from copy import copy
import base64


STORE_CUSTO = {
    'sped.documentoitem': (
        lambda docitem_pool, cr, uid, ids, context={}: [item_obj.documento_id.id for item_obj in docitem_pool.browse(cr, uid, ids)],
        ['vr_produtos', 'vr_frete', 'vr_seguro', 'vr_outras', 'vr_desconto', 'vr_ipi',
         'vr_icms_st', 'vr_ii', 'credita_icms_proprio', 'cfop_id', 'credita_icms_st',
         'credita_ipi', 'credita_pis_cofins', 'quantidade', 'fator_quantidade', 'vr_custo', 'vr_custo_estoque',
         'vr_diferencial_aliquota', 'vr_diferencial_aliquota_st', 'vr_simples',
         'credita_icms_proprio', 'credita_icms_st', 'credita_ipi', 'credita_pis_cofins'],
        10  #  Prioridade
    ),
    'sped.documento': (
        lambda doc_pool, cr, uid, ids, context={}: doc_pool.pool.get('sped.documentoitem').search(cr, uid, [['documento_id', 'in', ids]]),
        ['vr_frete_rateio', 'vr_seguro_rateio', 'vr_desconto_rateio',
         'vr_outras_rateio', 'write_date'],
        20  #  Prioridade
    )
}

GRAVA_RELATED = True
GRAVA_PROCESSADOS = True


class sped_documento(osv.Model):
    _description = 'Documentos SPED'
    _name = 'sped.documento'
    _inherit = 'mail.thread'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            txt = TIPO_EMISSAO_DICT[registro.emissao]

            if registro.emissao == TIPO_EMISSAO_PROPRIA:
                txt += ' - ' + ENTRADA_SAIDA_DICT[registro.entrada_saida]

            txt += ' - ' + registro.modelo
            txt += ' - ' + (registro.serie or '')
            txt += ' - ' + unicode(registro.numero)
            txt += ' - ' + parse_datetime(registro.data_emissao_brasilia).strftime('%d/%m/%Y')
            txt += ' - ' + registro.partner_id.razao_social
            txt += ' - ' + registro.partner_id.cnpj_cpf

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        try:
            numero = int(texto)
        except:
            numero = None

        if numero:
            procura = [('numero', '=', texto)]
        else:
            procura = ['|',
                       ('partner_razao_social', 'ilike', texto),
                       ('partner_cnpj_cpf', 'ilike', texto)]

        return procura

    def _get_modelo_padrao(self, cr, uid, context=None):
        if context is None:
            context = {}

        if context and context.get('modelo', MODELO_FISCAL_NFE):
            return context.get('modelo', MODELO_FISCAL_NFE)
        else:
            return MODELO_FISCAL_NFE

    def _get_emissao_padrao(self, cr, uid, context=None):
        if context is None:
            context = {}

        if context and context.get('emissao', TIPO_EMISSAO_PROPRIA):
            return context.get('emissao', TIPO_EMISSAO_PROPRIA)
        else:
            return TIPO_EMISSAO_PROPRIA

    def _get_entrada_saida_padrao(self, cr, uid, context=None):
        if context is None:
            context = {}

        if context and context.get('entrada_saida', ENTRADA_SAIDA_SAIDA):
            return context.get('entrada_saida', ENTRADA_SAIDA_SAIDA)
        else:
            return ENTRADA_SAIDA_SAIDA

    def _get_company_id_padrao(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
        return company_id

    def _get_regime_tributario_padrao(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
        company_obj = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        if company_obj.matriz_id:
            return company_obj.matriz_id.regime_tributario or REGIME_TRIBUTARIO_SIMPLES
        else:
            return company_obj.regime_tributario or REGIME_TRIBUTARIO_SIMPLES

    def _get_ambiente_nfe_padrao(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
        company_obj = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        modelo = self._get_modelo_padrao(cr, uid, context)

        if modelo == '55':
            if company_obj.matriz_id:
                return company_obj.matriz_id.ambiente_nfe or AMBIENTE_NFE_HOMOLOGACAO
            else:
                return company_obj.ambiente_nfe or AMBIENTE_NFE_HOMOLOGACAO
        elif modelo == 'SE':
            if company_obj.matriz_id:
                return company_obj.matriz_id.ambiente_nfse or AMBIENTE_NFE_HOMOLOGACAO
            else:
                return company_obj.ambiente_nfse or AMBIENTE_NFE_HOMOLOGACAO

    def _get_tipo_emissao_nfe_padrao(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
        company_obj = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        if company_obj.matriz_id:
            return company_obj.matriz_id.tipo_emissao_nfe or TIPO_EMISSAO_NFE_NORMAL
        else:
            return company_obj.tipo_emissao_nfe or TIPO_EMISSAO_NFE_NORMAL

    def _get_serie_padrao(self, cr, uid, context):
        ambiente_nfe = self._get_ambiente_nfe_padrao(cr, uid, context)
        tipo_emissao_nfe = self._get_tipo_emissao_nfe_padrao(cr, uid, context)
        modelo = self._get_modelo_padrao(cr, uid, context)
        company_id = context.get('company_id') or self._get_company_id_padrao(cr, uid, context)
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if modelo == '55':
            if ambiente_nfe == AMBIENTE_NFE_HOMOLOGACAO:
                if tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
                    if company_obj.matriz_id:
                        return company_obj.matriz_id.serie_homologacao or '100'
                    else:
                        return company_obj.serie_homologacao or '100'
                else:
                    if company_obj.matriz_id:
                        return company_obj.matriz_id.serie_scan_homologacao or '100'
                    else:
                        return company_obj.serie_scan_homologacao or '999'
            else:
                if tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
                    if company_obj.matriz_id:
                        return company_obj.matriz_id.serie_producao or '1'
                    else:
                        return company_obj.serie_producao or '1'
                else:
                    if company_obj.matriz_id:
                        return company_obj.matriz_id.serie_scan_producao or '900'
                    else:
                        return company_obj.serie_scan_producao or '900'
        elif modelo == 'SE':
            if company_obj.matriz_id:
                return company_obj.matriz_id.serie_nfse or '1'
            else:
                return company_obj.serie_nfse or '1'
        elif modelo == 'RL':
            return '1'
        elif modelo == '2D':
            return '01'

    def _get_serie_rps_padrao(self, cr, uid, context):
        modelo = self._get_modelo_padrao(cr, uid, context)
        company_id = context.get('company_id') or self._get_company_id_padrao(cr, uid, context)
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if modelo == 'SE':
            if company_obj.matriz_id:
                return company_obj.matriz_id.serie_rps or '1'
            else:
                return company_obj.serie_rps or '1'

    def _get_numero_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        emissao = context.get('emissao', TIPO_EMISSAO_PROPRIA)
        company_id = context.get('company_id') or self._get_company_id_padrao(cr, uid, context)
        company_obj = self.pool.get('res.company').browse(cr, 1, company_id)
        modelo = context.get('modelo', MODELO_FISCAL_NFE)
        serie = context.get('serie') or self._get_serie_padrao(cr, uid, context)
        ambiente_nfe = context.get('ambiente_nfe') or self._get_ambiente_nfe_padrao(cr, uid, context)

        if emissao != TIPO_EMISSAO_PROPRIA:
            return 0

        if modelo == '55':
            lista_ultimo_numero = self.search(
                cr,
                uid,
                args=[
                    ('company_cnpj_cpf', '=', company_obj.partner_id.cnpj_cpf),
                    ('ambiente_nfe', '=', ambiente_nfe),
                    ('emissao', '=', emissao),
                    ('modelo', '=', modelo),
                    ('serie', '=', serie),
                ],
                limit=1,
                order='numero DESC'
            )

            if lista_ultimo_numero:
                ultimo_numero = self.browse(cr, uid, lista_ultimo_numero, context)[0]
                return ultimo_numero.numero + 1
            else:
                return 1

        elif modelo == 'SE':
            return -1

        elif modelo == 'RL':
            lista_ultimo_numero = self.search(
                cr,
                uid,
                args=[
                    ('company_cnpj_cpf', '=', company_obj.partner_id.cnpj_cpf),
                    ('emissao', '=', emissao),
                    ('modelo', '=', modelo),
                ],
                limit=1,
                order='numero DESC'
            )

            if lista_ultimo_numero:
                ultimo_numero = self.browse(cr, uid, lista_ultimo_numero[0], context)
                ultimo_numero = ultimo_numero.numero
            else:
                ultimo_numero = 0

            return ultimo_numero + 1

    def _get_rps_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        emissao = context.get('emissao', TIPO_EMISSAO_PROPRIA)
        company_id = context.get('company_id') or self._get_company_id_padrao(cr, uid, context)
        company_obj = self.pool.get('res.company').browse(cr, 1, company_id)
        modelo = context.get('modelo', MODELO_FISCAL_NFE)
        #serie = context.get('serie_rps') or self._get_serie_padrao(cr, uid, context)
        ambiente_nfe = context.get('ambiente_nfe') or self._get_ambiente_nfe_padrao(cr, uid, context)

        if emissao != TIPO_EMISSAO_PROPRIA or 'temporario' in context:
            return 0

        if modelo == 'SE':
            #company = self.pool.get('res.company').browse(cr, uid, company_id)
            #self.pool.get('res.company').write(cr, 1, company_id, {'ultimo_rps': company.ultimo_rps + 1})
            #return company.ultimo_rps + 1
            lista_ultimo_numero = self.search(
                cr,
                uid,
                args=[
                    ('company_cnpj_cpf', '=', company_obj.partner_id.cnpj_cpf),
                    ('ambiente_nfe', '=', ambiente_nfe),
                    ('emissao', '=', emissao),
                    ('modelo', '=', modelo),
                    #('serie', '=', serie),
                ],
                limit=1,
                order='numero_rps DESC'
            )

            if lista_ultimo_numero:
                ultimo_numero = self.browse(cr, uid, lista_ultimo_numero, context)[0]
                return ultimo_numero.numero_rps + 1
            else:
                return 1

    def action_enviar(self, cr, uid, ids, context=None):
        for registro_nfe in self.browse(cr, uid, ids, context={'lang': 'pt_BR'}):
            #
            # Verifica se há outro número igual a esta NF com outro id, antes
            # de enviar para a SEFAZ
            #
            busca = [
                ['company_cnpj_cpf', '=', registro_nfe.company_id.partner_id.cnpj_cpf],
                ['emissao', '=', '0'],
                ['modelo', '=', registro_nfe.modelo or '55'],
                ['serie', '=', registro_nfe.serie or ''],
                ['ambiente_nfe', '=', registro_nfe.ambiente_nfe or '2'],
                ['numero', '=', registro_nfe.numero or -1],
                ['id', '!=', registro_nfe.id],
            ]

            lista_numero = self.search(cr, 1, busca)

            if len(lista_numero) != 0:
                raise osv.except_osv(u'Erro!', u'O número dessa nota já existe no sistema, vinculado a outro documento!')

            trata_nfe.envia_nfe(self, cr, uid, registro_nfe)

        return True

    def action_inutilizar(self, cr, uid, ids, context=None):
        for registro_nfe in self.browse(cr, uid, ids, context={'lang': 'pt_BR'}):
            trata_nfe.inutiliza_numeracao(self, cr, uid, registro_nfe)

        return True

    #def action_consultar(self, cr, uid, ids, context=None):
        #return self.write(cr, uid, ids, {'state': 'autorizada'}, context=context)

    def action_cancelar(self, cr, uid, ids, context=None):
        for registro_nfe in self.browse(cr, uid, ids, context={'lang': 'pt_BR'}):
            if registro_nfe.emissao != '0':
                raise osv.except_osv(u'Erro!', u'Proibido cancelar notas de terceiros!')
            #
            # Não cancela se passou de 24 horas da autorização
            #
            tempo = parse_datetime(fields.datetime.now()) - parse_datetime(registro_nfe.data_autorizacao or registro_nfe.data_emissao)
            horas = D((tempo.days * 86400) + tempo.seconds) / D(60) / D(60)
            print(tempo.days, tempo.seconds, horas)
            if horas >= 24:
                raise osv.except_osv(u'Erro!', u'Proibido cancelar após 24 horas da autorização!')

            if not registro_nfe.motivo_cancelamento or len(registro_nfe.motivo_cancelamento) < 15:
                raise osv.except_osv(u'Erro!', u'O motivo do cancelamento deve ter pelo menos 15 caracteres!')

            trata_nfe.cancela_nfe(self, cr, uid, registro_nfe)
            # novo_state = nfe.envia_nfe(cr, uid, registro_nfe)
        #return self.write(cr, uid, ids, {'state': 'cancelada'}, context=context)
        return True

    def action_rejeitar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'rejeitada'}, context=context)

    def action_gera_danfe(self, cr, uid, ids, context=None):
        for registro_nfe in self.browse(cr, uid, ids):
            if registro_nfe.modelo == '55':
                trata_nfe.gera_danfe(self, cr, uid, registro_nfe)
            elif registro_nfe.modelo == 'SE':
                trata_nfse.grava_pdf(self, cr, uid, registro_nfe)

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            al_simples = D('0')

            for item_obj in doc_obj.documentoitem_ids:
                #
                # Para o custo da mercadoria para baixa do custo na venda/devolução
                #
                if nome_campo == 'vr_custo_estoque':
                    if item_obj.cfop_id.codigo in CFOPS_CUSTO_ESTOQUE_VENDA_DEVOLUCAO:
                        soma += D(str(getattr(item_obj, nome_campo, 0)))

                #
                # Para o SIMPLES Nacional, somar o valor da operação
                #
                elif nome_campo == 'vr_simples':
                    if D(str(getattr(item_obj, 'vr_simples', 0))):
                        if al_simples == 0:
                            al_simples = D(str(getattr(item_obj, 'al_simples', 0)))

                        soma += D(str(getattr(item_obj, 'vr_operacao', 0)))
                else:
                    soma += D(str(getattr(item_obj, nome_campo, 0)))

            soma = soma.quantize(D('0.01'))

            if nome_campo == 'vr_fatura' and doc_obj.deduz_retencao:
                soma -= D(str(doc_obj.vr_pis_retido))
                soma -= D(str(doc_obj.vr_cofins_retido))
                soma -= D(str(doc_obj.vr_csll))
                soma -= D(str(doc_obj.vr_irrf))
                soma -= D(str(doc_obj.vr_previdencia))
                soma -= D(str(doc_obj.vr_iss_retido))

            if (nome_campo == 'bc_previdencia' or nome_campo == 'vr_previdencia') and doc_obj.deduz_retencao:
                if soma < D('10'):
                    soma = D('0')

            if nome_campo == 'vr_simples' and soma > 0:
                soma *= al_simples / D(100)
                soma = soma.quantize(D('0.01'))

            res[doc_obj.id] = soma

        return res

    def _get_itens_originais_processados(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            itens_originais = 0
            itens_originais_processados = 0
            for item_obj in doc_obj.documentoitem_ids:
                if item_obj.produto_codigo != False:
                    itens_originais += 1

                    if item_obj.produto_id and item_obj.cfop_id:
                        itens_originais_processados += 1

            if nome_campo == 'itens_originais':
                res[doc_obj.id] = itens_originais
            elif nome_campo == 'itens_originais_a_processar':
                res[doc_obj.id] = itens_originais - itens_originais_processados
            elif nome_campo == 'itens_originais_processados':
                res[doc_obj.id] = itens_originais == itens_originais_processados

        return res

    def _get_hora_brasilia(self, cr, uid, ids, nome_campo, args, context={}):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            data_emissao = data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao))
            data_entrada_saida = data_hora_horario_brasilia(parse_datetime(doc_obj.data_entrada_saida))

            if nome_campo == 'data_emissao_brasilia':
                if data_emissao:
                    res[doc_obj.id] = data_emissao.strftime('%Y-%m-%d')
                else:
                    res[doc_obj.id] = data_emissao
            elif nome_campo == 'hora_emissao_brasilia':
                if data_emissao:
                    res[doc_obj.id] = data_emissao.strftime('%H:%M:%S')
                else:
                    res[doc_obj.id] = data_emissao
            elif nome_campo == 'data_entrada_saida_brasilia':
                if data_entrada_saida:
                    res[doc_obj.id] = data_entrada_saida.strftime('%Y-%m-%d')
                else:
                    res[doc_obj.id] = data_entrada_saida
            elif nome_campo == 'hora_entrada_saida_brasilia':
                if data_entrada_saida:
                    res[doc_obj.id] = data_entrada_saida.strftime('%H:%M:%S')
                else:
                    res[doc_obj.id] = data_entrada_saida

        return res

    _columns = {
        #
        # Empresa emissora ou recebedora do documento
        #
        'company_id_readonly': fields.many2one('res.company', u'Empresa', select=True),
        'company_id': fields.many2one('res.company', u'Empresa', select=True),
        'company_cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'CNJP/CPF da empresa'),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', relation='res.company', string=u'Empresa mãe', store=GRAVA_RELATED, select=True),
        'company_partner_id': fields.related('company_id', 'partner_id', type='many2one', string=u'Empresa', relation='res.partner', store=GRAVA_RELATED),
        'simples_anexo': fields.related('company_id', 'simples_anexo', type='char', string=u'Anexo do SIMPLES Nacional'),
        'simples_teto': fields.related('company_id', 'simples_teto', type='char', string=u'Faixa de faturamento'),

        'descricao': fields.function(_descricao, string='Documento', method=True, type='char', fnct_search=_procura_descricao),
        'state': fields.selection(SITUACAO_NFE, string='Situação NF-e', select=True),

        #
        # Cabeçalho do documento
        #
        'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão', select=True),
        'modelo': fields.selection(MODELO_FISCAL, u'Modelo', select=True),
        'serie': fields.char(u'Série', size=3, select=True),
        'subserie': fields.char(u'Subsérie', size=4, select=True),        
        'numero': fields.integer(u'Número', select=True),
        'numero_prefeitura': fields.float(u'Número Prefeitura', digits=(18,0), select=True),
        'situacao': fields.selection(SITUACAO_FISCAL, u'Situação fiscal', select=True),
        'entrada_saida': fields.selection(ENTRADA_SAIDA, u'Entrada/saída', select=True),
        #'data_emissao': fields.date(u'Data de emissão'),
        'data_emissao': fields.datetime(u'Data de emissão', select=True),
        'data_entrada_saida': fields.datetime(u'Data de entrada/saída', select=True),
        'data_autorizacao': fields.datetime(u'Data de autorização'),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário', select=True),
        'ambiente_nfe': fields.selection(AMBIENTE_NFE, u'Ambiente da NF-e', select=True),
        'tipo_emissao_nfe': fields.selection(TIPO_EMISSAO_NFE, u'Tipo de emissão da NF-e'),
        'finalidade_nfe': fields.selection(FINALIDADE_NFE, u'Finalidade da NF-e'),
        'forma_pagamento': fields.selection(FORMA_PAGAMENTO, u'Forma de pagamento'),
        'processo_emissao_nfe': fields.selection(PROCESSO_EMISSAO_NFE, u'Processo de emissão'),
        'ie_st': fields.char(u'IE do substituto tributário', size=14),
        'municipio_fato_gerador_id': fields.many2one('sped.municipio', u'Município do fato gerador', select=True),

        'operacao_id': fields.many2one('sped.operacao', u'Operação fiscal', ondelete='restrict', select=True),
        'naturezaoperacao_id': fields.many2one('sped.naturezaoperacao', u'Natureza da operação'),

        'partner_id': fields.many2one('res.partner', string=u'Destinatário/Remetente', select=True, ondelete='restrict', required=True, domain="[('cnpj_cpf', '!=', False)]"),

        #
        # Dados do cliente/fornecedor
        #
        'partner_contribuinte': fields.related('partner_id', 'contribuinte', type='char', string=u'Contribuinte'),
        'partner_cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', string=u'CNJP/CPF'),
        'partner_razao_social': fields.related('partner_id', 'razao_social', type='char', string=u'Razão Social/Nome'),
        'partner_fantasia': fields.related('partner_id', 'fantasia', type='char', string=u'Fantasia'),
        'partner_endereco': fields.related('partner_id', 'endereco', type='char', string=u'Endereço'),
        'partner_numero': fields.related('partner_id', 'numero', type='char', string=u'nº'),
        'partner_complemento': fields.related('partner_id', 'complemento', type='char', string=u'complemento'),
        'partner_bairro': fields.related('partner_id', 'bairro', type='char', string=u'Bairro'),
        'partner_municipio_id': fields.related('partner_id', 'municipio_id', type='many2one', relation='sped.municipio', string=u'Município'),
        'partner_cep': fields.related('partner_id', 'cep', type='char', string=u'CEP'),
        'partner_ie': fields.related('partner_id', 'ie', type='char', string=u'Inscrição estadual'),
        'partner_im': fields.related('partner_id', 'im', type='char', string=u'Inscrição municipal'),
        'partner_eh_orgao_publico': fields.related('partner_id', 'eh_orgao_publico', type='boolean', string=u'É órgão público?'),

        # 'endereco_entrega': fields.many2one(),
        # 'endereco_retirada': fields.many2one(),

        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'duplicata_ids': fields.one2many('sped.documentoduplicata', 'documento_id', u'Vencimentos'),

        # 'endereco_cobranca': fields.many2one(),

        #
        # Totais dos itens
        #

        # Valor total dos produtos
        #'vr_produtos': CampoDinheiro(u'Valor dos produtos'),
        'vr_produtos': fields.function(_get_soma_funcao, type='float', string=u'Valor dos produtos/serviços', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_produtos_tributacao': CampoDinheiro(u'Valor dos produtos para tributação'),
        'vr_produtos_tributacao': fields.function(_get_soma_funcao, type='float', string=u'Valor dos produtos para tributação', store=GRAVA_RELATED, digits=(18, 2)),

        # Outros valores acessórios
        #'vr_frete': CampoDinheiro(u'Valor do frete'),
        'vr_frete': fields.function(_get_soma_funcao, type='float', string=u'Valor do frete', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_seguro': CampoDinheiro(u'Valor do seguro'),
        'vr_seguro': fields.function(_get_soma_funcao, type='float', string=u'Valor do seguro', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_desconto': CampoDinheiro(u'Valor do desconto'),
        'vr_desconto': fields.function(_get_soma_funcao, type='float', string=u'Valor do desconto', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_outras': CampoDinheiro(u'Outras despesas acessórias'),
        'vr_outras': fields.function(_get_soma_funcao, type='float', string=u'Outras despesas acessórias', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_operacao': CampoDinheiro(u'Valor da operação'),
        'vr_operacao': fields.function(_get_soma_funcao, type='float', string=u'Valor da operação', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_operacao_tributacao': CampoDinheiro(u'Valor da operação para tributação'),
        'vr_operacao_tributacao': fields.function(_get_soma_funcao, type='float', string=u'Valor da operação para tributação', store=GRAVA_RELATED, digits=(18, 2)),

        # ICMS próprio
        #'bc_icms_proprio': CampoDinheiro(u'Base do ICMS próprio'),
        'bc_icms_proprio': fields.function(_get_soma_funcao, type='float', string=u'Base do ICMS próprio', store=GRAVA_RELATED, digits=(18, 2)),
        #'vr_icms_proprio': CampoDinheiro(u'Valor do ICMS próprio'),
        #'al_icms_sem_item': fields.selection((('25', '25%'), ('18', '18%'), ('12', '12%'), ('7', '7%')), u'Alíquota'),
        'vr_icms_proprio': fields.function(_get_soma_funcao, type='float', string=u'Valor do ICMS próprio', store=GRAVA_RELATED, digits=(18, 2)),
        # ICMS SIMPLES
        #'vr_icms_sn': CampoDinheiro(u'Valor do crédito de ICMS - SIMPLES Nacional'),
        'vr_icms_sn': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do crédito de ICMS - SIMPLES Nacional'),
        'vr_simples': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do SIMPLES Nacional'),
        # ICMS ST
        #'bc_icms_st': CampoDinheiro(u'Base do ICMS ST'),
        'bc_icms_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do ICMS ST'),
        #'vr_icms_st': CampoDinheiro(u'Valor do ICMS ST'),
        'vr_icms_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do ICMS ST'),
        # ICMS ST retido
        #'bc_icms_st_retido': CampoDinheiro(u'Base do ICMS retido anteriormente por substituição tributária'),
        'bc_icms_st_retido': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do ICMS retido anteriormente por substituição tributária'),
        #'vr_icms_st_retido': CampoDinheiro(u'Valor do ICMS retido anteriormente por substituição tributária'),
        'vr_icms_st_retido': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do ICMS retido anteriormente por substituição tributária'),

        # IPI
        #'bc_ipi': CampoDinheiro(u'Base do IPI'),
        'bc_ipi': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do IPI'),
        #'vr_ipi': CampoDinheiro(u'Valor do IPI'),
        'vr_ipi': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do IPI'),

        # Imposto de importação
        #'bc_ii': CampoDinheiro(u'Base do imposto de importação'),
        'bc_ii': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do imposto de importação'),
        #'vr_ii': CampoDinheiro(u'Valor do imposto de importação'),
        'vr_ii': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do imposto de importação'),

        # PIS e COFINS
        #'bc_pis_proprio': CampoDinheiro(u'Base do PIS próprio'),
        'bc_pis_proprio': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do PIS próprio'),
        #'vr_pis_proprio': CampoDinheiro(u'Valor do PIS próprio'),
        'vr_pis_proprio': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do PIS próprio'),
        #'bc_cofins_proprio': CampoDinheiro(u'Base da COFINS própria'),
        'bc_cofins_proprio': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base da COFINS própria'),
        #'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS própria'),
        'vr_cofins_proprio': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do COFINS própria'),
        #'bc_pis_st': CampoDinheiro(u'Base do PIS ST'),
        'bc_pis_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do PIS ST'),
        #'vr_pis_st': CampoDinheiro(u'Valor do PIS ST'),
        'vr_pis_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do PIS ST'),
        #'bc_cofins_st': CampoDinheiro(u'Base da COFINS ST'),
        'bc_cofins_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base da COFINS ST'),
        #'vr_cofins_st': CampoDinheiro(u'Valor do COFINS ST'),
        'vr_cofins_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do COFINS ST'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        #'vr_servicos': CampoDinheiro(u'Valor dos serviços'),
        'vr_servicos': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor dos serviços'),

        # ISS
        #'bc_iss': CampoDinheiro(u'Base do ISS'),
        'bc_iss': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do ISS'),
        #'vr_iss': CampoDinheiro(u'Valor do ISS'),
        'vr_iss': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do ISS'),

        # PIS e COFINS
        #'vr_pis_servico': CampoDinheiro(u'PIS sobre serviços'),
        'vr_pis_servico': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'PIS sobre serviços'),
        #'vr_cofins_servico': CampoDinheiro(u'COFINS sobre serviços'),
        'vr_cofins_servico': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'COFINS sobre serviços'),

        #
        # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
        #
        #'vr_operacao_pis_cofins_csll': CampoDinheiro(u'Base da retenção do PIS-COFINS e CSLL'),

        # PIS e COFINS
        'pis_cofins_retido': fields.boolean(u'PIS-COFINS retidos?'),
        'al_pis_retido': CampoPorcentagem(u'Alíquota do PIS retido'),
        'vr_pis_retido': CampoDinheiro(u'PIS retido'),
        'al_cofins_retido': CampoPorcentagem(u'Alíquota da COFINS retida'),
        'vr_cofins_retido': CampoDinheiro(u'COFINS retida'),

        # Contribuição social sobre lucro líquido
        'csll_retido': fields.boolean(u'CSLL retida?'),
        'al_csll': CampoPorcentagem('Alíquota da CSLL'),
        'vr_csll': CampoDinheiro(u'CSLL retida'),
        'bc_csll_propria': CampoDinheiro(u'Base da CSLL própria'),
        'al_csll_propria': CampoPorcentagem('Alíquota da CSLL própria'),
        'vr_csll_propria': CampoDinheiro(u'CSLL própria'),

        # IRRF
        'irrf_retido': fields.boolean(u'IR retido?'),
        'bc_irrf': CampoDinheiro(u'Base do IRRF'),
        'al_irrf': CampoPorcentagem(u'Alíquota do IRRF'),
        'vr_irrf': CampoDinheiro(u'Valor do IRRF'),
        'bc_irpj_proprio': CampoDinheiro(u'Valor do IRPJ próprio'),
        'al_irpj_proprio': CampoPorcentagem(u'Alíquota do IRPJ próprio'),
        'vr_irpj_proprio': CampoDinheiro(u'Valor do IRPJ próprio'),

        # Previdência social
        'previdencia_retido': fields.boolean(u'INSS retido?'),
        'bc_previdencia': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do INSS'),
        'al_previdencia': CampoPorcentagem(u'Alíquota do INSS'),
        'vr_previdencia': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do INSS'),

        # ISS
        'iss_retido': fields.boolean(u'ISS retido?'),
        'bc_iss_retido': CampoDinheiro(u'Base do ISS'),
        'vr_iss_retido': CampoDinheiro(u'Valor do ISS'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        #'vr_nf': CampoDinheiro(u'Valor total da NF'),
        'vr_nf': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor total da NF'),
        #'vr_fatura': CampoDinheiro(u'valor total da fatura'),
        'vr_fatura': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor total da fatura'),

        'vr_ibpt': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor IBPT'),

        #
        # Transporte e frete
        #
        'modalidade_frete': fields.selection(MODALIDADE_FRETE, u'Modalidade do frete'),
        'transportadora_id': fields.many2one('res.partner', u'Transportadora', domain=[('cnpj_cpf', '!=', False)]),
        'veiculo_id': fields.many2one('sped.veiculo', u'Veículo'),
        'reboque1_id': fields.many2one('sped.veiculo', u'1º reboque'),
        'reboque2_id': fields.many2one('sped.veiculo', u'2º reboque'),
        'reboque3_id': fields.many2one('sped.veiculo', u'3º reboque'),
        'reboque4_id': fields.many2one('sped.veiculo', u'4º reboque'),
        'reboque5_id': fields.many2one('sped.veiculo', u'5º reboque'),
        'volume_ids': fields.one2many('sped.documentovolume', 'documento_id', u'Volumes'),
        'cce_ids': fields.one2many('sped.documentocce', 'documento_id', u'Cartas de correção'),


        # Impostos retidos sobre o transporte
        'vr_servico_frete': CampoDinheiro(u'Valor do serviço do frete'),
        'bc_icms_frete': CampoDinheiro(u'Base do ICMS retido sobre o frete'),
        'al_icms_frete': CampoPorcentagem(u'Alíquota do ICMS retido sobre o frete'),
        'vr_icms_frete': CampoDinheiro(u'Valor do ICMS retido sobre o frete'),
        'cfop_frete_id': fields.many2one('sped.cfop', u'CFOP do frete'),
        'municipio_frete_id': fields.many2one('sped.municipio', u'Município de ocorrência do frete'),

        # Informações adicionais
        'infadfisco': fields.text(u'Informações adicionais de interesse do fisco'),
        'infcomplementar': fields.text(u'Informações complementares'),

        # Exportação
        'exportacao_estado_embarque_id': fields.many2one('sped.estado', u'Estado do embarque'),
        'exportacao_local_embarque': fields.char(u'Local do embarque', size=60),

        # Compras públicas

        'compra_nota_empenho': fields.char(u'Identificação da nota de empenho (compra pública)', size=17),
        'compra_pedido': fields.char(u'Pedido (compra pública)', size=60),
        'compra_contrato': fields.char(u'Contrato (compra pública)', size=60),

        #
        # Chave de acesso em documentos eletrônicos
        #
        'chave': fields.char(u'Chave NF-e/CT-e', size=44, select=True),

        #
        # Valores originais em documentos de entrada
        #
        'natureza_operacao_original': fields.char(u'Natureza da operação original', size=60),
        'itens_originais': fields.function(_get_itens_originais_processados, method=True, type='integer', string=u'Itens originais', store=GRAVA_PROCESSADOS, select=True),
        'itens_originais_a_processar': fields.function(_get_itens_originais_processados, method=True, type='integer', string=u'Itens originais a processar', store=GRAVA_PROCESSADOS, select=True),
        'itens_originais_processados': fields.function(_get_itens_originais_processados, method=True, type='boolean', string=u'Itens originais processados', store=GRAVA_PROCESSADOS, select=True),
        #'itens_originais_processados': fields.boolean(u'Itens originais processados?'),
        'mercadoria_recebida': fields.boolean(u'Mercadoria recebida?'),

        #
        # Valores obrigatórios em contas de água, gás, telefonia etc.
        #
        'classe_consumo_agua': fields.selection(CLASSE_CONSUMO_AGUA, u'Classe de consumo de água'),
        'classe_consumo_gas': fields.selection(CLASSE_CONSUMO_GAS, u'Classe de consumo de gás'),
        'classe_consumo_energia': fields.selection(CLASSE_CONSUMO_ENERGIA, u'Classe de consumo de energia elétrica'),
        'tipo_ligacao_energia': fields.selection(TIPO_LIGACAO_ENERGIA, u'Tipo da ligação de energia elétrica'),
        'grupo_tensao_energia': fields.selection(GRUPO_TENSAO_ENERGIA, u'Grupo de tensão de energia elétrica'),
        'tipo_assinante': fields.selection(TIPO_ASSINANTE, u'Tipo de assinante'),

        'documentoitem_ids': fields.one2many('sped.documentoitem', 'documento_id', u'Ítens do documento'),
        'documentoitem_servico_ids': fields.one2many('sped.documentoitem', 'documento_id', u'Ítens do documento'),
        'documentoitem_simples_ids': fields.one2many('sped.documentoitem', 'documento_id', u'Ítens do documento'),
        'documentoreferenciado_ids': fields.one2many('sped.documentoreferenciado', 'documento_id', u'Ítens do documento'),

        'dados_originais': fields.text('Dados originais da NF - formato json'),

        #
        # Nota de serviço
        #
        'cnae_id': fields.many2one('sped.cnae', u'CNAE'),
        'natureza_tributacao_nfse': fields.selection(NATUREZA_TRIBUTACAO_NFSE, u'Natureza da tributação'),
        'servico_id': fields.many2one('sped.servico', u'Serviço'),
        'numero_rps': fields.integer(u'RPS', select=True),
        'serie_rps': fields.char(u'Série RPS', size=3, select=True),
        'data_emissao_rps': fields.datetime(u'Data de emissão do RPS', select=True),
        'numero_lote_rps': fields.integer(u'Lote RPS', select=True),
        'numero_protocolo_nfse': fields.char(u'Protocolo', size=60, select=True),
        'codigo_verificacao_nfse': fields.char(u'Código de verificação', size=30, select=True),
        'descricao_servico': fields.text(u'Descrição do serviço'),
        'link_verificacao_nfse': fields.text(u'Link para verificação'),
        'limite_retencao_pis_cofins_csll': CampoDinheiro(u'Obedecer limite de faturamento para retenção de'),
        'data_cancelamento': fields.datetime(u'Data de cancelamento', select=True),
        'motivo_cancelamento': fields.char(u'Motivo do cancelamento', size=60),

        'nota_substituida_id': fields.many2one('sped.documento', u'Nota substituída'),

        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'sped.documento')], ondelete="cascade"),

        'resposta_nfse': fields.text(u'Erro na NFS-e'),

        #
        # Campos para rateio de custo
        #
        'vr_frete_rateio': CampoDinheiro(u'Valor do frete'),
        'vr_seguro_rateio': CampoDinheiro(u'Valor do seguro'),
        'vr_desconto_rateio': CampoDinheiro(u'Valor do desconto'),
        'vr_outras_rateio': CampoDinheiro(u'Outras despesas acessórias'),
        'vr_custo': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Valor de custo'),

        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
        'deduz_retencao': fields.boolean(u'Deduz retenção do total da NF?'),
        'irrf_retido_ignora_limite': fields.boolean(u'IR retido ignora limite de R$ 10,00?'),

        #
        # Funcoes para filtrar datas por periodo
        #
        'data_emissao_brasilia': fields.function(_get_hora_brasilia, type='date', string='Data de emissão', method=True, store=GRAVA_RELATED, select=True),
        #'hora_emissao_brasilia': fields.function(_get_hora_brasilia, type='float', string='Hora de emissão', method=True, store=GRAVA_RELATED, select=True),
        'data_entrada_saida_brasilia': fields.function(_get_hora_brasilia, type='date', string='Data de entrada/saída', method=True, store=GRAVA_RELATED, select=True),
        'data_emissao_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De emissão'),
        'data_emissao_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A emissão'),
        'data_entrada_saida_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De emissão'),
        'data_entrada_saida_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A emissão'),

        'forca_recalculo_st_compra': fields.boolean(u'Força recálculo do ST na compra?'),
        'bc_icms_st_compra': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Base do ICMS ST compra'),
        'vr_icms_st_compra': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do ICMS ST compra'),
        'calcula_diferencial_aliquota': fields.boolean(u'Calcula diferencial de alíquota?'),
        'vr_diferencial_aliquota': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do Diferencial de Alíquota ICMS próprio'),
        'vr_diferencial_aliquota_st': fields.function(_get_soma_funcao, type='float', store=GRAVA_RELATED, digits=(18, 2), string=u'Valor do Diferencial de Alíquota ICMS ST'),
        'company_provedor_nfse': fields.related('company_id', 'provedor_nfse', type='selection', selection=PROVEDOR_NFSE, string=u'Provedor'),
    }

    _defaults = {
        'irrf_retido_ignora_limite': False,
        #
        # Empresa emissora ou recebedora do documento
        #
        'company_id_readonly': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=c),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=c),
        'state': 'em_digitacao',
        'deduz_retencao': True,

        #
        # Cabeçalho do documento
        #
        'emissao': _get_emissao_padrao,
        'modelo': _get_modelo_padrao,
        'serie': _get_serie_padrao,
        'serie_rps': _get_serie_rps_padrao,
        'subserie': u'',
        'numero_rps': _get_rps_padrao,
        'numero': _get_numero_padrao,
        'situacao': SITUACAO_FISCAL_REGULAR,
        'entrada_saida': _get_entrada_saida_padrao,
        'data_emissao': lambda self, cr, uid, context={}: fields.datetime.now() if 'emissao' not in context or context['emissao'] == TIPO_EMISSAO_PROPRIA else False,
        'data_emissao_rps': fields.datetime.now,
        'data_entrada_saida': fields.datetime.now,
        # 'hora_entrada_saida': ,
        'regime_tributario': _get_regime_tributario_padrao,
        'ambiente_nfe': _get_ambiente_nfe_padrao,
        'tipo_emissao_nfe': _get_tipo_emissao_nfe_padrao,
        'finalidade_nfe': FINALIDADE_NFE_NORMAL,
        'forma_pagamento': FORMA_PAGAMENTO_A_VISTA,
        'processo_emissao_nfe': PROCESSO_EMISSAO_NFE_CONTRIBUINTE_PROPRIO,
        'ie_st': u'',
        #
        # Totais dos itens
        #

        # Valor total dos produtos
        'vr_produtos': D('0'),
        'vr_produtos_tributacao': D('0'),

        # Outros valores acessórios
        'vr_frete': D('0'),
        'vr_seguro': D('0'),
        'vr_desconto': D('0'),
        'vr_outras': D('0'),
        'vr_operacao': D('0'),
        'vr_operacao_tributacao': D('0'),

        # ICMS próprio
        'bc_icms_proprio': D('0'),
        'vr_icms_proprio': D('0'),
        # ICMS SIMPLES
        'vr_icms_sn': D('0'),
        # ICMS ST
        'bc_icms_st': D('0'),
        'vr_icms_st': D('0'),
        # ICMS ST retido
        'bc_icms_st_retido': D('0'),
        'vr_icms_st_retido': D('0'),

        # IPI
        'bc_ipi': D('0'),
        'vr_ipi': D('0'),

        # Imposto de importação
        'bc_ii': D('0'),
        'vr_ii': D('0'),

        # PIS e COFINS
        'bc_pis_proprio': D('0'),
        'vr_pis_proprio': D('0'),
        'bc_cofins_proprio': D('0'),
        'vr_cofins_proprio': D('0'),
        'bc_pis_st': D('0'),
        'vr_pis_st': D('0'),
        'bc_cofins_st': D('0'),
        'vr_cofins_st': D('0'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': D('0'),

        # ISS
        'bc_iss': D('0'),
        'vr_iss': D('0'),

        # PIS e COFINS
        'vr_pis_servico': D('0'),
        'vr_cofins_servico': D('0'),

        #
        # Retenções de tributos (órgãos públicos, substitutos tributários etc.)
        #
        #'vr_operacao_pis_cofins_csll': D('0'),

        # PIS e COFINS
        'pis_cofins_retido': False,
        'al_pis_retido': D('0'),
        'vr_pis_retido': D('0'),
        'al_cofins_retido': D('0'),
        'vr_cofins_retido': D('0'),

        # Contribuição social sobre lucro líquido
        'csll_retido': False,
        'al_csll': D('0'),
        'vr_csll': D('0'),

        # IRRF
        'irrf_retido': False,
        'bc_irrf': D('0'),
        'al_irrf': D('0'),
        'vr_irrf': D('0'),

        # Previdência social
        'previdencia_retido': False,
        'bc_previdencia': D('0'),
        'al_previdencia': D('0'),
        'vr_previdencia': D('0'),

        # ISS
        'iss_retido': False,
        'bc_iss_retido': D('0'),
        'vr_iss_retido': D('0'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': D('0'),
        'vr_fatura': D('0'),

        #
        # Transporte e frete
        #
        'modalidade_frete': MODALIDADE_FRETE_DESTINATARIO,

        # Impostos retidos sobre o transporte
        'vr_servico_frete': D('0'),
        'bc_icms_frete': D('0'),
        'al_icms_frete': D('0'),
        'vr_icms_frete': D('0'),
        # 'cfop_frete': models.ForeignKey('tabela.CFOP', verbose_name=_(u'CFOP do frete'), blank=True, null=True)
        # 'municipio_frete': fields.many2one('sped.municipio', u'Município de ocorrência do frete'),

        # Informações adicionais
        'infadfisco': u'',
        'infcomplementar': u'',

        # Exportação
        # 'exportacao_estado_embarque_id': fields.many2one('sped.estado', u'Estado do embarque'),
        'exportacao_local_embarque': u'',

        # Compras públicas
        'compra_nota_empenho': u'',
        'compra_pedido': u'',
        'compra_contrato': u'',

        #
        # Chave de acesso em documentos eletrônicos
        #
        'chave': u'',

        #
        # Valores originais em documentos de entrada
        #
        'natureza_operacao_original': u'',
        'itens_originais_processados': False,
        'mercadoria_recebida': False,

        #
        # Valores obrigatórios em contas de água, gás, telefonia etc.
        #
        'classe_consumo_gas': u'',
        'classe_consumo_agua': u'',
        'classe_consumo_energia': u'',
        'tipo_ligacao_energia': u'',
        'grupo_tensao_energia': u'',

        'dados_originais': '',

        #
        # Nota de serviço
        #
        'cnae_id': False,
        'natureza_tributacao_nfse': '0',
        'servico_id': False,
        'numero_lote_rps': 0,
        'numero_protocolo_nfse': '',
        'codigo_verificacao_nfse': '',
        'descricao_servico': '',
        'link_verificacao_nfse': '',

        'vr_frete_rateio': D('0'),
        'vr_seguro_rateio': D('0'),
        'vr_desconto_rateio': D('0'),
        'vr_outras_rateio': D('0'),
        'forca_recalculo_st_compra': False,
        'calcula_diferencial_aliquota': False,
    }

    _order = 'emissao, modelo, data_emissao DESC, serie, numero'
    _rec_name = 'descricao'

    def onchange_operacao(self, cursor, user_id, ids, operacao_id ):
        valores = {}
        retorno = {'value': valores}

        if not operacao_id:
            return retorno

        operacao = self.pool.get('sped.operacao').browse(cursor, user_id, operacao_id)

        valores['regime_tributario'] = operacao.regime_tributario
        valores['entrada_saida'] = operacao.entrada_saida
        valores['forma_pagamento'] = operacao.forma_pagamento
        valores['finalidade_nfe'] = operacao.finalidade_nfe
        valores['modalidade_frete'] = operacao.modalidade_frete
        valores['naturezaoperacao_id'] = operacao.naturezaoperacao_id.id
        valores['infadfisco'] = operacao.infadfisco
        valores['infcomplementar'] = operacao.infcomplementar
        valores['cnae_id'] = operacao.cnae_id.id
        valores['natureza_tributacao_nfse'] = operacao.natureza_tributacao_nfse
        valores['servico_id'] = operacao.servico_id.id
        valores['deduz_retencao'] = operacao.deduz_retencao
        valores['pis_cofins_retido'] = operacao.pis_cofins_retido
        valores['al_pis_retido'] = operacao.al_pis_retido
        valores['al_cofins_retido'] = operacao.al_cofins_retido
        valores['csll_retido'] = operacao.csll_retido
        valores['al_csll'] = operacao.al_csll
        valores['irrf_retido'] = operacao.irrf_retido
        valores['irrf_retido_ignora_limite'] = operacao.irrf_retido_ignora_limite
        valores['al_irrf'] = operacao.al_irrf
        #valores['previdencia_retido'] = operacao.previdencia_retido
        #valores['al_previdencia'] = operacao.al_previdencia
        valores['forca_recalculo_st_compra'] = operacao.forca_recalculo_st_compra
        valores['calcula_diferencial_aliquota'] = operacao.calcula_diferencial_aliquota
        valores['iss_retido'] = operacao.cst_iss == ST_ISS_RETIDO
        valores['limite_retencao_pis_cofins_csll'] = operacao.limite_retencao_pis_cofins_csll or 0
        if operacao.serie:
            valores['serie'] = operacao.serie or ''
            context = {
                        'emissao': '0',
                        'modelo': operacao.modelo,
                        'serie': operacao.serie,
                        'ambiente_nfe': '1',

                       }
            numero = self._get_numero_padrao(cursor, user_id, context=context)
            valores['numero'] = numero or ''

        return retorno

    def onchange_partner_id(self, cursor, user_id, ids, partner_id, context=None):
        valores = {}
        retorno = {'value': valores}

        if not partner_id:
            return res

        partner_obj = self.pool.get('res.partner').browse(cursor, user_id, partner_id)

        valores['partner_contribuinte'] = partner_obj.contribuinte
        valores['partner_cnpj_cpf'] = partner_obj.cnpj_cpf
        valores['partner_razao_social'] = partner_obj.razao_social
        valores['partner_fantasia'] = partner_obj.fantasia
        valores['partner_endereco'] = partner_obj.endereco
        valores['partner_numero'] = partner_obj.numero
        valores['partner_complemento'] = partner_obj.complemento
        valores['partner_bairro'] = partner_obj.bairro
        valores['partner_municipio_id'] = partner_obj.municipio_id.id
        valores['partner_cep'] = partner_obj.cep
        valores['partner_ie'] = partner_obj.ie
        valores['partner_im'] = partner_obj.im

        return retorno

    def _valida_numero_repetido(self, cr, uid, dados, context={}):
        lista_numero = [True]

        while len(lista_numero) != 0:
            modelo = dados['modelo'] or '55'
            serie = dados.get('serie', '') or ''
            ambiente_nfe = dados.get('ambiente_nfe', '2') or '2'
            company_id = dados.get('company_id', False)
            #company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
            company_obj = self.pool.get('res.company').browse(cr, 1, company_id)

            numero = -1
            numero_rps = -1
            busca = [
                ['company_cnpj_cpf', '=', company_obj.partner_id.cnpj_cpf],
                ['emissao', '=', '0'],
                ['modelo', '=', modelo],
                ['serie', '=', serie],
            ]

            if modelo == 'SE':
                numero_rps = dados.get('numero_rps', -1)
                busca.append(['ambiente_nfe', '=', ambiente_nfe])
                busca.append(['numero_rps', '=', numero_rps])
            else:
                numero = dados.get('numero', -1)
                busca.append(['numero', '=', numero])

                if modelo == '55':
                    busca.append(['ambiente_nfe', '=', ambiente_nfe])

            lista_numero = self.search(cr, 1, busca)

            if len(lista_numero) != 0:
                if modelo == 'SE':
                    dados['numero_rps'] = self._get_rps_padrao(cr, uid, context=dados)
                else:
                    dados['numero'] = self._get_numero_padrao(cr, uid, context=dados)

        return dados

    def _valida_sequencia(self, cr, uid, dados, context={}):
        if dados.get('modelo', '55') != '55' or dados.get('emissao', '0') == '1':
            return

        if dados.get('situacao', '00') == SITUACAO_FISCAL_INUTILIZADO:
            return

        proximo_numero = self._get_numero_padrao(cr, uid, dados)

        if 'numero' in dados:
            if proximo_numero != dados['numero']:
                raise osv.except_osv(u'Erro!', u'O número da nota não bate com a numeração da sequência; deveria ser ' + str(proximo_numero) + '!')

        return

    def create(self, cr, uid, dados, context=None):
        dados['company_id_readonly'] = dados['company_id']
        #
        # Verifica duplicidade de numeração de documentos emitidos
        #
        if dados.get('emissao', '1') == '0' and dados.get('modelo', '55') in ['55', 'SE', 'RL']:
            dados = self._valida_numero_repetido(cr, uid, dados, context)

        self._valida_sequencia(cr, uid, dados, context)

        res = super(sped_documento, self).create(cr, uid, dados, context)
        cr.commit()
        self._elimina_itens_sem_produto_proprio(cr, uid, res)

        self.ajusta_impostos_retidos(cr, uid, [res])
        self.ajusta_impostos_lucro_presumido(cr, uid, [res])
        return res

    def write(self, cr, uid, ids, dados, context={}):
        #
        # No caso da prefeitura de João Pessoa, dá muito pau na autorização, então, se o usuário
        # colocar o nº da nota a mão, o sistema considera como autorizado
        #
        if 'numero' in dados and dados['numero'] > 0:
            for doc_obj in self.browse(cr, uid, ids):
                if doc_obj.modelo == 'SE': # and doc_obj.company_id.provedor_nfse and doc_obj.company_id.provedor_nfse == 'IPM':
                    dados['state'] = 'autorizada'

        #
        # No caso de notas de serviço da pref. de Santa Rosa, em que não há um
        # webservice de cancelamento, quando o usuário definir o cancelamento pela
        # situacao fiscal, o sistema deverá alterar o campo state para cancelada,
        # para disparar o cancelamento da parcela do contrato, e perimitir novamente
        # o faturamento
        #
        if 'situacao' in dados:
            if dados['situacao'] == SITUACAO_FISCAL_CANCELADO:
                for doc_obj in self.browse(cr, uid, ids):
                    if doc_obj.modelo == 'SE': # and doc_obj.company_id.provedor_nfse and doc_obj.company_id.provedor_nfse != 'BETHA':
                        dados['state'] = 'cancelada'
            elif dados['situacao'] == SITUACAO_FISCAL_INUTILIZADO:
                        dados['state'] = 'inutilizada'

        if 'state' in dados:
            if dados['state'] == 'autorizada':
                self.pool.get('sped.documento').antes_autorizar(cr, uid, ids, dados=dados, context=context)
            elif dados['state'] == 'cancelada':
                self.pool.get('sped.documento').antes_cancelar(cr, uid, ids, dados=dados, context=context)
        elif 'situacao' in dados:
            if dados['situacao'] in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
                self.pool.get('sped.documento').antes_cancelar(cr, uid, ids, dados=dados, context=context)

        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        if 'state' in dados:
            if dados['state'] == 'autorizada':
                self.pool.get('sped.documento').depois_autorizar(cr, uid, ids, dados=dados, context=context)
            elif dados['state'] == 'cancelada':
                self.pool.get('sped.documento').depois_cancelar(cr, uid, ids, dados=dados, context=context)
        elif 'situacao' in dados:
            if dados['situacao'] in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
                self.pool.get('sped.documento').depois_cancelar(cr, uid, ids, dados=dados, context=context)

        if not ('nao_calcula' in context):
            self.ajusta_impostos_retidos(cr, uid, ids)
            self.ajusta_impostos_lucro_presumido(cr, uid, ids)
            self._elimina_itens_sem_produto_proprio(cr, uid, ids)

        return res

    def _elimina_itens_sem_produto_proprio(self, cr, uid, ids):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if not len(ids):
            return

        for doc_obj in self.browse(cr, uid, ids):
            itens_vazios = []

            if doc_obj.emissao != TIPO_EMISSAO_PROPRIA:
                continue

            for item_obj in doc_obj.documentoitem_ids:
                if not item_obj.produto_id:
                    itens_vazios.append(item_obj.id)

            if len(itens_vazios) > 0:
                self.pool.get('sped.documentoitem').unlink(cr, uid, itens_vazios)

    def action_enviar_nfse(self, cr, uid, ids, context={}):

        if 'active_ids' in context:
            ids = context['active_ids']

        #
        # Reordena os ids para ficarem em ordem do RPS
        #
        ids_ordenados = self.search(cr, uid, [('id', 'in', ids), '|', ('partner_id.eh_orgao_publico', '=', False), ('compra_contrato', '!=', False)], order='numero_rps')

        res = {}
        for id in ids_ordenados:
            doc_obj = self.browse(cr, uid, id)
            doc_obj.write({'numero_lote_rps': 0, 'numero_protocolo_nfse': '', 'resposta_nfse': ''})

            doc_obj = self.browse(cr, uid, id)
            res[doc_obj.id] = trata_nfse.envia_nfse(self, cr, uid, doc_obj)

            doc_obj = self.browse(cr, uid, id)
            trata_nfse.grava_pdf(self, cr, uid, doc_obj)

        return res

    def action_consultar_nfse(self, cr, uid, ids, context=None):
        res = {}
        for id in ids:
            doc_obj = self.browse(cr, uid, id)
            res[doc_obj.id] = trata_nfse.consulta_nfse(self, cr, uid, doc_obj)

            doc_obj = self.browse(cr, uid, id)
            trata_nfse.grava_pdf(self, cr, uid, doc_obj)

        return res

    def action_cancelar_nfse(self, cr, uid, ids, context=None):
        res = {}
        for doc_obj in self.browse(cr, uid, ids):
            res[doc_obj.id] = trata_nfse.cancela_nfse(self, cr, uid, doc_obj)

        return res

    def antes_autorizar(self, cr, uid, ids, dados={}, context={}):
        pass

    def enviar_email_nota(self, cr, uid, ids, context={}, depois_autorizar=False):
        ids_contexto = context.get('active_ids', [])

        print('ids_contexto', ids_contexto)
        print('ids', ids)

        if ids_contexto:
            ids = ids_contexto

        if not ids:
            return False

        doc_pool = self.pool.get('sped.documento')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid)
        mail_pool = self.pool.get('mail.message')
        attachment_pool = self.pool.get('ir.attachment')

        #
        # Verificamos se tem modelo pré-definido
        #
        template_pool = self.pool.get('email.template')
        template_ids = template_pool.search(cr, 1, [('name', '=', 'NF emitida'), ('model_id.model', '=', 'sped.documento')])

        #print('vai fazer')
        if user_obj.user_email:
            for doc_obj in doc_pool.browse(cr, uid, ids):
                if doc_obj.partner_id.email_nfe:
                    #
                    # Força a geração do PDF do recibo de locação
                    #
                    if doc_obj.modelo == 'RL':
                        trata_nfse.grava_pdf_recibo_locacao(self, cr, uid, doc_obj)
                    elif doc_obj.modelo == '55':
                        trata_nfe.gera_danfe(self, cr, uid, doc_obj)
                    elif doc_obj.modelo == 'SE':
                        trata_nfse.grava_pdf(self, cr, uid, doc_obj)

                    if template_ids:
                        dados = template_pool.generate_email(cr, 1, template_ids[0], doc_obj.id, context=context)

                        if 'attachment_ids' in dados:
                            del dados['attachment_ids']

                        dados.update({
                            'model': 'sped.documento',
                            'res_id': doc_obj.id,
                            'user_id': uid,
                            'email_to': doc_obj.partner_id.email_nfe or '',
                            'date': str(fields.datetime.now()),
                            'reply_to': user_obj.user_email,
                            'state': 'outgoing',
                        })

                        if 'email_from' not in dados or (not dados['email_from']):
                            dados['email_from'] = user_obj.user_email

                    else:
                        dados = {
                            'subject':  u'Envio de nossa NF-e',
                            'model': 'sped.documento',
                            'res_id': doc_obj.id,
                            'user_id': uid,
                            'email_to': doc_obj.partner_id.email_nfe or '',
                            #'email_to': 'ari@erpintegra.com.br',
                            'email_from': user_obj.user_email,
                            'date': str(fields.datetime.now()),
                            'headers': '{}',
                            'email_cc': '',
                            'reply_to': user_obj.user_email,
                            'state': 'outgoing',
                            'message_id': False,
                        }

                    dados['subject'] += u' nº ' + formata_valor(doc_obj.numero or 0, casas_decimais=0) + ' de ' + formata_data(doc_obj.data_emissao_brasilia)

                    #
                    # Verificando se já não foi enviado antes, quando é enviado automático depois de autorizar
                    #
                    if depois_autorizar:
                        mail_ids = mail_pool.search(cr, uid, [('model', '=', 'sped.documento'), ('res_id', '=', doc_obj.id), ('subject', '=', dados['subject'])])

                        if len(mail_ids):
                            continue

                    #
                    # Só envia o email se houver anexos
                    #
                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sped.documento'), ('res_id', '=', doc_obj.id)])
                    if len(attachment_ids):
                        anexos = []
                        for attachment_id in attachment_ids:
                            anexos.append((4, attachment_id))

                        dados['attachment_ids'] = anexos
                        mail_id = mail_pool.create(cr, uid, dados)
                        mail_pool.process_email_queue(cr, uid, [mail_id])

        return {'value': {}, 'warning': {'title': u'Confirmação', 'message': u'Envio agendado!'}}

    def depois_autorizar(self, cr, uid, ids, dados={}, context={}):
        print('entrou depois autorizar', fields.datetime.now(), dados, context)

        if len(dados) == 1 and 'state' in dados and dados['state'] == 'autorizada':
            self.pool.get('sped.documento').enviar_email_nota(cr, uid, ids, context=context, depois_autorizar=True)

        elif len(dados) == 2 and 'state' in dados and 'data_autorizacao' in dados and dados['state'] == 'autorizada':
            self.pool.get('sped.documento').enviar_email_nota(cr, uid, ids, context=context, depois_autorizar=True)

        return True

    def antes_cancelar(self, cr, uid, ids, dados={}, context={}):
        pass

    def depois_cancelar(self, cr, uid, ids, dados={}, context={}):
        pass

    def ajusta_impostos_retidos(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.emissao == '1' and doc_obj.modelo == '55':
                continue

            if doc_obj.entrada_saida == '1' and doc_obj.partner_id.tipo_pessoa != 'J':
                continue

            vr_pis_retido = D('0')
            vr_cofins_retido = D('0')
            vr_csll = D('0')
            bc_irrf = D('0')
            vr_irrf = D('0')
            previdencia_retido = False
            bc_previdencia = D(str(doc_obj.bc_previdencia))
            vr_previdencia = D(str(doc_obj.vr_previdencia))
            al_previdencia = D('0')
            bc_iss_retido = D('0')
            vr_iss_retido = D('0')
            vr_operacao = D(str(doc_obj.vr_operacao)).quantize(D('0.01'))
            vr_operacao_pis_cofins_csll = D(str(doc_obj.vr_operacao)).quantize(D('0.01'))

            #
            # PIS, COFINS e CSLL somente retém para pessoas jurídicas que não sejam
            # do regime tributário SIMPLES
            #
            if doc_obj.partner_id.regime_tributario not in (REGIME_TRIBUTARIO_SIMPLES, REGIME_TRIBUTARIO_SIMPLES_EXCESSO):
                #
                # Acumula as operações e valores retidos anteriormente
                # no mesmo mês, para o PIS, COFINS e CSLL
                #
                # No caso da Patrimonial, isso foi alterado para ser pelo mesmo vencimento
                # do contrato
                #
                if doc_obj.limite_retencao_pis_cofins_csll > 0:
                    nota_emitida_retencao_ids = []

                    if 'patrimonial' in cr.dbname.lower():
                        data_vencimento = None
                        if doc_obj.finan_contrato_id:
                            data_vencimento = doc_obj.finan_lancamento_id.data_vencimento
                        elif len(doc_obj.duplicata_ids):
                            data_vencimento = doc_obj.duplicata_ids[0].data_vencimento

                        if data_vencimento:
                            nota_emitida_retencao_ids = self.search(cr, uid, [('emissao', '=', '0'), ('company_id.partner_id.cnpj_cpf', '=', doc_obj.company_id.partner_id.cnpj_cpf), ('partner_id.cnpj_cpf', 'ilike', doc_obj.partner_id.cnpj_cpf[:10]), ('modelo', '=', doc_obj.modelo), ('finan_lancamento_id.data_vencimento', '=', data_vencimento), ('id', '!=', doc_obj.id), ('situacao', 'in', SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

                    else:
                        data_emissao = parse_datetime(doc_obj.data_emissao + ' UTC')
                        data_inicio_mes = datetime.datetime(data_emissao.year, data_emissao.month, 1)

                        #
                        # Quais notas foram emitidas no último mês
                        #
                        #nota_emitida_retencao_ids = self.search(cr, uid, [('emissao', '=', '0'), ('company_id.partner_id.cnpj_cpf', '=', doc_obj.company_id.partner_id.cnpj_cpf), ('partner_id', '=', doc_obj.partner_id.id), ('modelo', '=', doc_obj.modelo), ('data_emissao', '>=', data_inicio_mes.strftime('%Y-%m-%d') + ' 00:00:00'), ('data_emissao', '<=', doc_obj.data_emissao), ('id', '!=', doc_obj.id), ('situacao', 'in', SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

                        nota_emitida_retencao_ids = []

                    print('notas com retencao')
                    print(nota_emitida_retencao_ids)

                    #
                    # Acumula o valor da operação, deduz as retenções já realizadas
                    #
                    for nota_emitida_retencao_obj in self.browse(cr, uid, nota_emitida_retencao_ids):
                        vr_operacao_pis_cofins_csll += D(str(nota_emitida_retencao_obj.vr_operacao))
                        vr_pis_retido -= D(str(nota_emitida_retencao_obj.vr_pis_retido))
                        vr_cofins_retido -= D(str(nota_emitida_retencao_obj.vr_cofins_retido))
                        vr_csll -= D(str(nota_emitida_retencao_obj.vr_csll))

                print('valores retidos anteriormente')
                print('vr_operacao_pis_cofins_csll', vr_operacao_pis_cofins_csll)
                print('vr_pis_retido', vr_pis_retido)
                print('vr_cofins_retido', vr_cofins_retido)
                print('vr_csll', vr_csll)

                if doc_obj.pis_cofins_retido and (vr_operacao_pis_cofins_csll > doc_obj.limite_retencao_pis_cofins_csll):
                    #
                    # Aqui soma para considerar a possível dedução do acumulado
                    #
                    vr_pis_retido += vr_operacao_pis_cofins_csll * D(str(doc_obj.al_pis_retido)) / D('100.0000000000')
                    vr_cofins_retido += vr_operacao_pis_cofins_csll * D(str(doc_obj.al_cofins_retido)) / D('100.0000000000')
                    vr_pis_retido = vr_pis_retido.quantize(D('0.01'))
                    vr_cofins_retido = vr_cofins_retido.quantize(D('0.01'))
                else:
                    vr_pis_retido = 0
                    vr_cofins_retido = 0

                if doc_obj.csll_retido and (vr_operacao_pis_cofins_csll > doc_obj.limite_retencao_pis_cofins_csll):
                    #
                    # Aqui soma para considerar a possível dedução do acumulado
                    #
                    vr_csll += vr_operacao_pis_cofins_csll * D(str(doc_obj.al_csll)) / D('100.0000000000')
                    vr_csll = vr_csll.quantize(D('0.01'))
                else:
                    vr_csll = 0

            if doc_obj.irrf_retido:
                bc_irrf = vr_operacao
                vr_irrf = bc_irrf * D(str(doc_obj.al_irrf)) / D('100.0000000000')
                vr_irrf = vr_irrf.quantize(D('0.01'))
                #
                # Imposto Federal, só reter se valor for a partir de R$ 10,00
                #
                print('base e valor ir', bc_irrf, vr_irrf)
                if vr_irrf < 10 and (not doc_obj.irrf_retido_ignora_limite):
                    bc_irrf = D('0')
                    vr_irrf = D('0')

            if doc_obj.vr_previdencia > 0:
                previdencia_retido = True
                al_previdencia = vr_previdencia / bc_previdencia * D('100.0000000000')
                al_previdencia = al_previdencia.quantize(D('0.0001'))

            if doc_obj.iss_retido:
                bc_iss_retido = D(str(doc_obj.bc_iss))
                vr_iss_retido = D(str(doc_obj.vr_iss))

            #
            # Somas as retenções, e verifica se vai ultrapassar o vr_operacao
            #
            soma_retencoes = vr_pis_retido + vr_cofins_retido + vr_csll + vr_irrf + vr_previdencia + vr_iss_retido

            if soma_retencoes > vr_operacao:
                #
                # As retenções de ISS, IRRF e INSS sempre são cobradas
                # já que não sofrem acúmulo
                #
                saldo_vr_operacao = vr_operacao - (vr_irrf + vr_previdencia + vr_iss_retido)
                soma_retencoes = vr_pis_retido + vr_cofins_retido + vr_csll
                proporcao_pis = vr_pis_retido / soma_retencoes
                proporcao_cofins = vr_cofins_retido / soma_retencoes
                proporcao_csll = vr_csll / soma_retencoes
                vr_pis_retido = saldo_vr_operacao * proporcao_pis
                vr_pis_retido = vr_pis_retido.quantize(D('0.01'))
                vr_cofins_retido = saldo_vr_operacao * proporcao_cofins
                vr_cofins_retido = vr_cofins_retido.quantize(D('0.01'))
                vr_csll = saldo_vr_operacao * proporcao_csll
                vr_csll = vr_csll.quantize(D('0.01'))

                #
                # Verifica agora se há 0,01 de diferença a considerar;
                # se houver, tira do maior valor
                #
                saldo_vr_operacao -= vr_pis_retido + vr_cofins_retido + vr_csll

                if vr_cofins_retido > vr_csll and vr_cofins_retido > vr_pis_retido:
                    vr_cofins_retido += saldo_vr_operacao
                elif vr_pis_retido > vr_csll and vr_pis_retido > vr_cofins_retido:
                    vr_pis_retido += saldo_vr_operacao
                elif vr_csll > vr_pis_retido and vr_csll > vr_cofins_retido:
                    vr_csll += saldo_vr_operacao

            dados = {
                'id': doc_obj.id,
                'vr_pis_retido': vr_pis_retido,
                'vr_cofins_retido': vr_cofins_retido,
                'vr_csll': vr_csll,
                'bc_irrf': bc_irrf,
                'vr_irrf': vr_irrf,
                'previdencia_retido': previdencia_retido,
                'al_previdencia': al_previdencia,
                'bc_iss_retido': bc_iss_retido,
                'vr_iss_retido': vr_iss_retido,
            }

            #sql = """
                #update sped_documento set
                    #vr_pis_retido = {vr_pis_retido:.2f},
                    #vr_cofins_retido = {vr_cofins_retido:.2f},
                    #vr_csll = {vr_csll:.2f},
                    #bc_irrf = {bc_irrf:.2f},
                    #vr_irrf = {vr_irrf:.2f},
                    #previdencia_retido = {previdencia_retido},
                    #al_previdencia = {al_previdencia:.4f},
                    #bc_iss_retido = {bc_iss_retido:.2f},
                    #vr_iss_retido = {vr_iss_retido:.2f}
                #where id = {id:d};
            #""".format(**dados)
            #print(sql)
            #cr.execute(sql)
            super(sped_documento, self).write(cr, uid, [doc_obj.id], dados, context={'nao_calcula': True})

    def ari(self, cr, uid, ids, context={}):
        busca = [
            ('company_id', 'in', (77, 73, 78, 5, 34, 156, 33, 32, 75, 79, 76, 160, 159)),
            ('emissao', '=', '0'),
            ('entrada_saida', '=', '0'),
            ('operacao_id', 'in', [429, 189, 191]),
            #'|',
            #('modelo', 'in', ('SE', 'RL', '55', '')),
            #('forma_pagamento', '!=', '2'),
            ('data_emissao_brasilia', '>=', '2015-01-01'),
        ]
        nota_ids = self.pool.get('sped.documento').search(cr, uid, busca)
        print(nota_ids)
        print(len(nota_ids))
        self.pool.get('sped.documento').ajusta_impostos_lucro_presumido(cr, uid, nota_ids)

    def ajusta_impostos_lucro_presumido(self, cr, uid, ids, context={}):
        #doc_pool = self.pool.get('sped.documento')
        #ids = doc_pool.search(cr, uid, [('emissao', '=', '0'), ('regime_tributario', '=', REGIME_TRIBUTARIO_LUCRO_PRESUMIDO),
            #('entrada_saida', '=', ENTRADA_SAIDA), '|', ('forma_pagamento', '!=', FORMA_PAGAMENTO_SEM_PAGAMENTO),
            #('modelo', 'in', ['SE', 'RL']), ('data_emissao_brasilia', '>=', '2016-03-18')])

        for doc_obj in self.browse(cr, uid, ids):
            #
            # Do lucro presumido
            #
            if doc_obj.company_id.regime_tributario != REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
                continue

            #
            # De saída, ou entrada por devolução de venda
            #
            if doc_obj.entrada_saida == ENTRADA_SAIDA_SAIDA:
                #
                # E que gerem financeiro (contas a receber)
                #
                if (doc_obj.forma_pagamento == FORMA_PAGAMENTO_SEM_PAGAMENTO) and (doc_obj.modelo not in ('SE', 'RL')):
                    continue
            else:
                #
                # Verifica as CFOPs de devolução
                #
                eh_devolucao = False
                for item_obj in doc_obj.documentoitem_ids:
                    if item_obj.cfop_id.codigo in CFOPS_DEVOLUCAO_VENDA:
                        eh_devolucao = True
                        break

                if not eh_devolucao:
                    continue

            bc_csll_propria = D(0)
            al_csll_propria = D(0)
            vr_csll_propria = D(0)
            bc_irpj_proprio = D(0)
            al_irpj_proprio = D(0)
            vr_irpj_proprio = D(0)

            #
            # ICMS ST e IPI não entram como receita bruta
            # http://www.portaltributario.com.br/guia/lucro_presumido_irpj.html
            # Na receita bruta não se incluem (Lei 8.541/1992, artigo 14, § 4°).
            #
            # 1. as vendas canceladas;
            # 2. os descontos incondicionais concedidos (constantes na nota fiscal de venda dos bens ou da fatura de serviços e não dependentes de evento posterior á emissão desses documentos);
            # 3. os impostos não cumulativos cobrados destacadamente do comprador ou contratante dos quais o vendedor dos bens ou o prestador dos serviços seja mero depositário. Estes impostos são: o IPI incidente sobre as vendas e ao ICMS devido por substituição tributária
            #
            receita_bruta = D(doc_obj.vr_nf or 0)
            receita_bruta -= D(doc_obj.vr_icms_st or 0)
            receita_bruta -= D(doc_obj.vr_ipi or 0)

            if doc_obj.modelo == 'SE' or doc_obj.modelo == 'RL':
                lucro_irpj = receita_bruta * D(32) / D(100)
                lucro_csll = receita_bruta * D(32) / D(100)

            else:
                lucro_irpj = receita_bruta * D(8) / D(100)
                lucro_csll = receita_bruta * D(12) / D(100)

            #
            # A alíquota do IRPJ é 15% para faturamento até 20.000,00
            # A partir de 20.000,00, a alíquota sobe pra 25%
            # http://www.portaltributario.com.br/guia/lucro_presumido_irpj.html
            #
            sql = """
            select
                coalesce(sum(coalesce(d.vr_nf, 0) - coalesce(d.vr_icms_st, 0) - coalesce(d.vr_ipi, 0)), 0) as receita_bruta
            from
                sped_documento d
                join res_company c on c.id = d.company_id
                join res_partner p on p.id = c.partner_id
            where
                d.emissao = '0'
                and d.entrada_saida = '1'
                and d.forma_pagamento != '2'
                and d.data_emissao_brasilia between '{data_inicial}' and '{data_final}';
            """
            bc_irpj_proprio = lucro_irpj.quantize(D('0.01'))
            al_irpj_proprio = D(15)
            vr_irpj_proprio = bc_irpj_proprio * al_irpj_proprio / D(100)
            vr_irpj_proprio = vr_irpj_proprio.quantize(D('0.01'))

            bc_csll_propria = lucro_csll.quantize(D('0.01'))
            al_csll_propria = D(9)
            vr_csll_propria = bc_csll_propria * al_csll_propria / D(100)
            vr_csll_propria = vr_csll_propria.quantize(D('0.01'))

            dados = {
                #'id': doc_obj.id,
                'bc_irpj_proprio': bc_irpj_proprio,
                'al_irpj_proprio': al_irpj_proprio,
                'vr_irpj_proprio': vr_irpj_proprio,
                'bc_csll_propria': bc_csll_propria,
                'al_csll_propria': al_csll_propria,
                'vr_csll_propria': vr_csll_propria,
            }

            sql = """
                update sped_documento set
                    bc_irpj_proprio = {bc_irpj_proprio:.2f},
                    al_irpj_proprio = {al_irpj_proprio:.2f},
                    vr_irpj_proprio = {vr_irpj_proprio:.2f},
                    bc_csll_propria = {bc_csll_propria:.2f},
                    al_csll_propria = {al_csll_propria:.2f},
                    vr_csll_propria = {vr_csll_propria:.2f}
                where id = {id:d};
            """.format(id=doc_obj.id, **dados)
            #print(sql)
            cr.execute(sql)
            super(sped_documento, self).write(cr, uid, [doc_obj.id], dados, context={'nao_calcula': True})

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            sped_documento_id = ids[0]

        if not sped_documento_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sped', 'sped_nfe_emitida_form')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'sped.documento',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'sped.documento', 'active_ids': [sped_documento_id]},
        }

        return retorno

    def envio_nfse_automatico(self, cr, uid, ids, context={}):
        doc_pool = self.pool.get('sped.documento')
        doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'SE'), ('emissao', '=', '0'), ('state', '=', 'a_enviar')], order='numero_rps')

        for id in doc_ids:
            doc_obj = self.browse(cr, uid, id)
            if doc_obj.state == 'a_enviar':
                #try:
                doc_obj.action_enviar_nfse()
                #except:
                    #pass

    def marca_envio_nfse_automatico(self, cr, uid, ids, context={}):
        ids_contexto = context.get('active_ids', [])

        if ids_contexto:
            ids = ids_contexto

        if not ids:
            return False

        doc_pool = self.pool.get('sped.documento')
        doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'SE'), ('emissao', '=', '0'), ('state', 'in', ['em_digitacao', 'rejeitada']), ('id', 'in', ids), '|', ('partner_id.eh_orgao_publico', '=', False), ('compra_contrato', '!=', False)], order='numero_rps')

        print(doc_ids, 'notas a enviar')

        if len(doc_ids) == 0:
            return {'message': 'Notas marcadas para envio!', 'value': {}}

        cr.execute("update sped_documento set state = 'a_enviar' where id in (" + str(doc_ids).replace('[', '').replace(']', '') + ")")

        #self.write(cr, uid, doc_ids, {'state': 'a_enviar'})

        #
        # Envia imediatamente
        #
        self.envio_nfse_automatico(cr, uid, doc_ids, context=context)

        #
        # Consulta imediatamente
        #
        self.consulta_nfse_automatico(cr, uid, doc_ids, context=context)

        return {'value': {}, 'warning': {'title': u'Confirmação', 'message': u'Envio agendado!'}}

    def consulta_nfse_automatico(self, cr, uid, ids, context={}):
        doc_pool = self.pool.get('sped.documento')
        doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'SE'), ('emissao', '=', '0'), ('state', '=', 'enviada')], order='numero_rps')

        for id in doc_ids:
            doc_obj = self.browse(cr, uid, id)
            doc_obj.action_consultar_nfse()

        return False

    def onchange_chave(self, cr, uid, ids, modelo, chave, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not (modelo and chave):
            return res

        try:
            cnpj = formata_cnpj(chave[6:20])
            serie = chave[22:25]
            serie = str(int(serie))
            numero = int(chave[25:34])
            modelo_chave = chave[20:22]

            if modelo != modelo_chave:
                raise osv.except_osv(u'Erro!', u'O modelo da chave não é ' + modelo + '!')

            valores['serie'] = serie
            valores['numero'] = numero

            partner_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj)], order='id')

            if len(partner_ids) > 0:
                valores['partner_id'] = partner_ids[0]
        except:
            pass

        return res

    def action_gerar_recibo_locacao(self, cr, uid, ids, context=None):
        res = {}
        for doc_obj in self.browse(cr, uid, ids):
            trata_nfse.grava_pdf_recibo_locacao(self, cr, uid, doc_obj)

        return res

    def onchange_al_icms_sem_item(self, cr, uid, ids, bc_icms_proprio, al_icms_sem_item):
        res = {}
        valores = {}
        res['value'] = valores

        if not bc_icms_proprio or not al_icms_sem_item:
            return res

        valores['vr_icms_proprio'] = bc_icms_proprio * float(al_icms_sem_item) / 100.00

        return res

    def onchange_company_id(self, cr, uid, ids, company_id):
        res = {}
        valores = {}
        res['value'] = valores

        if not company_id:
            return res

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        valores['company_cnpj_cpf'] = company_obj.partner_id.cnpj_cpf

        if company_obj.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if company_obj.matriz_id:
                valores['simples_anexo'] = company_obj.matriz_id.simples_anexo
                valores['simples_teto'] = company_obj.matriz_id.simples_teto
            else:
                valores['simples_anexo'] = company_obj.simples_anexo
                valores['simples_teto'] = company_obj.simples_teto

        return res

    def onchange_provedor(self, cr, uid, ids, company_id_readonly):
        res = {}
        valores = {}
        res['value'] = valores

        if not company_id_readonly:
            return res

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id_readonly)
        valores['company_provedor_nfse'] = company_obj.provedor_nfse

        return res

    def unlink(self, cr, uid, ids, context={}):
        #
        # Valida exclusão de notas eletrônicas autorizadas
        #
        for doc_obj in self.browse(cr, uid, ids):
            if doc_obj.emissao == '0' and doc_obj.modelo in ['55', 'SE', '2D'] and doc_obj.state in ['autorizada', 'cancelada', 'denegada', 'inutilizada']:

                if doc_obj.modelo == '55' and doc_obj.ambiente_nfe == '2':
                    continue

                raise osv.except_osv(u'Erro!', u'O documento nº “{numero}” não pode ser excluído!'.format(numero=doc_obj.numero))

        return super(sped_documento, self).unlink(cr, uid, ids)

    def message_new(self, cr, uid, msg_dict, custom_values=None, context=None):
        """Called by ``message_process`` when a new message is received
           for a given thread model, if the message did not belong to
           an existing thread.
           The default behavior is to create a new record of the corresponding
           model (based on some very basic info extracted from the message),
           then attach the message to the newly created record
           (by calling ``message_append_dict``).
           Additional behavior may be implemented by overriding this method.

           :param dict msg_dict: a map containing the email details and
                                 attachments. See ``message_process`` and
                                ``mail.message.parse`` for details.
           :param dict custom_values: optional dictionary of additional
                                      field values to pass to create()
                                      when creating the new thread record.
                                      Be careful, these values may override
                                      any other values coming from the message.
           :param dict context: if a ``thread_model`` value is present
                                in the context, its value will be used
                                to determine the model of the record
                                to create (instead of the current model).
           :rtype: int
           :return: the id of the newly created thread object
        """
        if context is None:
            context = {}
        print('entrou aqui')
        model = context.get('thread_model') or self._name
        model_pool = self.pool.get(model)
        fields = model_pool.fields_get(cr, uid, context=context)
        data = model_pool.default_get(cr, uid, fields, context=context)
        if 'name' in fields and not data.get('name'):
            data['name'] = msg_dict.get('from','')
        if custom_values and isinstance(custom_values, dict):
            data.update(custom_values)
        res_id = model_pool.create(cr, uid, data, context=context)
        self.message_append_dict(cr, uid, [res_id], msg_dict, context=context)
        return res_id

    def message_append(self, cr, uid, threads, subject, body_text=None, email_to=False,
                email_from=False, email_cc=None, email_bcc=None, reply_to=None,
                email_date=None, message_id=False, references=None,
                attachments=None, body_html=None, subtype=None, headers=None,
                original=None, context=None, forcar_data=False):
        """Creates a new mail.message attached to the current mail.thread,
           containing all the details passed as parameters.  All attachments
           will be attached to the thread record as well as to the actual
           message.
           If only the ``threads`` and ``subject`` parameters are provided,
           a *event log* message is created, without the usual envelope
           attributes (sender, recipients, etc.).

        :param threads: list of thread ids, or list of browse_records representing
                        threads to which a new message should be attached
        :param subject: subject of the message, or description of the event if this
                        is an *event log* entry.
        :param email_to: Email-To / Recipient address
        :param email_from: Email From / Sender address if any
        :param email_cc: Comma-Separated list of Carbon Copy Emails To addresse if any
        :param email_bcc: Comma-Separated list of Blind Carbon Copy Emails To addresses if any
        :param reply_to: reply_to header
        :param email_date: email date string if different from now, in server timezone
        :param message_id: optional email identifier
        :param references: optional email references
        :param body_text: plaintext contents of the mail or log message
        :param body_html: html contents of the mail or log message
        :param subtype: optional type of message: 'plain' or 'html', corresponding to the main
                        body contents (body_text or body_html).
        :param headers: mail headers to store
        :param dict attachments: map of attachment filenames to binary contents, if any.
        :param str original: optional full source of the RFC2822 email, for reference
        :param dict context: if a ``thread_model`` value is present
                             in the context, its value will be used
                             to determine the model of the thread to
                             update (instead of the current model).
        """
        if context is None:
            context = {}
        if attachments is None:
            attachments = {}

        if all(isinstance(thread_id, (int, long)) for thread_id in threads):
            model = context.get('thread_model') or self._name
            model_pool = self.pool.get(model)
            doc_obj = model_pool.browse(cr, uid, threads, context=context)

            if not email_to:
                email_to = doc_obj.partner_id.email_nfe or ''

        return super(sped_documento, self).message_append(cr, uid, threads,
            subject, body_text=body_text, email_to=email_to,
            email_from=email_from, email_cc=email_cc, email_bcc=email_bcc,
            reply_to=reply_to, email_date=email_date, message_id=message_id,
            references=references, attachments=attachments, body_html=body_html,
            subtype=subtype, headers=headers, original=original, context=context,
            forcar_data=forcar_data)

    def onchange_data_emissao(self, cr, uid, ids, data_emissao, data_entrada_saida):
        if (not data_emissao) or (data_entrada_saida):
            return {}

        valores = {'data_entrada_saida': data_emissao}
        res['value'] = valores

        return res

    def gerar_itens_devolucao(self, cr, uid, ids, context={}):
        res = {}

        ajusta_valor_venda = context.get('ajusta_valor_venda', False)

        for nota_obj in self.browse(cr, uid, ids):
            sped_itemreferenciado_objs = nota_obj.documentoreferenciado_ids

            if len(sped_itemreferenciado_objs) == 0:
                raise osv.except_osv(u'Erro!', u' Não existem Notas de Retorno Vinculadas!')

            dados_nota = {
                    'company_id': nota_obj.company_id.id,
                    'partner_id': nota_obj.partner_id.id,
                    'operacao_id': nota_obj.operacao_id.id,
                }
            contexto_item = copy(dados_nota)
            contexto_item['ajusta_valor_venda'] = ajusta_valor_venda

            for chave in dados_nota:
                if 'default_' not in chave:
                    contexto_item['default_' + chave] = contexto_item[chave]

            contexto_item['entrada_saida'] = nota_obj.entrada_saida
            contexto_item['regime_tributario'] = nota_obj.regime_tributario
            contexto_item['emissao'] = nota_obj.emissao
            contexto_item['data_emissao'] = nota_obj.data_emissao
            contexto_item['default_entrada_saida'] = nota_obj.entrada_saida
            contexto_item['default_regime_tributario'] = nota_obj.regime_tributario
            contexto_item['default_emissao'] = nota_obj.emissao
            contexto_item['default_data_emissao'] = nota_obj.data_emissao

            for sped_itemreferenciado_obj in sped_itemreferenciado_objs:
                sql = """
                select
                    sde.id
                from
                    sped_documentoitem sde
                    join sped_documento sd on sd.id = sde.documento_id

                where
                    sd.id = {documento_id}

                """
                cr.execute(sql.format(documento_id=sped_itemreferenciado_obj.documentoreferenciado_id.id))
                documentos = cr.fetchall()
                for id, in documentos:
                    documento_item = self.pool.get('sped.documentoitem').browse(cr, uid, id)

                    if documento_item.produto_id:

                        dados = {
                             'documento_id': nota_obj.id,
                             'produto_id': documento_item.produto_id.id,
                             'quantidade': documento_item.quantidade,
                             'vr_unitario': documento_item.vr_unitario,
                            }

                        item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados, context=contexto_item)
                        item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)
                        dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)

                        if not 'value' in dados_item:
                            raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % item_obj.produto_id.id)

                        item_obj.write(dados_item['value'])

                        dados_item = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                        item_obj.write(dados_item['value'])

            nota_obj.ajusta_impostos_retidos()
            nota_obj.ajusta_impostos_lucro_presumido()

    def forca_recalculo(self, cr, uid, ids, context={}):
        for nota_obj in self.browse(cr, uid, ids):
            for item_obj in nota_obj.documentoitem_ids:
                item_obj.write({'recalculo': int(random.random() * 100000000)})

    def trata_itens_entrada_terceiros(self, cr, uid, ids, context={}):
        res = {}

        for nota_obj in self.browse(cr, uid, ids, context=context):
            if nota_obj.emissao == TIPO_EMISSAO_PROPRIA:
                continue

            if not nota_obj.operacao_id:
                continue

            #
            # Vamos analisar cada item da nota, vinculando o produto correto,
            # e apropriando créditos de acordo com a operação ou com a úlitma
            # compra do mesmo produto
            #
            for item_obj in nota_obj.documentoitem_ids:

                #
                # Se o produto já estiver atribuído, ignora
                #
                if item_obj.produto_id:
                    continue

                #
                # Se o código original do fornecedor não existir, ignora
                #
                if not item_obj.produto_codigo:
                    continue

                #
                # Vamos buscar o código do fornecedor na tabela de produtos
                #
                sql = '''
select
ps.product_id

from
product_supplierinfo ps

where
ps.product_code = '{produto_codigo}'
and ps.name = {partner_id}

limit 1;'''
                sql = sql.format(produto_codigo=item_obj.produto_codigo, partner_id=nota_obj.partner_id.id)
                cr.execute(sql)
                dados = cr.fetchall()

                product_id = None
                item_anterior_id = None

                if len(dados):
                    product_id = dados[0][0]

                #
                # Não encontrei, vou buscar em outra nota que tenha recebido desse mesmo
                # fornecedor
                #
                if product_id is None:
                    sql = '''
select
di.produto_id

from sped_documentoitem di
join sped_documento d on d.id = di.documento_id

where
di.produto_codigo = '{produto_codigo}'
and d.partner_id = {partner_id}
and d.emissao = '1' and d.entrada_saida = '0'
and di.produto_id is not null

limit 1;'''

                    sql = sql.format(produto_codigo=item_obj.produto_codigo, partner_id=nota_obj.partner_id.id)
                    cr.execute(sql)
                    dados = cr.fetchall()

                    if len(dados):
                        product_id = dados[0][0]

                if not product_id:
                    continue

                #
                # Encontramos o produto, vamos associar a CFOP
                #
                contexto_item = {
                    'company_id': nota_obj.company_id.id,
                    'partner_id': nota_obj.partner_id.id,
                    'operacao_id': nota_obj.operacao_id.id,
                    'entrada_saida': nota_obj.entrada_saida,
                    'regime_tributario': nota_obj.regime_tributario,
                    'emissao': nota_obj.emissao,
                    'data_emissao': nota_obj.data_emissao,

                    'default_company_id': nota_obj.company_id.id,
                    'default_partner_id': nota_obj.partner_id.id,
                    'default_operacao_id': nota_obj.operacao_id.id,
                    'default_entrada_saida': nota_obj.entrada_saida,
                    'default_regime_tributario': nota_obj.regime_tributario,
                    'default_emissao': nota_obj.emissao,
                    'default_data_emissao': nota_obj.data_emissao,
                }

                dados_item = self.pool.get('sped.documentoitem').onchange_produto_entrada(cr, uid, [item_obj.id], product_id, item_obj.cfop_original_id.id, False, context=contexto_item)

                if not 'value' in dados_item:
                    raise osv.except_osv(u'Erro!', u'Sem configuração, ou configuração incorreta, para o produto "%s"!' % produto_obj.name)

                dados_item['value']['produto_id'] = product_id

                item_obj.write(dados_item['value'])
                ###item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_obj.id)

                ####
                #### Agora que temos o produto e a CFOP, buscamos a regra de entrada do
                #### mesmo fornecedor, do mesmo produto, da mesa CFOP de entrada
                ####
                ###sql = '''
###select
    ###di.id

###from
    ###sped_documentoitem di
    ###join sped_documento d on d.id = di.documento_id
    ###join res_company c on c.id = d.company_id
    ###join res_partner p on p.id = c.partner_id

###where
    ###p.cnpj_cpf = '{cnpj}'
    ###and d.partner_id = {partner_id}
    ###and d.emissao = '1' and d.entrada_saida = '0'
    ###and d.situacao in ('00', '01', '08')
    ###and di.produto_id = {product_id}
    ###and di.cfop_id = {cfop_id}
    ###and di.id != {item_id}

###order by
    ###d.data_emissao_brasilia desc

###limit 1;'''
                ###sql = sql.format(cnpj=nota_obj.company_id.partner_id.cnpj_cpf, partner_id=nota_obj.partner_id.id, product_id=product_id, cfop_id=item_obj.cfop_id.id, item_id=item_obj.id)
                ###print(sql)
                ###cr.execute(sql)
                ###dados = cr.fetchall()

                ###print(dados)

                ###if not len(dados):
                    ###continue

                ###item_anterior_id = dados[0][0]
                ###item_anterior_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_anterior_id)

                ###dados = {
                    ###'credita_icms_proprio': item_anterior_obj.credita_icms_proprio,
                    ###'credita_icms_st': item_anterior_obj.credita_icms_st,
                    ###'credita_ipi': item_anterior_obj.credita_ipi,
                    ###'credita_pis_cofins': item_anterior_obj.credita_pis_cofins,
                    ###'fator_quantidade': item_anterior_obj.fator_quantidade or 1,
                    ###'quantidade_estoque': (item_anterior_obj.fator_quantidade or 1) * item_obj.quantidade,
                ###}

                ###print(dados)

                ###item_obj.write(dados)

            nota_obj.ajusta_impostos_retidos()
            nota_obj.forca_recalculo()

    def abre_nota_emitida(self, cr, uid, ids, context={}):
        return {
            'type': 'ir.actions.act_window',
            'name': u'NFe emitida',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.documento',
            'res_id': ids[0],
            'target': 'inline',  # Abre na mesma janela, sem ser no meio da tela
        }

    def onchange_serie(self, cr, uid, ids, serie, context={}):
        valores = {}
        res = {'value': valores}

        if not serie:
            return res

        print('serie', serie, '800' <= serie <= '899')
        if '800' <= serie <= '899':
            valores['processo_emissao_nfe'] = PROCESSO_EMISSAO_NFE_FISCO_AVULSA
        else:
            valores['processo_emissao_nfe'] = PROCESSO_EMISSAO_NFE_CONTRIBUINTE_PROPRIO

        return res

    def importa_nota_avulsa(self, cr, uid, ids, context={}):
        trata_nfe.importa_nota_avulsa(self, cr, uid, ids, context=context)


sped_documento()


class mail_compose_message(osv.osv_memory):
    """Generic E-mail composition wizard. This wizard is meant to be inherited
       at model and view level to provide specific wizard features.

       The behavior of the wizard can be modified through the use of context
       parameters, among which are:

         * mail.compose.message.mode: if set to 'reply', the wizard is in
                      reply mode and pre-populated with the original quote.
                      If set to 'mass_mail', the wizard is in mass mailing
                      where the mail details can contain template placeholders
                      that will be merged with actual data before being sent
                      to each recipient. Recipients will be derived from the
                      records determined via  ``context['active_model']`` and
                      ``context['active_ids']``.
         * active_model: model name of the document to which the mail being
                        composed is related
         * active_id: id of the document to which the mail being composed is
                      related, or id of the message to which user is replying,
                      in case ``mail.compose.message.mode == 'reply'``
         * active_ids: ids of the documents to which the mail being composed is
                      related, in case ``mail.compose.message.mode == 'mass_mail'``.
    """

    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context={}):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'sped.documento':
            doc_obj = self.pool.get('sped.documento').browse(cr, uid, res_id)

            #
            # Verificamos se tem modelo pré-definido
            #
            template_pool = self.pool.get('email.template')
            template_ids = template_pool.search(cr, 1, [('name', '=', 'NF emitida'), ('model_id.model', '=', 'sped.documento')])

            if template_ids:
                dados = template_pool.generate_email(cr, 1, template_ids[0], doc_obj.id, context=context)
                dados.update({
                    'email_to': doc_obj.partner_id.email_nfe or '',
                })

                if 'attachment_ids' in dados:
                    del dados['attachment_ids']

                res.update(dados)

            else:
                res['email_to'] = doc_obj.partner_id.email_nfe or ''
                res['subject'] = u'Envio de nossa NF-e',

        return res


mail_compose_message()
