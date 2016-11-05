# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.models.fields import CampoDinheiro, CampoQuantidade
from pybrasil.valor.decimal import Decimal as D


class purchase_order_line(osv.Model):
    #_table = 'purchase_order_line'
    _name = 'purchase.order.line'
    _description = 'Purchase Order Line'
    _inherit = 'purchase.order.line'
    _rec_name = 'descricao'

    def _get_nome_funcao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            texto = u''
            if obj.product_id.default_code:
                texto += '[' + obj.product_id.default_code + '] '

            texto += obj.product_id.name
            texto += ' - ' + obj.order_id.name

            res[obj.id] = texto

        return res

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('descricao', 'ilike', texto),
        ]

        return procura

    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            #taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty)
            #cur = line.order_id.pricelist_id.currency_id
            subtotal = D(line.product_qty or 0) * D(line.price_unit or 0)
            subtotal -= D(line.vr_desconto or 0)

            #res[line.id] = cur_obj.round(cr, uid, cur, taxes['total']) + line.vr_ipi
            res[line.id] = subtotal + D(line.vr_ipi or 0) + D(line.vr_st or 0)
        return res

    #def _get_uom_id(self, cr, uid, context=None):
        #try:
            #proxy = self.pool.get('ir.model.data')
            #result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            #return result[1]
        #except Exception, ex:
            #return False

    _columns = {
        'descricao': fields.function(_get_nome_funcao, type='char', size=256, string=u'Descrição', store=False, fnct_search=_procura_nome),
        'bc_ipi': CampoDinheiro(u'Base do IPI'),
        'al_ipi': CampoQuantidade(u'Alíquota do IPI'),
        'vr_ipi': CampoDinheiro(u'Valor do IPI'),

        'bc_st': CampoDinheiro(u'Base do ST'),
        'al_st': CampoQuantidade(u'% do ST'),
        'vr_st': CampoDinheiro(u'Valor do ST'),
        #'name': fields.char('Description', size=256, required=True),
        #'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM'), required=True),
        #'date_planned': fields.date('Scheduled Date', required=True, select=True),
        #'taxes_id': fields.many2many('account.tax', 'purchase_order_taxe', 'ord_id', 'tax_id', 'Taxes'),
        #'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
        'product_id': fields.many2one('product.product', u'Produto', domain=[('purchase_ok','=',True)], change_default=True, ondelete='restrict'),
        #'move_ids': fields.one2many('stock.move', 'purchase_line_id', 'Reservation', readonly=True, ondelete='set null'),
        #'move_dest_id': fields.many2one('stock.move', 'Reservation Destination', ondelete='set null'),
        #'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Purchase Price')),
        'price_unit': fields.float('Unit Price', required=True, digits=(18,4)),
        'al_desconto': CampoQuantidade(u'% do Desconto'),
        'vr_desconto': CampoDinheiro(u'Desconto'),
        'price_subtotal': fields.function(_amount_line, type='float', string='Subtotal', digits=(18, 2), store=True),
        #'notes': fields.text('Notes'),
        #'order_id': fields.many2one('purchase.order', 'Order Reference', select=True, required=True, ondelete='cascade'),
        #'account_analytic_id':fields.many2one('account.analytic.account', 'Analytic Account',),
        #'company_id': fields.related('order_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
        #'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')], 'State', required=True, readonly=True,
                                  #help=' * The \'Draft\' state is set automatically when purchase order in draft state. \
                                       #\n* The \'Confirmed\' state is set automatically as confirm when purchase order in confirm state. \
                                       #\n* The \'Done\' state is set automatically when purchase order is set as done. \
                                       #\n* The \'Cancelled\' state is set automatically when user cancel purchase order.'),
        #'invoice_lines': fields.many2many('account.invoice.line', 'purchase_order_line_invoice_rel', 'order_line_id', 'invoice_id', 'Invoice Lines', readonly=True),
        #'invoiced': fields.boolean('Invoiced', readonly=True),
        #'partner_id': fields.related('order_id','partner_id',string='Partner',readonly=True,type="many2one", relation="res.partner", store=True),
        #'date_order': fields.related('order_id','date_order',string='Order Date',readonly=True,type="date")
    }

    _defaults = {
        #'product_uom' : _get_uom_id,
        #'product_qty': lambda *a: 1.0,
        #'state': lambda *args: 'draft',
        #'invoiced': lambda *a: 0,
        'bc_ipi': 0,
        'al_ipi': 0,
        'vr_ipi': 0,
        'bc_st': 0,
        'al_st': 0,
        'vr_st': 0,
        'al_desconto': 0,
        'vr_desconto': 0,
    }

    #def copy_data(self, cr, uid, id, default=None, context=None):
        #if not default:
            #default = {}
        #default.update({'state':'draft', 'move_ids':[],'invoiced':0,'invoice_lines':[]})
        #return super(purchase_order_line, self).copy_data(cr, uid, id, default, context)

    #def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            #partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            #name=False, price_unit=False, notes=False, context=None):
        #"""
        #onchange handler of product_uom.
        #"""
        #if not uom_id:
            #return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or'', 'product_uom' : uom_id or False}}
        #return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            #partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            #name=name, price_unit=price_unit, notes=notes, context=context)

    #def _get_date_planned(self, cr, uid, supplier_info, date_order_str, context=None):
        #"""Return the datetime value to use as Schedule Date (``date_planned``) for
           #PO Lines that correspond to the given product.supplierinfo,
           #when ordered at `date_order_str`.

           #:param browse_record | False supplier_info: product.supplierinfo, used to
               #determine delivery delay (if False, default delay = 0)
           #:param str date_order_str: date of order, as a string in
               #DEFAULT_SERVER_DATE_FORMAT
           #:rtype: datetime
           #:return: desired Schedule Date for the PO line
        #"""
        #supplier_delay = int(supplier_info.delay) if supplier_info else 0
        #return datetime.strptime(date_order_str, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=supplier_delay)

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context={}, al_ipi=0, vr_ipi=0, al_st=0, vr_st=0, al_desconto=0, vr_desconto=0):
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned, name=name, price_unit=price_unit, notes=notes, context=context)

        valores = res['value']

        if price_unit:
            vr_unitario = price_unit
            valores['price_unit'] = price_unit

        else:
            vr_unitario = valores['price_unit']

        vr_total = D(qty or 0) * D(vr_unitario or 0)
        vr_total = vr_total.quantize(D('0.01'))
        al_ipi = D(al_ipi or 0)
        vr_ipi = D(vr_ipi or 0)
        al_st = D(al_st or 0)
        vr_st = D(vr_st or 0)
        al_desconto = D(al_desconto or 0)
        vr_desconto = D(vr_desconto or 0)

        if al_desconto > 0:
            vr_desconto = vr_total * al_desconto / 100
            vr_desconto = vr_desconto.quantize(D('0.01'))
            valores['vr_desconto'] = vr_desconto
            vr_total -= vr_desconto
        elif vr_desconto > 0:
            al_desconto = vr_desconto / vr_total * 100
            al_desconto = al_desconto.quantize(D('0.01'))
            valores['al_desconto'] = al_desconto
            vr_total -= vr_desconto

        if al_ipi > 0:
            bc_ipi = vr_total
            valores['bc_ipi'] = bc_ipi

            vr_ipi = bc_ipi * al_ipi / 100
            valores['vr_ipi'] = vr_ipi
            valores['al_ipi'] = al_ipi

        elif vr_ipi > 0:
            bc_ipi = vr_total
            valores['bc_ipi'] = bc_ipi
            valores['vr_ipi'] = vr_ipi

            al_ipi = vr_ipi / bc_ipi * 100
            valores['al_ipi'] = al_ipi

        vr_total += vr_ipi

        if al_st > 0:
            bc_st = vr_total
            valores['bc_st'] = bc_st
            valores['al_st'] = al_st

            vr_st = bc_st * al_st / 100
            valores['vr_st'] = vr_st

        elif vr_st > 0:
            bc_st = vr_total
            valores['bc_st'] = bc_st
            valores['vr_st'] = vr_st

            al_st = vr_st / bc_st * 100
            valores['al_st'] = al_st

        valores['price_subtotal'] = vr_total + vr_ipi + vr_st

        return res

    product_id_change = onchange_product_id
    #product_uom_change = onchange_product_uom

    #def action_confirm(self, cr, uid, ids, context=None):
        #self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)
        #return True


purchase_order_line()
