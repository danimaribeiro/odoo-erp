# -*- encoding: utf-8 -*-

from osv import osv, fields
import base64
from pybrasil.valor.decimal import Decimal as D
from copy import copy
from finan.wizard.finan_relatorio import Report
import os


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


TIPO_SEPARACAO = [
    ('out', u'Envio de mercadorias'),
    ('in', u'Recebimento de mercadorias'),
    ('internal', u'Movimentação interna'),
    ('transf', u'Transferência'),
    ('invcli', u'Inventário em cliente'),
]


class stock_picking(osv.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        #'sped_documento_id': fields.many2one('sped.documento', u'Nota Fiscal'),
        'sped_documento_ids': fields.one2many('sped.documento', 'stock_picking_id', u'Notas Fiscais'),
        'type': fields.selection(TIPO_SEPARACAO, u'Tipo', required=True, select=True),
        'familiatributaria_ids': fields.many2many('sped.familiatributaria', 'stock_operacao_familiatributaria', 'picking_id', 'familiatributaria_id', u'Famílias tributárias'),
    }

    def write(self, cr, uid, ids, dados, context={}):
        res = super(stock_picking, self).write(cr, uid, ids, dados, context=context)

        cr.execute("update stock_picking set name = to_char(id, '999G000G000') where name is null;")

        return res

    def imprime_pedido_transferencia(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        picking_obj = self.browse(cr, uid, id)

        rel = Report('Romaneio de Ordem de Entrega', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_movimento_almoxarifado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['ROMANEIO'] = '%'
        rel.parametros['UID'] = uid

        rel.parametros['TITULO'] = u'PEDIDO DE TRANSFERÊNCIA ' + picking_obj.name

        nome_relatorio = u'ped_transf_' + picking_obj.name + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'stock.picking'), ('res_id', '=', id), ('name', '=', nome_relatorio)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_relatorio,
            'datas_fname': nome_relatorio,
            'res_model': 'stock.picking',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def gerar_nota_transferencia(self, cr, uid, ids, context={}):
        res = {}
        nf_pool = self.pool.get('sped.documento')
        item_pool = self.pool.get('sped.documentoitem')

        for transf_obj in self.browse(cr, uid, ids):
            #if transf_obj.state != 'done':
                #raise osv.except_osv(u'Erro!', u'Não é permitido gerar a nota de transferência antes de concluir o pedido de transferência!')

            if not transf_obj.operacao_id.sped_operacao_id:
                raise osv.except_osv(u'Erro!', u'Não é possível gerar a nota de transferência, operação fiscal não configurada!')

            #if transf_obj.sped_documento_id:
                #raise osv.except_osv(u'Erro!', u'Não é possível gerar a nota de transferência, uma nota já foi gerada!')

            romaneio_a_emitir = False
            for transf_item_obj in transf_obj.move_lines:
                if not transf_item_obj.romaneio:
                    continue

                #
                # Já existe nota pra esse romaneio?
                #
                nf_ids = nf_pool.search(cr, uid, [('stock_picking_id', '=', transf_obj.id), ('stock_romaneio', '=', transf_item_obj.romaneio)])

                if nf_ids:
                    continue

                romaneio_a_emitir = transf_item_obj.romaneio

            if not romaneio_a_emitir:
                continue

            dados_nota = {
                'modelo': '55',
                'company_id': transf_obj.operacao_id.remetente_id.id,
                'partner_id': transf_obj.company_id.partner_id.id,
                'operacao_id': transf_obj.operacao_id.sped_operacao_id.id,
                'stock_picking_id': transf_obj.id,
                'stock_romaneio': romaneio_a_emitir,
            }

            nota_id = nf_pool.create(cr, uid, dados_nota, context={'modelo': '55', 'default_modelo': '55'})
            nota_obj = nf_pool.browse(cr, uid, nota_id)
            dados_operacao = nota_obj.onchange_operacao(transf_obj.operacao_id.sped_operacao_id.id)
            nota_obj.write(dados_operacao['value'])
            dados_nota.update(dados_operacao['value'])

            contexto_item = copy(dados_nota)
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

            for transf_item_obj in transf_obj.move_lines:
                if transf_item_obj.romaneio != romaneio_a_emitir:
                    continue

                dados = {
                    'documento_id': nota_obj.id,
                    'produto_id': transf_item_obj.product_id.id,
                    'quantidade': transf_item_obj.product_qty,
                    'stock_move_id': transf_item_obj.id,
                    'stock_location_id': transf_item_obj.location_id.id,
                    'stock_location_dist_id': transf_item_obj.location_dest_id.id,
                }

                item_id = item_pool.create(cr, uid, dados, contexto_item)
                item_obj = item_pool.browse(cr, uid, item_id)
                dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)
                item_obj.write(dados_item['value'])
                item_obj = item_pool.browse(cr, uid, item_id)

                dados_item = item_pool.onchange_calcula_item(cr, uid, False, item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
                item_obj.write(dados_item['value'])

            nota_obj.ajusta_impostos_retidos()


stock_picking()
