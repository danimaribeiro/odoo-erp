# -*- coding: utf-8 -*-

from osv import osv, fields
import time


class crm_purchaseorder2phonecall(osv.osv_memory):
    _name = 'crm.purchaseorder2phonecall'
    _inherit = 'crm.phonecall2phonecall'
    _description = u'Lançamento para ligação telefônica'

    _columns = {
        'action': fields.selection([('schedule','Agendar uma ligação'), ('log','Registrar uma ligação')], 'Action', required=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        purchaseorder_pool = self.pool.get('purchase.order')

        record_ids = context and context.get('active_ids', []) or []
        res = {}
        res['action'] = 'schedule'
        res['date'] = time.strftime('%Y-%m-%d %H:%M:%S')

        for purchaseorder_obj in purchaseorder_pool.browse(cr, uid, record_ids, context=context):
            if 'name' in fields:
                #if purchaseorder_obj.state == 'draft':
                    #nome = u'Orçamento nº ' + purchaseorder_obj.name
                #else:
                    #nome = u'Pedido nº ' + purchaseorder_obj.name
                nome = u'Pedido de compra nº ' + purchaseorder_obj.name

                res['name'] = nome

            if 'user_id' in fields:
                res['user_id'] = purchaseorder_obj.user_id.id or uid

            if 'partner_id' in fields:
                res['partner_id'] = purchaseorder_obj.partner_id and purchaseorder_obj.partner_id.id or False

            if 'phone' in fields:
                res['phone'] = purchaseorder_obj.partner_fone or (purchaseorder_obj.partner_address_id and purchaseorder_obj.partner_address_id.phone or False)

        return res

    def action_schedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

        phonecall = self.pool.get('crm.phonecall')
        purchaseorder_ids = context and context.get('active_ids') or []
        purchaseorder_pool = self.pool.get('purchase.order')
        agenda_obj = self.browse(cr, uid, ids, context=context)[0]

        purchaseorder_pool.agenda_ligacao(cr, uid, purchaseorder_ids, agenda_obj.date, agenda_obj.name, \
                agenda_obj.note, agenda_obj.phone, agenda_obj.user_id and agenda_obj.user_id.id or False, \
                acao=agenda_obj.action, context=context)

        return {'type': 'ir.actions.act_window_close'}


crm_purchaseorder2phonecall()