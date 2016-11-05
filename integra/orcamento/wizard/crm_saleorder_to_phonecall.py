# -*- coding: utf-8 -*-

from osv import osv, fields
import time


class crm_saleorder2phonecall(osv.osv_memory):
    _name = 'crm.saleorder2phonecall'
    _inherit = 'crm.phonecall2phonecall'
    _description = u'Lançamento para ligação telefônica'

    _columns = {
        'action': fields.selection([('schedule','Agendar uma ligação'), ('log','Registrar uma ligação')], 'Action', required=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        saleorder_pool = self.pool.get('sale.order')

        record_ids = context and context.get('active_ids', []) or []
        res = {}
        res['action'] = 'schedule'
        res['date'] = time.strftime('%Y-%m-%d %H:%M:%S')

        for saleorder_obj in saleorder_pool.browse(cr, uid, record_ids, context=context):
            if 'name' in fields:
                if saleorder_obj.state == 'draft':
                    nome = u'Orçamento nº ' + saleorder_obj.name
                else:
                    nome = u'Pedido nº ' + saleorder_obj.name

                res['name'] = nome

            if 'user_id' in fields:
                res['user_id'] = saleorder_obj.user_id.id or uid

            if 'partner_id' in fields:
                res['partner_id'] = saleorder_obj.partner_id and saleorder_obj.partner_id.id or False

            if 'phone' in fields:
                res['phone'] = saleorder_obj.partner_fone or (saleorder_obj.partner_invoice_id and saleorder_obj.partner_invoice_id.phone or False)

        return res

    def action_schedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

        phonecall = self.pool.get('crm.phonecall')
        saleorder_ids = context and context.get('active_ids') or []
        saleorder_pool = self.pool.get('sale.order')
        agenda_obj = self.browse(cr, uid, ids, context=context)[0]

        saleorder_pool.agenda_ligacao(cr, uid, saleorder_ids, agenda_obj.date, agenda_obj.name, \
                agenda_obj.note, agenda_obj.phone, agenda_obj.user_id and agenda_obj.user_id.id or False, \
                acao=agenda_obj.action, context=context)

        return {'type': 'ir.actions.act_window_close'}


crm_saleorder2phonecall()