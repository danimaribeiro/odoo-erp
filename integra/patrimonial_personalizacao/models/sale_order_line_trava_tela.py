# -*- encoding: utf-8 -*-


from osv import osv, fields


CAMPOS_TELA = [
    'vr_unitario_custo',
    'vr_total_custo',
    'vr_unitario_minimo',
    'vr_total_minimo',
    'vr_unitario_venda_impostos',
    'vr_total_venda_impostos',
    'vr_comissao',
]


class sale_order_line(osv.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    
    def _valor_tela(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        
        for item_obj in self.pool.get('sale.order.line').browse(cr, uid, ids):
            nome_campo = nome_campo.replace('tela_', '')
            
            res[item_obj.id] = getattr(item_obj, nome_campo, False)
            
        return res

    _columns = {
        'tela_vr_unitario_custo': fields.function(_valor_tela, type='float', string=u'Unitário de custo'),
        'tela_vr_total_custo': fields.function(_valor_tela, type='float', string=u'Valor de custo'),
        'tela_vr_unitario_minimo': fields.function(_valor_tela, type='float', string=u'Unitário mínimo'),
        'tela_vr_total_minimo': fields.function(_valor_tela, type='float', string=u'Valor total mínimo'),
        'tela_vr_unitario_venda_impostos': fields.function(_valor_tela, type='float', string=u'Unitário venda'),
        'tela_vr_total_venda_impostos': fields.function(_valor_tela, type='float', string=u'Total venda'),
        'tela_vr_comissao': fields.function(_valor_tela, type='float', string=u'Comissão'),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context=context)
        
        if 'value' in res:
            for campo in CAMPOS_TELA:
                if campo in res['value']:
                    res['value']['tela_' + campo] = res['value'][campo]
            
        return res

    def on_change_quantidade_margem_desconto(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, vr_unitario_custo=0, vr_unitario_minimo=0, vr_unitario_venda=0, margem=0, desconto=0, autoinsert=False, mudou_quantidade=False, usa_unitario_minimo=False, context={}, desconto_direto=False, margem_direta=False):
        res = super(sale_order_line, self).on_change_quantidade_margem_desconto(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, desconto, autoinsert, mudou_quantidade, usa_unitario_minimo, context, desconto_direto, margem_direta)

        if 'value' in res:
            for campo in CAMPOS_TELA:
                if campo in res['value']:
                    res['value']['tela_' + campo] = res['value'][campo]
            
        return res


sale_order_line()
