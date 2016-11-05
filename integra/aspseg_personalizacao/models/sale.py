# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields
import netsvc
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def onchange_company_id_asp(self, cr, uid, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        retorna = False
        if user_obj.operacao_id:
            retorna = user_obj.operacao_id.id
        else:
            retorna = self.pool.get('res.company').browse(cr, uid, self.pool.get('res.company')._company_default_get(cr, uid, 'sale.order', context=context)).operacao_id.id

        return retorna

    _columns = {                
    }

    _defaults = {
        'operacao_fiscal_produto_id': onchange_company_id_asp,
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)

        if not part:
            return res

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)

        if part.account_payment_term_id:
            res['value']['payment_term'] = part.account_payment_term_id.id

        return res

    def button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).button_confirm(cr, uid, ids, context=context)

        #
        # No caso de venda ambulante, marcar automaticamente a lista de separação
        # como aprovada
        #
        for ped_obj in self.browse(cr, uid, ids, contex=context):
            if ped_obj.operacao_produto_id and ped_obj.operacao_produto_id.id == 8:
                for picking_obj in ped_obj.picking_ids:
                    picking_obj.action_confirm()

        return res

    def action_cancel(self, cr, uid, ids, context={}):
        wf_service = netsvc.LocalService("workflow")

        sale_order_line_obj = self.pool.get('sale.order.line')
        proc_obj = self.pool.get('procurement.order')

        for sale in self.browse(cr, uid, ids, context=context):
            #
            # No caso da ASP, se nenhuma nota tiver sido emitida, exclui as separações
            # do estoque, no caso de cancelamento do pedido
            #
            picks = []
            for pick in sale.picking_ids:
                if pick.sped_documento_id:
                    raise osv.except_osv(u'Erro!', u'Você não pode cancelar pois já há notas faturadas para esse item/pedido!')

                picks += [pick.id]

            for pid in picks:
                cr.execute("update stock_move set state='cancel' where picking_id = " + str(pid) + ";")
                cr.execute("update stock_picking set state='cancel' where id = " + str(pid) + ";")

            #self.pool.get('stock.picking').unlink(cr, 1, picks)

            #for pick in sale.picking_ids:
                #if pick.state not in ('draft', 'cancel'):
                    #raise osv.except_osv(
                        #_('Could not cancel sales order !'),
                        #_('You must first cancel all picking attached to this sales order.'))

                #if pick.state == 'cancel':
                    #for mov in pick.move_lines:
                        #proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        #if proc_ids:
                            #for proc in proc_ids:
                                #wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)

            #for r in self.read(cr, uid, ids, ['picking_ids']):
                #for pick in r['picking_ids']:
                    #wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)

            for inv in sale.invoice_ids:
                if inv.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Could not cancel this sales order !'),
                        _('You must first cancel all invoices attached to this sales order.'))

            for r in self.read(cr, uid, ids, ['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)

            sale_order_line_obj.write(cr, uid, [l.id for l in  sale.order_line],
                    {'state': 'cancel'})

            message = _("The sales order '%s' has been cancelled.") % (sale.name,)

            self.log(cr, uid, sale.id, message)

        self.write(cr, uid, ids, {'state': 'cancel'})
        return True


sale_order()
