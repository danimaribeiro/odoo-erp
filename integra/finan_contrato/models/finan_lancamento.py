# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from time import time
from mako.template import Template
from copy import copy
from pybrasil.valor.decimal import Decimal as D



class finan_lancamento(osv.Model):
    _description = u'Lançamentos'
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    def _get_valor_faturamento_eventual(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            valor = D(lancamento_obj.valor_documento)

            if lancamento_obj.contrato_id:
                for produto_contrato_obj in lancamento_obj.contrato_id.contrato_produto_ids:
                    if (not produto_contrato_obj.data) or produto_contrato_obj.data[:7] != lancamento_obj.data_vencimento_original[:7]:
                        continue

                    valor += D(produto_contrato_obj.vr_total or 0)

            res[lancamento_obj.id] = valor

        return res

    _columns = {
        'numero_documento_original': fields.char(u'Número da parcela', size=30, select=True),
        'data_vencimento_original': fields.date(u'Vencimento original', select=True),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'exige_contrato': fields.related('conta_id', 'exige_contrato', type='boolean', relation='finan.conta', string=u'Exige contrato no rateio?', store=False),
        'contrato_produto_ids': fields.related('contrato_id', 'contrato_produto_ids', type='one2many', relation='finan.contrato_produto', string=u'Produtos e serviços', store=False),
        'municipio_id': fields.related('contrato_id', 'municipio_id', type='many2one', relation='sped.municipio', string=u'Município do fato gerador'),
        'operacao_fiscal_produto_id': fields.related('contrato_id', 'operacao_fiscal_produto_id', type='many2one', relation='sped.operacao', string=u'Operação fiscal para produtos'),
        'operacao_fiscal_servico_id': fields.related('contrato_id', 'operacao_fiscal_servico_id', type='many2one', relation='sped.operacao', string=u'Operação fiscal para serviços'),
        'sped_documento_id': fields.many2one('sped.documento', u'Nota Fiscal'),
        'nf_numero': fields.related('sped_documento_id', 'numero', type='integer', string=u'Nº NF'),
        'nf_data': fields.related('sped_documento_id', 'data_emissao', type='datetime', string=u'Data NF'),
        'nf_valor': fields.related('sped_documento_id', 'vr_nf', type='float', string=u'Valor NF'),
        'rps_numero': fields.related('sped_documento_id', 'numero_rps', type='integer', string=u'Nº NF'),
        'rps_data': fields.related('sped_documento_id', 'data_emissao_rps', type='datetime', string=u'Data RPS'),
        'valor_original_contrato': fields.float(u'Valor original do contrato'),
        'valor_faturamento_eventual': fields.function(_get_valor_faturamento_eventual, type='float', string='Valor a faturar'),
        'parcelamento_ids': fields.one2many('finan.contrato', 'lancamento_parcelado_id', u'Parcelamento'),
    }

    def onchange_conta_id(self, cr, uid, ids, conta_id, company_id, centrocusto_id, valor_documento, valor, partner_id=False, data_vencimento=False, data_documento=False):
        res = super(finan_lancamento, self).onchange_conta_id(cr, uid, ids, conta_id, company_id, centrocusto_id, valor_documento, valor, partner_id, data_vencimento, data_documento)

        valores = res['value']
        conta_id = conta_id or False

        if conta_id:
            conta_obj = self.pool.get('finan.conta').browse(cr, uid, conta_id)
            valores['exige_centro_custo'] = conta_obj.exige_centro_custo
            valores['exige_contrato'] = conta_obj.exige_contrato

        return res

    def gerar_parcelamento(self, cr, uid, ids, context=None):
        if ids:
            lancamento_id = ids[0]

        if not lancamento_id:
            return

        try:
            lancamento_obj = self.browse(cr, uid, lancamento_id)
        except:
            raise osv.except_osv(u'Atenção!', u'Você precisa salvar o lançamento antes de fazer o parcelamento!')

        dados = {
            'company_id': lancamento_obj.company_id.id,
            'numero': lancamento_obj.numero_documento,
            'ativo': False,
            'partner_id': lancamento_obj.partner_id.id,
            'data_assinatura': lancamento_obj.data_vencimento,
            'data_inicio': lancamento_obj.data_vencimento,
            'tipo_valor_base': 'T',
            'valor': lancamento_obj.valor_documento,
            'documento_id': lancamento_obj.documento_id.id,
            'conta_id': lancamento_obj.conta_id.id,
            'provisionado': False,

            'res_partner_address_id': lancamento_obj.res_partner_address_id and lancamento_obj.res_partner_address_id.id,
            'centrocusto_id': lancamento_obj.centrocusto_id and lancamento_obj.centrocusto_id.id,
            'carteira_id': lancamento_obj.carteira_id and lancamento_obj.carteira_id.id,
            'lancamento_parcelado_id': lancamento_obj.id,
        }

        if getattr(lancamento_obj, 'sugestao_bank_id', False):
            dados['res_partner_bank_id'] = lancamento_obj.sugestao_bank_id.id
        elif getattr(lancamento_obj, 'res_partner_bank_id', False):
            dados['res_partner_bank_id'] = lancamento_obj.res_partner_bank_id.id

        if lancamento_obj.tipo == 'R':
            dados['natureza'] = 'RP'
            view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'finan_contrato', 'finan_parcelamento_receber_wizard')[1]
        else:
            dados['natureza'] = 'PP'
            view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'finan_contrato', 'finan_parcelamento_pagar_wizard')[1]

        contrato_ids = self.pool.get('finan.contrato').search(cr, uid, [('lancamento_parcelado_id', '=', lancamento_obj.id)])

        if len(contrato_ids):
            contrato_id = contrato_ids[0]
        else:
            contrato_id = self.pool.get('finan.contrato').create(cr, uid, dados)

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Parcelamento',
            'res_model': 'finan.contrato',
            'res_id': contrato_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'lancamento_id': lancamento_obj.id},
        }

        return retorno

    #def onchange_centrocusto_id(self, cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, context={}):
        #res = super(finan_lancamento, self).onchange_centrocusto_id(cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, context=context)
        #valores = res['value']

        #if centrocusto_id:
            #valor_documento = valor_documento or 0
            #valor = valor or 0

            #centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)
            #rateio_ids = valores['rateio_ids']

            #i = 0
            #for rateio_obj in centrocusto_obj.rateio_ids:
                #if rateio_obj.contrato_id:
                    #rateio_ids[i][2]['contrato_id'] = rateio_obj.contrato_id.id
                #i += 1

        #return res

    def gera_nfse(self, cr, uid, ids):
        res = {}
        documento_pool = self.pool.get('sped.documento')

        for lancamento_obj in self.browse(cr, uid, ids):
            ini = time()
            if not lancamento_obj.contrato_id:
                raise osv.except_osv(u'Inválido!', u'Lançamento não vinculado a um contrato!')

            if not lancamento_obj.contrato_id.operacao_fiscal_servico_id:
                raise osv.except_osv(u'Inválido!', u'O contrato nº ' + lancamento_obj.contrato_id.numero + ' não tem a operação fiscal definida!')

            contrato_obj = lancamento_obj.contrato_id
            operacao_obj = contrato_obj.operacao_fiscal_servico_id
            if contrato_obj.municipio_id:
                municipio_id = contrato_obj.municipio_id.id
            else:
                municipio_id = False

            dados = {
                'emissao': '0',
                'company_id': contrato_obj.company_id.id,
                'partner_id': contrato_obj.partner_id.id,
                'operacao_id': operacao_obj.id,
                'municipio_fato_gerador_id': municipio_id,
                'finan_contrato_id': contrato_obj.id,
                'finan_lancamento_id': lancamento_obj.id,
                'finan_documento_id': contrato_obj.documento_id.id,
                'finan_conta_id': contrato_obj.conta_id.id,
                'modelo': operacao_obj.modelo,
            }

            if operacao_obj.modelo == 'SE':
                dados['ambiente_nfe'] = contrato_obj.company_id.ambiente_nfse or '2'

            if contrato_obj.centrocusto_id:
                dados['finan_centrocusto_id'] = contrato_obj.centrocusto_id.id

            if contrato_obj.res_partner_bank_id:
                dados['res_partner_bank_id'] = contrato_obj.res_partner_bank_id.id

            if contrato_obj.carteira_id:
                dados['finan_carteira_id'] = contrato_obj.carteira_id.id

            #
            # Gera o registro da NFS-e
            #
            contexto_nota = {
                'modelo': operacao_obj.modelo,
                'default_modelo': operacao_obj.modelo,
                'company_id': contrato_obj.company_id.id,
                'default_company_id': contrato_obj.company_id.id,
                'emissao': '0',
                'default_emissao': '0',
            }

            if operacao_obj.modelo == 'SE':
                contexto_nota['default_ambiente_nfe'] = contrato_obj.company_id.ambiente_nfse or '2'
                contexto_nota['ambiente_nfe'] = contrato_obj.company_id.ambiente_nfse or '2'

            dados['numero'] = documento_pool._get_numero_padrao(cr, uid, context=contexto_nota)

            nfse_id = documento_pool.create(cr, uid, dados, context=contexto_nota)
            nfse_obj = documento_pool.browse(cr, uid, nfse_id)

            dados_operacao = nfse_obj.onchange_operacao(operacao_obj.id)
            dados_operacao['finan_conta_id'] = lancamento_obj.conta_id.id
            nfse_obj.write(dados_operacao['value'], context={'nao_calcula': True})

            if contrato_obj.obs:
                template_imports = [
                    'from pybrasil.base import (tira_acentos, primeira_maiuscula)',
                    'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
                    'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade)',
                ]
                if nfse_obj.infcomplementar:
                    template = Template(nfse_obj.infcomplementar.encode('utf-8') + '\n' + contrato_obj.obs.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8')
                else:
                    template = Template(contrato_obj.obs.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8')

                infcomplementar = template.render(nfse=nfse_obj, lancamento=lancamento_obj, contrato=lancamento_obj.contrato_id, nf=nfse_obj, doc_obj=nfse_obj, data_vencimento=lancamento_obj.data_vencimento)
                nfse_obj.write({'infcomplementar': infcomplementar}, context={'nao_calcula': True})

            dados['entrada_saida'] = nfse_obj.entrada_saida
            dados['regime_tributario'] = nfse_obj.regime_tributario
            dados['emissao'] = nfse_obj.emissao
            dados['data_emissao'] = nfse_obj.data_emissao
            contexto_item = copy(dados)

            for chave in dados:
                if 'default_' not in chave:
                    contexto_item['default_' + chave] = contexto_item[chave]

            #
            # Adiciona os produtos
            # Considera o pro-rata na geração dos itens
            #
            proporcao = D(lancamento_obj.valor_documento) / D(contrato_obj.valor_faturamento)
            produtos = {}
            for produto_contrato_obj in contrato_obj.contrato_produto_ids:

                if produto_contrato_obj.data and produto_contrato_obj.data[:7] != lancamento_obj.data_vencimento[:7]:
                    continue

                produto_obj = produto_contrato_obj.product_id

                if produto_obj.id in produtos:
                    item_id = produtos[produto_obj.id]
                    item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)

                    if produto_contrato_obj.data:
                        item_obj.vr_produtos += (produto_contrato_obj.quantidade * produto_contrato_obj.vr_unitario)
                        item_obj.quantidade += D(produto_contrato_obj.quantidade or 0)
                    else:
                        item_obj.vr_produtos += (produto_contrato_obj.quantidade * produto_contrato_obj.vr_unitario) * proporcao
                        item_obj.quantidade += D(produto_contrato_obj.quantidade or 0) * proporcao
                    #if produto_contrato_obj.data:
                        #item_obj.vr_unitario += produto_contrato_obj.vr_unitario
                    #else:
                        #item_obj.vr_unitario += produto_contrato_obj.vr_unitario * proporcao

                    item_obj.vr_unitario = D(item_obj.vr_produtos or 0) / D(item_obj.quantidade or 1)

                else:
                    dados = {
                        'documento_id': nfse_obj.id,
                        'produto_id': produto_obj.id,
                        'quantidade': produto_contrato_obj.quantidade,
                    }

                    if produto_contrato_obj.data:
                        dados['vr_unitario'] = produto_contrato_obj.vr_unitario
                    else:
                        dados['vr_unitario'] = produto_contrato_obj.vr_unitario * proporcao
                    item_id = self.pool.get('sped.documentoitem').create(cr, uid, dados, context=contexto_item)
                    produtos[produto_obj.id] = item_id
                    item_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_id)
                    dados_item = item_obj.onchange_produto(produto_obj.id, context=contexto_item)
                    item_obj.write(dados_item['value'])

                dados_item = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                item_obj.write(dados_item['value'])

            recalculo = nfse_obj.recalculo or 0
            nfse_obj.write({'recalculo': recalculo + 1}, context={'gera_do_contrato': True})
            nfse_obj = documento_pool.browse(cr, uid, nfse_obj.id)
            lancamento_obj.write({'sped_documento_id': nfse_obj.id, 'valor_documento': nfse_obj.vr_fatura, 'provisionado': False, 'data_documento': nfse_obj.data_emissao[:10] })

            if nfse_obj.modelo == 'RL':
                lancamento_obj.write({'numero_documento': str(nfse_obj.numero)})

                if lancamento_obj.carteira_id:
                    lancamento_obj.gerar_boleto()

        return res


finan_lancamento()


class finan_lancamento_rateio(osv.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.lancamento.rateio'
    _inherit = 'finan.lancamento.rateio'

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', select=True, ondelete='restrict'),
        #'conta_id': fields.related('lancamento_id', 'conta_id', type='many2one', relation='finan.conta', string=u'Exige contrato no rateio?', store=False),
        #'exige_contrato': fields.related('conta_id', 'exige_contrato', type='boolean', relation='finan.conta', string=u'Exige contrato no rateio?', store=False),
    }

    #_sql_constraints = [
        #('rateio_centrocusto_unique', 'unique(lancamento_id, centrocusto_id, contrato_id)',
            #u'Não é permitido repetir um mesmo centro de custo!'),
    #]


finan_lancamento_rateio()
