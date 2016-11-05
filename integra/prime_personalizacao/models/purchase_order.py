# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
import os
import base64
from osv import osv, fields
from finan.wizard.finan_relatorio import Report
from decimal import Decimal as D

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

class purchase_order(osv.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    
    def imprime_ordem_compra(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        
        sql = """    
            SELECT
                 ----Dados da empresa
                 comp.name AS empresa_nome,
                 orc.date_order  as data_pv,
                 orc.name as numero_pv,
                 partcomp.endereco AS empresa_endereco,
                 partcomp.numero AS empresa_numero,
                 partcomp.complemento AS empresa_complemento,
                 partcomp.bairro AS empresa_bairro,
                 partcomp.cidade AS empresa_municipio,
                 partcomp.estado AS empresa_estado,
                 partcomp.cep AS empresa_cep,
                 partcomp.cnpj_cpf AS empresa_cnpj,
                 partcomp.ie AS empresa_ie,
                 partcomp.fone as empresa_fone,
                 cast(comp.photo as varchar) as photo,
            
                 ----Dados do cliente--
                 partpart.name AS cliente_nome,
                 partpart.fantasia AS cliente_fantasia,
                 partpart.endereco AS cliente_endereco,
                 partpart.numero AS cliente_numero,
                 partpart.complemento AS cliente_complemento,
                 partpart.bairro AS cliente_bairro,
                 partpart.cidade AS cliente_municipio,
                 partpart.estado AS cliente_estado,
                 partpart.cep AS cliente_cep,
                 partpart.cnpj_cpf AS cliente_cnpj_cpf,
                 partpart.ie AS cliente_ie_rg,
                 partpart.fone AS cliente_fone,
                 partpart.ie as cliente_ie,
                 rpd.name as contato,
                 rpd.phone as contato_fone,
                 coalesce((select compra.email from res_partner_address compra where compra.partner_id = partpart.id and type in ('purchase', 'compras') and compra.email is not null limit 1), '') as contato_email,
            
                 partcomp.fone AS empresa_fone,
                 prod.name_template AS orcamento_item_produto,
                 prod.default_code AS orcamento_item_produto_codigo,
                 um.name as orcamento_item_produto_unidade,
                 oi.product_qty as produto_quantidade,
                 oi.price_unit as valor_unitário,
                 cast(comp.logo as varchar) as logo,
                 prod.name_template,
                 orc.id as purchase_id,
                 case
                    when orc.obs_custo_despesa = 'A' then 'Aplicação do material: Ativo imobilizado; ' || coalesce(orc.notes, '')
                    when orc.obs_custo_despesa = 'M' then 'Aplicação do material: Material aplicado; ' || coalesce(orc.notes, '')
                    else orc.notes
                 end as observacao,
                 orc.obs_fornecedor,
                 restrap.name as transportadora,
                 case
                 when orc.modalidade_frete = '0' then 'DO EMITENTE'
                 when orc.modalidade_frete = '1' then 'DO DESTINATÁRIO'
                 when orc.modalidade_frete = '2' then 'DE TERCEIROS'
                 when orc.modalidade_frete = '9' then 'SEM FRETE'
                 end
                 as modalidade_frete,
                 ff.nome as forma_pagamento,
                 apt.name as condicao_pagamento,
                 coalesce(orc.vr_ipi, 0) as total_ipi,
                 coalesce(orc.vr_st, 0) as total_st,
                 coalesce(orc.vr_desconto, 0) as desconto_global,
                 formata_valor(coalesce(orc.al_desconto, 0)) || '%' as al_desconto_global,
                 coalesce(orc.vr_frete, 0) as valor_frete,
                 coalesce(orc.amount_total, 0) as total_pedido,
                 oi.bc_ipi as base_ipi_produto,
                 oi.al_ipi as aliquota_ipi_produto,
                 oi.vr_ipi as valor_ipi_produto,
                 oi.bc_st as base_st_produto,
                 oi.al_st as aliquota_st_produto,
                 oi.vr_st as valor_st_produto,
                 oi.vr_desconto as valor_desconto,
                 coalesce(oi.price_subtotal, 0) as total_produto,
                 sl.name as local_estoque,
                 prod.variants as marca,
                 oi.name || ' DATA DE ENTREGA ' || to_char(date_planned,'DD/MM/YYYY') as nome_produto,
                 u.name as usuario_aprovador,
                 bc.agencia as banco_agencia,
                 bc.acc_number as banco_conta,
                 bk.name as banco_nomer,
                 case
                    when u.user_email is not null then 'Email: ' || u.user_email
                    else ''
                 end as usuario_aprovador_email,
                 case
                    when u.fone is not null then 'Fone: ' || u.fone
                    else ''
                 end as usuario_aprovador_fone,
            
                 --
                 -- Ultimos precos praticados pelo fornecedor
                 --
                 coalesce(
                (select
                        'data ped. ' || to_char(po.date_order, 'dd/mm/yyyy') || ', R$ ' || formata_valor(pol.price_unit) || '; '
                from purchase_order_line pol
                join purchase_order po on po.id = pol.order_id
            
                where
                    po.state = 'done'
                    and po.partner_id = orc.partner_id
                    and po.company_id = orc.company_id
                    and pol.product_id = oi.product_id
                    and po.date_order < orc.date_order
                order by
                    po.date_order desc
                limit 1), '') as ultimo_preco,
                 coalesce(
                (select
                        'data ped. ' || to_char(po.date_order, 'dd/mm/yyyy') || ', R$ ' || formata_valor(pol.price_unit) || '; '
                from purchase_order_line pol
                join purchase_order po on po.id = pol.order_id
            
                where
                    po.state = 'done'
                    and po.partner_id = orc.partner_id
                    and po.company_id = orc.company_id
                    and pol.product_id = oi.product_id
                    and po.date_order < orc.date_order
                order by
                    po.date_order desc
                offset 1
                limit 1), '') as penultimo_preco            
            
            FROM
                 purchase_order_line as oi
                 join purchase_order as orc on orc.id = oi.order_id
                 join product_product as prod ON oi.product_id = prod.id
                 join product_template as prodtemp ON prod.product_tmpl_id = prodtemp.id
                 left join product_uom as um on um.id = prodtemp.uom_id
                 join res_company as comp ON orc.company_id = comp.id
                 join res_partner partcomp ON comp.partner_id = partcomp.id
                 join res_partner partpart on partpart.id = orc.partner_id
                 left join res_partner_address as rpd on rpd.id = orc.partner_address_id
                 left join res_partner restrap on restrap.id = orc.transportadora_id
                 left join account_payment_term as apt on apt.id = orc.payment_term_id
                 join stock_location sl on sl.id = orc.location_id
                 left join res_users u on u.id = orc.validator
                 left join finan_formapagamento ff on ff.id = orc.formapagamento_id
                 left join res_partner_bank bc on bc.id = orc.partner_bank_id
                 left join res_bank bk on bk.id = bc.bank
            where
                orc.id = {id}            
            
            ORDER BY
                 orc.id,
                 prod.name_template ASC"""
                 
        sql = sql.format(id=id)                           
        
        rel = Report('Ordem de Compra', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'ordem_compra.jrxml')
        rel.parametros['SQL'] = sql
        rel.parametros['UID'] = uid
        rel.parametros['ULTIMAS_COMPRAS'] = True

        nome = rel_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'purchase.order'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'purchase.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

purchase_order()