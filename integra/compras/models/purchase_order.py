# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from finan.wizard.finan_relatorio import Report
import os
import base64
from decimal import Decimal as D
from sped.constante_tributaria import MODALIDADE_FRETE
from sped.models.fields import CampoDinheiro


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


RECALCULA = {
    'purchase.order.line': (
        lambda compra_pool, cr, uid, ids, context={}: compra_pool.pool.get('purchase.order')._get_order(cr, uid, ids, context),
        None,
        10
    ),
    'purchase.order': (
        lambda compra_pool, cr, uid, ids, context={}: ids,
        ['vr_desconto', 'vr_frete', 'vr_ipi', 'write_date', 'vr_st'],
        20  #  Prioridade
    )

}


class purchase_order(osv.Model):
    _name = 'purchase.order'
    _description = 'Purchase Order'
    _order = 'name desc'
    _inherit = ['purchase.order', 'mail.thread']

    def imprime_ordem_compra(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Ordem de Compra', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'ordem_compra.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
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

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }

            total = 0
            total_sem_ipi = 0
            for line in order.order_line:
               total += (line.product_qty * line.price_unit)
               total += line.vr_ipi or 0
               total += line.vr_st or 0
               total_sem_ipi += line.product_qty * line.price_unit

            res[order.id]['amount_tax'] = 0
            res[order.id]['amount_untaxed'] = total_sem_ipi
            res[order.id]['amount_total'] = total + order.vr_frete - order.vr_desconto

        return res

    def agenda_ligacao(self, cr, uid, ids, hora, resumo_ligacao, descricao, fone, user_id, acao='schedule', context={}):
        """
        action :('schedule','Schedule a call'), ('log','Log a call')
        """
        ligacao_pool= self.pool.get('crm.phonecall')
        dados_ligacao = {}

        for purchaseorder_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                    'name' : resumo_ligacao,
                    'purchase_order_id': purchaseorder_obj.id,
                    'opportunity_id' : False,
                    'user_id' : user_id or purchaseorder_obj.user_id.id or uid,
                    'categ_id' : False,
                    'description' : descricao or '',
                    'date' : hora,
                    'section_id' : False,
                    'partner_id': purchaseorder_obj.partner_id and purchaseorder_obj.partner_id.id or False,
                    'partner_address_id': purchaseorder_obj.partner_address_id and purchaseorder_obj.partner_address_id.id or False,
                    'partner_phone' : fone or purchaseorder_obj.partner_fone or (purchaseorder_obj.partner_address_id and purchaseorder_obj.partner_address_id.phone or False),
                    'partner_mobile' : purchaseorder_obj.partner_celular or purchaseorder_obj.partner_address_id and purchaseorder_obj.partner_address_id.mobile or False,
                    #'priority': purchaseorder_obj.priority,
            }

            ligacao_id = ligacao_pool.create(cr, uid, dados, context=context)
            ligacao_pool.case_open(cr, uid, [ligacao_id])
            if acao == 'log':
                ligacao_pool.case_close(cr, uid, [ligacao_id])
            dados_ligacao[purchaseorder_obj.id] = ligacao_id

        return dados_ligacao

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            lancamento_id = ids[0]

        if not lancamento_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'compras', 'purchase_nota_wizard')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'purchase.nota',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'purchase.order', 'active_ids': [lancamento_id]},
        }

        return retorno

    ##def _set_minimum_planned_date(self, cr, uid, ids, name, value, arg, context=None):
        ##if not value: return False
        ##if type(ids)!=type([]):
            ##ids=[ids]
        ##for po in self.browse(cr, uid, ids, context=context):
            ##if po.order_line:
                ##cr.execute("""update purchase_order_line set
                        ##date_planned=%s
                    ##where
                        ##order_id=%s and
                        ##(date_planned=%s or date_planned<%s)""", (value,po.id,po.minimum_planned_date,value))
            ##cr.execute("""update purchase_order set
                    ##minimum_planned_date=%s where id=%s""", (value, po.id))
        ##return True

    ##def _minimum_planned_date(self, cr, uid, ids, field_name, arg, context=None):
        ##res={}
        ##purchase_obj=self.browse(cr, uid, ids, context=context)
        ##for purchase in purchase_obj:
            ##res[purchase.id] = False
            ##if purchase.order_line:
                ##min_date=purchase.order_line[0].date_planned
                ##for line in purchase.order_line:
                    ##if line.date_planned < min_date:
                        ##min_date=line.date_planned
                ##res[purchase.id]=min_date
        ##return res


    ##def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        ##res = {}
        ##for purchase in self.browse(cursor, user, ids, context=context):
            ##tot = 0.0
            ##for invoice in purchase.invoice_ids:
                ##if invoice.state not in ('draft','cancel'):
                    ##tot += invoice.amount_untaxed
            ##if purchase.amount_untaxed:
                ##res[purchase.id] = tot * 100.0 / purchase.amount_untaxed
            ##else:
                ##res[purchase.id] = 0.0
        ##return res

    ##def _shipped_rate(self, cr, uid, ids, name, arg, context=None):
        ##if not ids: return {}
        ##res = {}
        ##for id in ids:
            ##res[id] = [0.0,0.0]
        ##cr.execute('''SELECT
                ##p.purchase_id,sum(m.product_qty), m.state
            ##FROM
                ##stock_move m
            ##LEFT JOIN
                ##stock_picking p on (p.id=m.picking_id)
            ##WHERE
                ##p.purchase_id IN %s GROUP BY m.state, p.purchase_id''',(tuple(ids),))
        ##for oid,nbr,state in cr.fetchall():
            ##if state=='cancel':
                ##continue
            ##if state=='done':
                ##res[oid][0] += nbr or 0.0
                ##res[oid][1] += nbr or 0.0
            ##else:
                ##res[oid][1] += nbr or 0.0
        ##for r in res:
            ##if not res[r][1]:
                ##res[r] = 0.0
            ##else:
                ##res[r] = 100.0 * res[r][0] / res[r][1]
        ##return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    ##def _invoiced(self, cursor, user, ids, name, arg, context=None):
        ##res = {}
        ##for purchase in self.browse(cursor, user, ids, context=context):
            ##invoiced = False
            ##if purchase.invoiced_rate == 100.00:
                ##invoiced = True
            ##res[purchase.id] = invoiced
        ##return res

    STATE_SELECTION = [
        ('draft', u'Aguardando Aprovação'),
        ('wait', 'Waiting'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]

    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for doc_obj in self.browse(cr, uid, ids):
            soma = D('0')
            for item_obj in doc_obj.order_line:
                soma += D(str(getattr(item_obj, nome_campo, 0)))

            soma = soma.quantize(D('0.01'))

            #if nome_campo == 'vr_fatura':
                #soma -= D(str(doc_obj.vr_pis_retido))
                #soma -= D(str(doc_obj.vr_cofins_retido))
                #soma -= D(str(doc_obj.vr_csll))
                #soma -= D(str(doc_obj.vr_irrf))
                #soma -= D(str(doc_obj.vr_previdencia))
                #soma -= D(str(doc_obj.vr_iss_retido))

            #if nome_campo == 'bc_previdencia' or nome_campo == 'vr_previdencia':
                #if soma < D('10'):
                    #soma = D('0')

            res[doc_obj.id] = soma

        return res

    _columns = {
        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'purchase.order')]),
        'crm_phonecall_ids': fields.one2many('crm.phonecall', 'purchase_order_id', u'Ligações telefônicas'),
        'partner_fone': fields.related('partner_id', 'fone', type='char', string='Fone'),
        'partner_celular': fields.related('partner_id', 'celular', type='char', string='Celular'),

        'modalidade_frete': fields.selection(MODALIDADE_FRETE, u'Modalidade do frete'),
        'transportadora_id': fields.many2one('res.partner', u'Transportadora', domain=[('cnpj_cpf', '!=', False)]),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'bc_ipi': fields.function(_get_soma_funcao, type='float', store=True, digits=(18, 2), string=u'Base do IPI'),
        'vr_ipi': fields.function(_get_soma_funcao, type='float', store=True, digits=(18, 2), string=u'Valor do IPI'),
        'bc_st': fields.function(_get_soma_funcao, type='float', store=True, digits=(18, 2), string=u'Base do ST'),
        'vr_st': fields.function(_get_soma_funcao, type='float', store=True, digits=(18, 2), string=u'Valor do ST'),
        'al_desconto': CampoDinheiro(u'Percentual do desconto'),
        'vr_desconto': CampoDinheiro(u'Valor do desconto'),
        'vr_frete': CampoDinheiro(u'Valor do frete'),
        #'vr_ipi': CampoDinheiro(u'Valor do IPI'),
        #'name': fields.char('Order Reference', size=64, required=True, select=True, help="unique number of the purchase order,computed automatically when the purchase order is created"),
        #'origin': fields.char('Source Document', size=64,
            #help="Reference of the document that generated this purchase order request."
        #),
        #'partner_ref': fields.char('Supplier Reference', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, size=64),
        #'date_order':fields.date('Order Date', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}, select=True, help="Date on which this document has been created."),
        #'date_approve':fields.date('Date Approved', readonly=1, select=True, help="Date on which purchase order has been approved"),
        #'partner_id':fields.many2one('res.partner', 'Supplier', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, change_default=True),
        #'partner_address_id':fields.many2one('res.partner.address', 'Address', required=True,
            #states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]},domain="[('partner_id', '=', partner_id)]"),
        #'dest_address_id':fields.many2one('res.partner.address', 'Destination Address', domain="[('partner_id', '!=', False)]",
            #states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]},
            #help="Put an address if you want to deliver directly from the supplier to the customer." \
                #"In this case, it will remove the warehouse link and set the customer location."
        #),
        #'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        #'location_id': fields.many2one('stock.location', 'Destination', required=True, domain=[('usage','<>','view')]),
        #'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'state': fields.selection(STATE_SELECTION, 'State', readonly=True, help="The state of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' state. Then the order has to be confirmed by the user, the state switch to 'Confirmed'. Then the supplier must confirm the order to change the state to 'Approved'. When the purchase order is paid and received, the state becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the state becomes in exception.", select=True),
        #'order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
        #'validator' : fields.many2one('res.users', 'Validated by', readonly=True),
        #'invoice_ids': fields.many2many('account.invoice', 'purchase_invoice_rel', 'purchase_id', 'invoice_id', 'Invoices', help="Invoices generated for a purchase order"),
        #'picking_ids': fields.one2many('stock.picking', 'purchase_id', 'Picking List', readonly=True, help="This is the list of picking list that have been generated for this purchase"),
        #'shipped':fields.boolean('Received', readonly=True, select=True, help="It indicates that a picking has been done"),
        #'shipped_rate': fields.function(_shipped_rate, string='Received', type='float'),
        #'invoiced': fields.function(_invoiced, string='Invoiced & Paid', type='boolean', help="It indicates that an invoice has been paid"),
        #'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
        'invoice_method': fields.selection([('manual','Based on Purchase Order lines'),('order','Based on generated draft invoice'),('picking','Based on receptions')], 'Invoicing Control', required=True,
            help="Based on Purchase Order lines: place individual lines in 'Invoice Control > Based on P.O. lines' from where you can selectively create an invoice.\n" \
                "Based on generated invoice: create a draft invoice you can validate later.\n" \
                "Based on receptions: let you create an invoice when receptions are validated."
        ),
        #'minimum_planned_date':fields.function(_minimum_planned_date, fnct_inv=_set_minimum_planned_date, string='Expected Date', type='date', select=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
            #store = {
                #'purchase.order.line': (_get_order, ['date_planned'], 10),
            #}
        #),
        'amount_untaxed': fields.function(_amount_all, digits=(18, 2), string='Untaxed Amount',
            store=RECALCULA, multi="sums", help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, digits=(18, 2), string='Taxes',
            store=RECALCULA, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits=(18, 2), string='Total',
            store=RECALCULA, multi="sums",help="The total amount"),
        #'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        #'product_id': fields.related('order_line','product_id', type='many2one', relation='product.product', string='Product'),
        #'create_uid':  fields.many2one('res.users', 'Responsible'),
        #'company_id': fields.many2one('res.company','Company',required=True,select=1),
        'notes': fields.text(u'Observações internas'),
        'obs_fornecedor': fields.text(u'Observações para o fornecedor'),
        'obs_custo_despesa': fields.selection([['A', u'Ativo imobilizado'], ['M', u'Material aplicado']], u'Aplicação do material')

    }

    _defaults = {
        #'date_order': fields.date.context_today,
        #'state': 'draft',
        #'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.order'),
        #'shipped': 0,
        'invoice_method': 'picking',
        #'invoiced': 0,
        #'partner_address_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['default'])['default'],
        #'pricelist_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').browse(cr, uid, context['partner_id']).property_product_pricelist_purchase.id,
        #'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order', context=c),
        'modalidade_frete': '0',
    }

    ##_sql_constraints = [
        ##('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ##]
    ##_name = "purchase.order"
    ##_description = "Purchase Order"
    ##_order = "name desc"

    ##def unlink(self, cr, uid, ids, context=None):
        ##purchase_orders = self.read(cr, uid, ids, ['state'], context=context)
        ##unlink_ids = []
        ##for s in purchase_orders:
            ##if s['state'] in ['draft','cancel']:
                ##unlink_ids.append(s['id'])
            ##else:
                ##raise osv.except_osv(_('Invalid action !'), _('In order to delete a purchase order, it must be cancelled first!'))

        ### TODO: temporary fix in 5.0, to remove in 5.2 when subflows support
        ### automatically sending subflow.delete upon deletion
        ##wf_service = netsvc.LocalService("workflow")
        ##for id in unlink_ids:
            ##wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)

        ##return super(purchase_order, self).unlink(cr, uid, unlink_ids, context=context)

    ##def button_dummy(self, cr, uid, ids, context=None):
        ##return True

    ##def onchange_dest_address_id(self, cr, uid, ids, address_id):
        ##if not address_id:
            ##return {}
        ##address = self.pool.get('res.partner.address')
        ##values = {'warehouse_id': False}
        ##supplier = address.browse(cr, uid, address_id).partner_id
        ##if supplier:
            ##location_id = supplier.property_stock_customer.id
            ##values.update({'location_id': location_id})
        ##return {'value':values}

    ##def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        ##if not warehouse_id:
            ##return {}
        ##warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        ##return {'value':{'location_id': warehouse.lot_input_id.id, 'dest_address_id': False}}

    ##def onchange_partner_id(self, cr, uid, ids, partner_id):
        ##partner = self.pool.get('res.partner')
        ##if not partner_id:
            ##return {'value':{'partner_address_id': False, 'fiscal_position': False}}
        ##supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        ##supplier = partner.browse(cr, uid, partner_id)
        ##pricelist = supplier.property_product_pricelist_purchase.id
        ##fiscal_position = supplier.property_account_position and supplier.property_account_position.id or False
        ##return {'value':{'partner_address_id': supplier_address['default'], 'pricelist_id': pricelist, 'fiscal_position': fiscal_position}}

    ##def wkf_approve_order(self, cr, uid, ids, context=None):
        ##self.write(cr, uid, ids, {'state': 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context)})
        ##return True

    ###TODO: implement messages system
    ##def wkf_confirm_order(self, cr, uid, ids, context=None):
        ##todo = []
        ##for po in self.browse(cr, uid, ids, context=context):
            ##if not po.order_line:
                ##raise osv.except_osv(_('Error !'),_('You cannot confirm a purchase order without any lines.'))
            ##for line in po.order_line:
                ##if line.state=='draft':
                    ##todo.append(line.id)
            ##message = _("Purchase order '%s' is confirmed.") % (po.name,)
            ##self.log(cr, uid, po.id, message)
###        current_name = self.name_get(cr, uid, ids)[0][1]
        ##self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        ##for id in ids:
            ##self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})
        ##return True

    ##def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        ##"""Collects require data from purchase order line that is used to create invoice line
        ##for that purchase order line
        ##:param account_id: Expense account of the product of PO line if any.
        ##:param browse_record order_line: Purchase order line browse record
        ##:return: Value for fields of invoice lines.
        ##:rtype: dict
        ##"""
        ##return {
            ##'name': order_line.name,
            ##'account_id': account_id,
            ##'price_unit': order_line.price_unit or 0.0,
            ##'quantity': order_line.product_qty,
            ##'product_id': order_line.product_id.id or False,
            ##'uos_id': order_line.product_uom.id or False,
            ##'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            ##'account_analytic_id': order_line.account_analytic_id.id or False,
        ##}

    ##def action_cancel_draft(self, cr, uid, ids, *args):
        ##if not len(ids):
            ##return False
        ##self.write(cr, uid, ids, {'state':'draft','shipped':0})
        ##wf_service = netsvc.LocalService("workflow")
        ##for p_id in ids:
            ### Deleting the existing instance of workflow for PO
            ##wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
            ##wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        ##for (id,name) in self.name_get(cr, uid, ids):
            ##message = _("Purchase order '%s' has been set in draft state.") % name
            ##self.log(cr, uid, id, message)
        ##return True

    ##def action_invoice_create(self, cr, uid, ids, context=None):
        ##"""Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        ##:param ids: list of ids of purchase orders.
        ##:return: ID of created invoice.
        ##:rtype: int
        ##"""
        ##res = False

        ##journal_obj = self.pool.get('account.journal')
        ##inv_obj = self.pool.get('account.invoice')
        ##inv_line_obj = self.pool.get('account.invoice.line')
        ##fiscal_obj = self.pool.get('account.fiscal.position')
        ##property_obj = self.pool.get('ir.property')

        ##for order in self.browse(cr, uid, ids, context=context):
            ##pay_acc_id = order.partner_id.property_account_payable.id
            ##journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
            ##if not journal_ids:
                ##raise osv.except_osv(_('Error !'),
                    ##_('There is no purchase journal defined for this company: "%s" (id:%d)') % (order.company_id.name, order.company_id.id))

            ### generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            ##inv_lines = []
            ##for po_line in order.order_line:
                ##if po_line.product_id:
                    ##acc_id = po_line.product_id.product_tmpl_id.property_account_expense.id
                    ##if not acc_id:
                        ##acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
                    ##if not acc_id:
                        ##raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (po_line.product_id.name, po_line.product_id.id,))
                ##else:
                    ##acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category').id
                ##fpos = order.fiscal_position or False
                ##acc_id = fiscal_obj.map_account(cr, uid, fpos, acc_id)

                ##inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                ##inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                ##inv_lines.append(inv_line_id)

                ##po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)

            ### get invoice data and create invoice
            ##inv_data = {
                ##'name': order.partner_ref or order.name,
                ##'reference': order.partner_ref or order.name,
                ##'account_id': pay_acc_id,
                ##'type': 'in_invoice',
                ##'partner_id': order.partner_id.id,
                ##'currency_id': order.pricelist_id.currency_id.id,
                ##'address_invoice_id': order.partner_address_id.id,
                ##'address_contact_id': order.partner_address_id.id,
                ##'journal_id': len(journal_ids) and journal_ids[0] or False,
                ##'invoice_line': [(6, 0, inv_lines)],
                ##'origin': order.name,
                ##'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                ##'payment_term': order.partner_id.property_payment_term and order.partner_id.property_payment_term.id or False,
                ##'company_id': order.company_id.id,
            ##}
            ##inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            ### compute the invoice
            ##inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            ### Link this new invoice to related purchase order
            ##order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            ##res = inv_id
        ##return res

    ##def has_stockable_product(self,cr, uid, ids, *args):
        ##for order in self.browse(cr, uid, ids):
            ##for order_line in order.order_line:
                ##if order_line.product_id and order_line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    ##return True
        ##return False

    ##def action_cancel(self, cr, uid, ids, context=None):
        ##wf_service = netsvc.LocalService("workflow")
        ##for purchase in self.browse(cr, uid, ids, context=context):
            ##for pick in purchase.picking_ids:
                ##if pick.state not in ('draft','cancel'):
                    ##raise osv.except_osv(
                        ##_('Unable to cancel this purchase order!'),
                        ##_('You must first cancel all receptions related to this purchase order.'))
            ##for pick in purchase.picking_ids:
                ##wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            ##for inv in purchase.invoice_ids:
                ##if inv and inv.state not in ('cancel','draft'):
                    ##raise osv.except_osv(
                        ##_('Unable to cancel this purchase order!'),
                        ##_('You must first cancel all invoices related to this purchase order.'))
                ##if inv:
                    ##wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
        ##self.write(cr,uid,ids,{'state':'cancel'})

        ##for (id, name) in self.name_get(cr, uid, ids):
            ##wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
            ##message = _("Purchase order '%s' is cancelled.") % name
            ##self.log(cr, uid, id, message)
        ##return True

    ##def _prepare_order_picking(self, cr, uid, order, context=None):
        ##return {
            ##'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in'),
            ##'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            ##'date': order.date_order,
            ##'type': 'in',
            ##'address_id': order.dest_address_id.id or order.partner_address_id.id,
            ##'invoice_state': '2binvoiced' if order.invoice_method == 'picking' else 'none',
            ##'purchase_id': order.id,
            ##'company_id': order.company_id.id,
            ##'move_lines' : [],
        ##}

    ##def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        ##return {
            ##'name': order.name + ': ' + (order_line.name or ''),
            ##'product_id': order_line.product_id.id,
            ##'product_qty': order_line.product_qty,
            ##'product_uos_qty': order_line.product_qty,
            ##'product_uom': order_line.product_uom.id,
            ##'product_uos': order_line.product_uom.id,
            ##'date': order_line.date_planned,
            ##'date_expected': order_line.date_planned,
            ##'location_id': order.partner_id.property_stock_supplier.id,
            ##'location_dest_id': order.location_id.id,
            ##'picking_id': picking_id,
            ##'address_id': order.dest_address_id.id or order.partner_address_id.id,
            ##'move_dest_id': order_line.move_dest_id.id,
            ##'state': 'draft',
            ##'purchase_line_id': order_line.id,
            ##'company_id': order.company_id.id,
            ##'price_unit': order_line.price_unit
        ##}

    ##def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        ##"""Creates pickings and appropriate stock moves for given order lines, then
        ##confirms the moves, makes them available, and confirms the picking.

        ##If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        ##a standard outgoing picking will be created to wrap the stock moves, as returned
        ##by :meth:`~._prepare_order_picking`.

        ##Modules that wish to customize the procurements or partition the stock moves over
        ##multiple stock pickings may override this method and call ``super()`` with
        ##different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        ##:param browse_record order: purchase order to which the order lines belong
        ##:param list(browse_record) order_lines: purchase order line records for which picking
                                                ##and moves should be created.
        ##:param int picking_id: optional ID of a stock picking to which the created stock moves
                               ##will be added. A new picking will be created if omitted.
        ##:return: list of IDs of pickings used/created for the given order lines (usually just one)
        ##"""
        ##if not picking_id:
            ##picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
        ##todo_moves = []
        ##stock_move = self.pool.get('stock.move')
        ##wf_service = netsvc.LocalService("workflow")
        ##for order_line in order_lines:
            ##if not order_line.product_id:
                ##continue
            ##if order_line.product_id.type in ('product', 'consu'):
                ##move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                ##if order_line.move_dest_id:
                    ##order_line.move_dest_id.write({'location_id': order.location_id.id})
                ##todo_moves.append(move)
        ##stock_move.action_confirm(cr, uid, todo_moves)
        ##stock_move.force_assign(cr, uid, todo_moves)
        ##wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        ##return [picking_id]

    ##def action_picking_create(self,cr, uid, ids, context=None):
        ##picking_ids = []
        ##for order in self.browse(cr, uid, ids):
            ##picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))

        ### Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        ### In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        ### one that should trigger the advancement of the purchase workflow.
        ### By default we will consider the first one as most important, but this behavior can be overridden.
        ##return picking_ids[0] if picking_ids else False

    ##def copy(self, cr, uid, id, default=None, context=None):
        ##if not default:
            ##default = {}
        ##default.update({
            ##'state':'draft',
            ##'shipped':False,
            ##'invoiced':False,
            ##'invoice_ids': [],
            ##'picking_ids': [],
            ##'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order'),
        ##})
        ##return super(purchase_order, self).copy(cr, uid, id, default, context)

    ##def do_merge(self, cr, uid, ids, context=None):
        ##"""
        ##To merge similar type of purchase orders.
        ##Orders will only be merged if:
        ##* Purchase Orders are in draft
        ##* Purchase Orders belong to the same partner
        ##* Purchase Orders are have same stock location, same pricelist
        ##Lines will only be merged if:
        ##* Order lines are exactly the same except for the quantity and unit

         ##@param self: The object pointer.
         ##@param cr: A database cursor
         ##@param uid: ID of the user currently logged in
         ##@param ids: the ID or list of IDs
         ##@param context: A standard dictionary

         ##@return: new purchase order id

        ##"""
        ###TOFIX: merged order line should be unlink
        ##wf_service = netsvc.LocalService("workflow")
        ##def make_key(br, fields):
            ##list_key = []
            ##for field in fields:
                ##field_val = getattr(br, field)
                ##if field in ('product_id', 'move_dest_id', 'account_analytic_id'):
                    ##if not field_val:
                        ##field_val = False
                ##if isinstance(field_val, browse_record):
                    ##field_val = field_val.id
                ##elif isinstance(field_val, browse_null):
                    ##field_val = False
                ##elif isinstance(field_val, list):
                    ##field_val = ((6, 0, tuple([v.id for v in field_val])),)
                ##list_key.append((field, field_val))
            ##list_key.sort()
            ##return tuple(list_key)

    ### compute what the new orders should contain

        ##new_orders = {}

        ##for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'draft']:
            ##order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id'))
            ##new_order = new_orders.setdefault(order_key, ({}, []))
            ##new_order[1].append(porder.id)
            ##order_infos = new_order[0]
            ##if not order_infos:
                ##order_infos.update({
                    ##'origin': porder.origin,
                    ##'date_order': porder.date_order,
                    ##'partner_id': porder.partner_id.id,
                    ##'partner_address_id': porder.partner_address_id.id,
                    ##'dest_address_id': porder.dest_address_id.id,
                    ##'warehouse_id': porder.warehouse_id.id,
                    ##'location_id': porder.location_id.id,
                    ##'pricelist_id': porder.pricelist_id.id,
                    ##'state': 'draft',
                    ##'order_line': {},
                    ##'notes': '%s' % (porder.notes or '',),
                    ##'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,
                ##})
            ##else:
                ##if porder.date_order < order_infos['date_order']:
                    ##order_infos['date_order'] = porder.date_order
                ##if porder.notes:
                    ##order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                ##if porder.origin:
                    ##order_infos['origin'] = (order_infos['origin'] or '') + ' ' + porder.origin

            ##for order_line in porder.order_line:
                ##line_key = make_key(order_line, ('name', 'date_planned', 'taxes_id', 'price_unit', 'notes', 'product_id', 'move_dest_id', 'account_analytic_id'))
                ##o_line = order_infos['order_line'].setdefault(line_key, {})
                ##if o_line:
                    ### merge the line with an existing line
                    ##o_line['product_qty'] += order_line.product_qty * order_line.product_uom.factor / o_line['uom_factor']
                ##else:
                    ### append a new "standalone" line
                    ##for field in ('product_qty', 'product_uom'):
                        ##field_val = getattr(order_line, field)
                        ##if isinstance(field_val, browse_record):
                            ##field_val = field_val.id
                        ##o_line[field] = field_val
                    ##o_line['uom_factor'] = order_line.product_uom and order_line.product_uom.factor or 1.0



        ##allorders = []
        ##orders_info = {}
        ##for order_key, (order_data, old_ids) in new_orders.iteritems():
            ### skip merges with only one order
            ##if len(old_ids) < 2:
                ##allorders += (old_ids or [])
                ##continue

            ### cleanup order line data
            ##for key, value in order_data['order_line'].iteritems():
                ##del value['uom_factor']
                ##value.update(dict(key))
            ##order_data['order_line'] = [(0, 0, value) for value in order_data['order_line'].itervalues()]

            ### create the new order
            ##neworder_id = self.create(cr, uid, order_data)
            ##orders_info.update({neworder_id: old_ids})
            ##allorders.append(neworder_id)

            ### make triggers pointing to the old orders point to the new order
            ##for old_id in old_ids:
                ##wf_service.trg_redirect(uid, 'purchase.order', old_id, neworder_id, cr)
                ##wf_service.trg_validate(uid, 'purchase.order', old_id, 'purchase_cancel', cr)
        ##return orders_info

    def create(self, cr, uid, dados, context={}):
        res = super(purchase_order, self).create(cr, uid, dados, context=context)

        if 'vr_desconto' in dados or 'al_desconto' in dados:
            self.pool.get('purchase.order').ajusta_desconto(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(purchase_order, self).write(cr, uid, ids, dados, context=context)

        if not context.get('vr_desconto', False):
            if 'vr_desconto' in dados or 'al_desconto' in dados:
                self.pool.get('purchase.order').ajusta_desconto(cr, uid, ids)

        return res

    def ajusta_desconto(self, cr, uid, ids):
        for oc_obj in self.browse(cr, uid, ids):
            total = oc_obj.amount_untaxed or 0
            total += oc_obj.vr_ipi or 0
            total += oc_obj.vr_st or 0

            if oc_obj.al_desconto:
                vr_desconto = total * oc_obj.al_desconto / 100
                oc_obj.write({'vr_desconto': vr_desconto}, context={'vr_desconto': vr_desconto})

            elif oc_obj.vr_desconto:
                al_desconto = oc_obj.vr_desconto / total * 100
                cr.execute('update purchase_order set al_desconto = {al_desconto} where id = {id};'.format(al_desconto=al_desconto, id=oc_obj.id))



purchase_order()


class mail_compose_message(osv.osv_memory):
    """Generic E-mail composition wizard. This wizard is meant to be inherited
       at model and view level to provide specific wizard features.

       The behavior of the wizard can be modified through the use of context
       parameters, among which are:

         * mail.compose.message.mode: if set to 'reply', the wizard is in
                      reply mode and pre-populated with the original quote.
                      If set to 'mass_mail', the wizard is in mass mailing
                      where the mail details can contain template placeholders
                      that will be merged with actual data before being sent
                      to each recipient. Recipients will be derived from the
                      records determined via  ``context['active_model']`` and
                      ``context['active_ids']``.
         * active_model: model name of the document to which the mail being
                        composed is related
         * active_id: id of the document to which the mail being composed is
                      related, or id of the message to which user is replying,
                      in case ``mail.compose.message.mode == 'reply'``
         * active_ids: ids of the documents to which the mail being composed is
                      related, in case ``mail.compose.message.mode == 'mass_mail'``.
    """

    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context=None):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'purchase.order':
            doc_obj = self.pool.get('purchase.order').browse(cr, uid, res_id)

            if doc_obj.partner_address_id and doc_obj.partner_address_id.email:
                res['email_to'] = doc_obj.partner_address_id.email or ''
            else:
                res['email_to'] = doc_obj.partner_id.email_nfe or ''

            res['subject'] = u'Envio de pedido de compra'

        return res