# -*- coding: utf-8 -*-

from osv import osv, fields
import os
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.valor.decimal import Decimal as D
from pybrasil.base import DicionarioBrasil

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

STORE_ITEM = {
    'project.orcamento.item': (
        lambda item_pool, cr, uid, ids, context={}: [item_obj.orcamento_id.id for item_obj in item_pool.browse(cr, uid, ids)],
        ['vr_risco'],
        10  #  Prioridade
    ),
}


class project_orcamento(osv.Model):
    _name = 'project.orcamento'
    _inherit = 'project.orcamento'
    _order = 'ano desc, mes desc, versao desc'

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for orc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            for item_obj in orc_obj.item_ids:
                soma += D(str(getattr(item_obj, nome_campo, 0)))

            soma = soma.quantize(D('0.01'))

            res[orc_obj.id] = soma

        return res

    _columns = {
        #'versao': fields.char(u'Versão', size=60, select=True),
        'crm_lead_id': fields.many2one('crm.lead', u'Oportunidade'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'vr_risco': fields.function(_get_soma_funcao, type='float', string=u'Valor de Venda produtos/serviços', store=STORE_ITEM, digits=(18, 2)),
        'sale_order_id': fields.many2one('sale.order', u'Pedido de Venda'),
        'sale_order_id': fields.many2one('sale.order', u'Pedido de Venda'),  
        'just_cancelamento': fields.text(u'Justificativa do Cancelamento'),  
    }

    #_defaults = {
        #'versao': lambda self, cr, uid, ids: fields.date.today()[:4] + '-' + str(len(self.pool.get('project.orcamento').search(cr, uid, [('versao', 'ilike', fields.date.today()[:4] + '-')])) + 1).zfill(4),
    #}

    def atualiza_valor_componentes(self, cr, uid, item_obj, dados, context={}):
        pass

    def imprime_orcamento(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Orçamento do Projeto', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'ms_redes_orcamento_projeto.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.outputFormat = 'rtf'

        if rel_obj.versao:
            nome = 'ORC_' + rel_obj.versao + '.doc'
        else:
            nome = 'ORC_SEM_VERSAO.doc'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.orcamento'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'project.orcamento',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def ajusta_oportunidade(self, cr, uid, ids, context={}):
        for orcamento_obj in self.pool.get('project.orcamento').browse(cr, uid, ids, context=context):
            if not orcamento_obj.crm_lead_id:
                continue

            cr.execute("update crm_lead set planned_revenue = {valor} where id = {id};".format(id=orcamento_obj.crm_lead_id.id, valor=D(orcamento_obj.vr_risco or 0)))

    def create(self, cr, uid, dados, context={}):
        res = super(project_orcamento, self).create(cr, uid, dados, context=context)

        self.ajusta_oportunidade(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(project_orcamento, self).write(cr, uid, ids, dados, context=context)

        self.ajusta_oportunidade(cr, uid, ids, context=context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        self.ajusta_oportunidade(cr, uid, ids, context=context)

        res = super(project_orcamento, self).unlink(cr, uid, ids, context=context)

        return res

    def gerar_pedido_venda(self, cr, uid, ids, context={}):
        res = {}

        venda_pool = self.pool.get('sale.order')
        item_pool = self.pool.get('sale.order.line')

        for orcamento_obj in self.browse(cr, uid, ids):
            complemento = venda_pool.onchange_partner_id(cr, uid, False, orcamento_obj.partner_id.id)

            dados = complemento['value']

            dados.update({
                'company_id': orcamento_obj.project_id.company_id.id,
                'project_id': orcamento_obj.project_id.id,
                'partner_id': orcamento_obj.partner_id.id,
                'orcamento_id': orcamento_obj.id,
                'note': orcamento_obj.obs,
                'pricelist_id': 1,
            })
            del dados['tipo_pessoa']
            venda_id = venda_pool.create(cr, uid, dados)
            venda_obj = venda_pool.browse(cr, uid, venda_id)

            for item_obj in orcamento_obj.item_ids:

                filtro = {
                    'partner_id': venda_obj.partner_id.id,
                    'quantity': item_obj.quantidade,
                    'pricelist': venda_obj.pricelist_id.id,
                    'price_unit': item_obj.vr_unitario_risco,
                    'force_product_uom': True,
                    'operacao_fiscal_produto_id': venda_obj.operacao_fiscal_produto_id.id,
                    'operacao_fiscal_servico_id': venda_obj.operacao_fiscal_servico_id.id,
                    'company_id': venda_obj.company_id.id
                }
                if item_obj.vr_unitario_risco:
                    valor_unitario = item_obj.vr_unitario_risco
                    filtro['price_unit'] = valor_unitario
                else:
                    valor_unitario = item_obj.vr_risco / item_obj.quantidade
                    filtro['price_unit'] = valor_unitario

                complemento = item_pool.product_id_change(cr, uid, False, venda_obj.pricelist_id.id, item_obj.product_id.id, item_obj.quantidade, False, 0, False,False,orcamento_obj.partner_id.id, False, False,venda_obj.date_order, False, False, False, context=filtro)

                complemento['value'].update({
                    'order_id': venda_obj.id,
                    'product_id': item_obj.product_id.id,
                    'product_qty': item_obj.quantidade,
                    'vr_unitario_base': item_obj.vr_unitario,
                    'risco': item_obj.risco,
                    'price_unit': valor_unitario,
                    'orcamento_item_id': item_obj.id,
                    'name': item_obj.product_id.name,
                })

                dados = {}
                for chave in complemento['value']:
                    if not isinstance(complemento['value'][chave], DicionarioBrasil):
                        dados[chave] = complemento['value'][chave]

                item_id = item_pool.create(cr, uid, dados)

                item_obj.write({'sale_item_id': item_id })

            orcamento_obj.write({'sale_order_id': venda_id })
            
        return True        
    
    def cancela_orcamento(self, cr, uid, ids, context={}):
        for orc_obj in self.browse(cr, uid, ids):
            if orc_obj.situacao == 'A':
                raise osv.except_osv(u'Erro!', u'Não é permitido cancelar um orçamento aprovado!')
            
            elif not orc_obj.just_cancelamento:
                raise osv.except_osv(u'Atenção!', u'Justificar o Cancelamento!')
                

            orc_obj.write({'situacao': 'C'})

            cr.execute("update project_orcamento_item set situacao = 'C' where orcamento_id = " + str(orc_obj.id) + ";")

        return ids

project_orcamento()
