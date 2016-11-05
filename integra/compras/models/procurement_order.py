# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from tools.translate import _
import netsvc


class procurement_order(osv.osv):
    _name = 'procurement.order'
    _inherit = 'procurement.order'

    _columns = {
        'requisition_id': fields.many2one('purchase.requisition', u'Requisição de compra'),
    }

    def check_buy_original(self, cr, uid, ids):
        """ Checks product type.
        @return: True or Product Id.
        """
        user = self.pool.get('res.users').browse(cr, uid, uid)
        partner_pool = self.pool.get('res.partner')
        for procurement in self.browse(cr, uid, ids):
            if procurement.product_id.product_tmpl_id.supply_method <> 'buy':
                return False
            if not procurement.product_id.seller_ids:
                #cr.execute('update procurement_order set message=%s where id=%s',
                        #(_('No supplier defined for this product !'), procurement.id))
                return False
            partner = procurement.product_id.seller_id #Taken Main Supplier of Product of Procurement.

            if not partner:
                #cr.execute('update procurement_order set message=%s where id=%s',
                           #(_('No default supplier defined for this product'), procurement.id))
                return False

            if user.company_id and user.company_id.partner_id:
                if partner.id == user.company_id.partner_id.id:
                    return False

            address_id = partner_pool.address_get(cr, uid, [partner.id], ['delivery'])['delivery']
            if not address_id:
                #cr.execute('update procurement_order set message=%s where id=%s',
                        #(_('No address defined for the supplier'), procurement.id))
                return False

    def check_buy(self, cr, uid, ids):
        #
        # Retorna sempre verdadeiro, porque se não for possível criar um
        # pedido de compra, vai criar a requisição no lugar
        #
        return True

    def action_po_assign(self, cr, uid, ids, context=None):
        """ This is action which call from workflow to assign purchase order to procurements
        @return: True
        """
        if self.check_buy_original(cr, uid, ids):
            res = self.make_po(cr, uid, ids, context=context)
        else:
            res = self.cria_requisicao(cr, uid, ids, context=context)

        res = res.values()
        return len(res) and res[0] or 0 #TO CHECK: why workflow is generated error if return not integer value

    def cria_requisicao(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        @return: New created Purchase Orders procurement wise
        """
        res = {}

        if context is None:
            context = {}

        requisition_pool = self.pool.get('purchase.requisition')
        item_requisition_pool = self.pool.get('purchase.requisition.line')
        unidade_pool = self.pool.get('product.uom')
        warehouse_pool = self.pool.get('stock.warehouse')

        for procurement_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                'company_id': procurement_obj.company_id.id,
            }

            warehouse_ids = warehouse_pool.search(cr, uid, [('company_id', '=', procurement_obj.company_id.id)], context=context)
            if len(warehouse_ids):
                dados['warehouse_id'] = warehouse_ids[0]

            requisition_id = requisition_pool.create(cr, uid, dados)

            dados_item = {
                'requisition_id': requisition_id,
                'product_id': procurement_obj.product_id.id,
                'product_uom_id': procurement_obj.product_uom.id,
            }

            quantidade = unidade_pool._compute_qty(cr, uid, procurement_obj.product_uom.id, procurement_obj.product_qty, procurement_obj.product_id.uom_po_id.id)

            dados_item['product_qty'] = quantidade or 0

            item_requisition_pool.create(cr, uid, dados_item)

            res[procurement_obj.id] = requisition_id

            self.write(cr, uid, [procurement_obj.id], {'state': 'running', 'requisition_id': res[procurement_obj.id]})

        return res

    def check_make_to_stock(self, cr, uid, ids, context=None):
        """ Checks product type.
        @return: True or False
        """
        ok = True
        for procurement in self.browse(cr, uid, ids, context=context):
            if procurement.product_id.type == 'service':
                ok = ok and self._check_make_to_stock_service(cr, uid, procurement, context)
            else:
                ok = ok and self._check_make_to_stock_product(cr, uid, procurement, context)

                if not ok:
                    #
                    # Não tem produto, muda o tipo de seleção para compra
                    #
                    #procurement.write({'procure_method': 'make_to_order'})
                    cr.execute("update procurement_order set procure_method = 'make_to_order' where id = {id};".format(id=procurement.id))
                    #pass

        return ok

    def verifica_compra(self, cr, uid, ids, context={}):
        #for procurement in self.browse(cr, uid, ids, context=context):
            #cr.execute("update procurement_order set state = 'draft', procure_method = 'make_to_order' where id = {id};".format(id=procurement.id))

        return True

    #def action_done(self, cr, uid, ids):
        #""" Changes procurement state to Done and writes Closed date.
        #@return: True
        #"""
        #move_obj = self.pool.get('stock.move')
        #res = []

        #print('entrou aqui', ids)

        #for procurement in self.browse(cr, uid, ids):
            #if procurement.move_id:
                #if procurement.close_move and (procurement.move_id.state <> 'done'):
                    #move_obj.action_done(cr, uid, [procurement.move_id.id])

            #print(procurement, procurement.state, procurement.procure_method)
            #if procurement.state != 'draft':
                #gravado = self.write(cr, uid, [procurement.id], {'state': 'done', 'date_close': time.strftime('%Y-%m-%d')})
                #res += gravado

        #wf_service = netsvc.LocalService("workflow")
        #for id in ids:
            #wf_service.trg_trigger(uid, 'procurement.order', id, cr)

        #return res

    #def write(self, cr, uid, ids, dados, context={}):
        #res = super(procurement_order, self).write(cr, uid, ids, dados, context=context)

        #print(ids, dados)
        #import traceback
        #traceback.print_stack()

        #return res


procurement_order()
