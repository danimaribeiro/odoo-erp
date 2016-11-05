# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields



class ordem_servico_produto(osv.Model):
    _name = 'ordem.servico.produto'
    _description = u'Ordem de Serviço Produto'
    
    def _busca_campo(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        
        for obj in self.browse(cr, uid, ids):
            valor = 0
            
            nome_campo = nome_campo.replace('func_', '')
            
            valor = getattr(obj, nome_campo, 0)
            
            res[obj.id] = valor
            
        return res        
    
    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'product_id': fields.many2one('product.product', u'Produto/Serviço'),
        'qtd': fields.float(u'quantidade'),
        'vr_unitario': fields.float(u'Valor unitário'),
        'func_vr_unitario': fields.function(_busca_campo, type='float', string=u'Valor unitário'),
        'vr_total': fields.float(u'Valor total'),            
        'func_vr_total': fields.function(_busca_campo, type='float', string=u'Valor total'),            
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ordem.servico', context=c),       
        'qtd': 0,
        'vr_unitario': 0,
        'vr_total': 0,
    }

    def onchange_product_id(self, cr, uid, ids, product_id, partner_id, company_id, context={}):
        if not product_id:
            return {}
        
        if not partner_id:
            return {}
        
        if not company_id:
            return {}
        
        order_pool = self.pool.get('sale.order')
        order_line_pool = self.pool.get('sale.order.line')
        
        #
        # Busca a lista de preços
        #
        dados = order_pool.onchange_partner_id(cr, 1, False, partner_id)
        print(partner_id)
        pricelist_id = dados['value']['pricelist_id'] or 1
        
        #
        # Busca o preço de venda
        #
        dados = order_line_pool.product_id_change(cr, uid, False, pricelist_id, product_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={})
        
        res = {}
        valores = {}
        res['value'] = valores
        valores['qtd'] = 1
        valores['vr_unitario'] = dados['value']['price_unit']
        valores['func_vr_unitario'] = dados['value']['price_unit']
        valores['vr_total'] = dados['value']['price_unit']
        valores['func_vr_total'] = dados['value']['price_unit']
        
        #
        # Muda a empresa para os serviços
        #
        valores['company_id'] = company_id
        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
        
        if product_obj.type == 'service':
            company_obj = self.pool.get('res.company').browse(cr, 1, company_id)
            
            if company_obj.company_servico_id:
                valores['company_id'] = company_obj.company_servico_id.id
        
        return res
    
    def onchange_qtd(self, cr, uid, ids, qtd, vr_unitario, context={}):
        qtd = qtd or 1.0
        vr_unitario = vr_unitario or 1.0
        vr_total = qtd * vr_unitario
        
        res = {}
        valores = {}
        res['value'] = valores
        
        valores['vr_total'] = vr_total
        valores['func_vr_total'] = vr_total
        
        return res


ordem_servico_produto()

