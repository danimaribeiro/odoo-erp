# -*- coding: utf-8 -*-

from osv import fields, osv
from integra_rh.models.hr_payslip_input import mes_atual, primeiro_ultimo_dia_mes
from copy import copy
import random


class ordem_servico_gera_nota(osv.osv_memory):
    _name = 'ordem.servico.gera_nota'
    _description = u'Gerar notas fiscais'

    def _get_os_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        gera_nota_obj = self.browse(cr, uid, ids[0])

        sql = '''
        select distinct
            os.id

        from
            ordem_servico os
            -- left join sped_documentoitem di on di.os_id = os.id

        where
            os.data between '{data_inicial}' and '{data_final}'
        '''

        filtro = {
            'data_inicial': gera_nota_obj.data_inicial,
            'data_final': gera_nota_obj.data_final,
            'etapa_id': gera_nota_obj.etapa_id.id,
        }

        if gera_nota_obj.etapa_id:
            sql += '''
            and os.etapa_id = {etapa_id}
            '''
            filtro['etapa_id'] = gera_nota_obj.etapa_id.id

        if gera_nota_obj.marca_id:
            sql += '''
            and os.marca ilike '%{marca}%'
            '''
            filtro['marca'] = gera_nota_obj.marca_id.name

        if gera_nota_obj.os_id:
            sql += '''
            and os.id = {os_id}
            '''
            filtro['os_id'] = gera_nota_obj.os_id.id

        sql = sql.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        os_ids = []
        for os_id, in dados:
            os_ids.append(os_id)

        res = {}
        if ids:
            for id in ids:
                res[id] = os_ids
        else:
            res = os_ids

        return res

    _columns = {
        'data_inicial': fields.date('Data inicial'),
        'data_final': fields.date('Data final'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'marca_id': fields.many2one('res.partner', u'Marca'),
        'etapa_id': fields.many2one('ordem.servico.etapa', u'Etapa'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'operacao_id': fields.many2one('sped.operacao', u'Operação Fiscal'),
        'operacao_produto_id': fields.many2one('sped.operacao', u'Operação fiscal para produtos'),
        'operacao_servico_id': fields.many2one('sped.operacao', u'Operação fiscal para serviços'),
        'os_id': fields.many2one('ordem.servico', u'OS'),
        'os_ids': fields.function(_get_os_ids, method=True, type='one2many', string=u'OSs', relation='ordem.servico'),
    }

    #def onchange_get_operacao_produto_id(self, cr, uid, ids, context={}):
        #if 'company_id' in context:
            #company_id = context['company_id']
        #else:
            #company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context),

        #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        #if company_obj.operacao_id:
            #return company_obj.operacao_id.id

    #def onchange_get_operacao_servico_id(self, cr, uid, ids, context={}):
        #if 'company_id' in context:
            #company_id = context['company_id']
        #else:
            #company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context),

        #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        #if company_obj.operacao_servico_id:
            #return company_obj.operacao_servico_id.id

    _defaults = {
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[1],
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context=c),
        #'operacao_produto_id': onchange_get_operacao_produto_id,
        #'operacao_servico_id': onchange_get_operacao_servico_id,
    }

    def gera_notas(self, cr, uid, ids, context=None):
        gera_nota_obj = self.browse(cr, uid, ids[0])

        if not gera_nota_obj.partner_id:
            raise osv.except_osv(u'Inválido!', u'Para gerar a NF, é preciso selecionar o destinatário!')

        if not gera_nota_obj.company_id:
            raise osv.except_osv(u'Inválido!', u'Para gerar a NF, é preciso selecionar a empresa para a emissão das NFs!')

        if not gera_nota_obj.operacao_id:
            raise osv.except_osv(u'Inválido!', u'Para gerar a NF, é preciso selecionar a operação fiscal!')

        if not gera_nota_obj.os_ids:
            raise osv.except_osv(u'Inválido!', u'Para gerar a NF, é preciso ter pelo menos uma OS selecionada!')

        documento_pool = self.pool.get('sped.documento')
        documento_item_pool = self.pool.get('sped.documentoitem')

        dados = {
            'company_id': gera_nota_obj.company_id.id,
            'partner_id': gera_nota_obj.partner_id.id,
            'operacao_id': gera_nota_obj.operacao_id.id,
        }

        nota_id = documento_pool.create(cr, uid, dados, context={'modelo': gera_nota_obj.operacao_id.modelo, 'default_modelo': gera_nota_obj.operacao_id.modelo})
        nota_obj = documento_pool.browse(cr, uid, nota_id)
        dados_operacao = nota_obj.onchange_operacao(gera_nota_obj.operacao_id.id)
        nota_obj.write(dados_operacao['value'])

        contexto_item = copy(dados)
        for chave in dados:
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

        for os_obj in gera_nota_obj.os_ids:
            dados = {
                'documento_id': nota_obj.id,
                'produto_id': os_obj.product_id.id,
                'quantidade': 1,
                'quantidade_tributacao': 1,
                'modelo': nota_obj.modelo,
                'os_id': os_obj.id,
            }

            if os_obj.numero_serie_id:
                dados['numero_serie_ids'] = [os_obj.numero_serie_id.id]

            item_id = documento_item_pool.create(cr, uid, dados, context=contexto_item)
            item_obj = documento_item_pool.browse(cr, uid, item_id)

            dados_item = documento_item_pool.onchange_produto(cr, uid, False, os_obj.product_id.id, context=contexto_item)
            item_obj.write(dados_item['value'])
            item_obj = documento_item_pool.browse(cr, uid, item_id)

            #
            # Valor unitário é o valor da última compra
            #
            produto_obj = self.pool.get('product.product').browse(cr, uid, os_obj.product_id.id)
            item_obj.vr_unitario = getattr(produto_obj, 'custo_ultima_compra_asp', produto_obj.standard_price or 1)

            dados_item = documento_item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
            item_obj.write(dados_item['value'])

        nota_obj.write({'recalculo': int(random.random() * 100000000)})

        #
        # Agora que a nota foi gerada, muda a etapa das OSs
        #
        if gera_nota_obj.operacao_id.ordem_servico_etapa_id:
            for os_obj in gera_nota_obj.os_ids:
                print('mudando etapa')
                print(gera_nota_obj.operacao_id.ordem_servico_etapa_id)
                print(os_obj.id)
                os_obj.write({'etapa_id': gera_nota_obj.operacao_id.ordem_servico_etapa_id.id, 'proxima_etapa_id':'' })


    def busca_oss(self, cr, uid, ids, context={}):
        #valores = {}
        #retorno = {'value': valores}

        os_ids = self._get_os_ids(cr, uid, ids, 'os_ids', context=context)

        return self.write(cr, uid, ids, {'os_ids': os_ids})

    def onchange_marca_id(self, cr, uid, ids, marca_id, context={}):
        if not marca_id:
            return {}

        marca_obj = self.pool.get('res.partner').browse(cr, uid, marca_id)

        res = {}
        valores = {}
        res['value'] = valores

        if marca_obj.assistencia_tecnica_id:
            valores['partner_id'] = marca_obj.assistencia_tecnica_id.id
        else:
            valores['partner_id'] = marca_obj.id

        return res

ordem_servico_gera_nota()
