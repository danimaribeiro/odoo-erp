# -*- coding: utf-8 -*-

from osv import osv, fields
import time


class crm_ordem_servico2phonecall(osv.osv_memory):
    _name = 'crm.ordem_servico2phonecall'
    _inherit = 'crm.phonecall2phonecall'

    _columns = {
        'action': fields.selection([('schedule','Agendar uma ligação'), ('log','Registrar uma ligação')], 'Action', required=True),
    }

    def default_get(self, cr, uid, fields, context={}):
        ordem_servico_pool = self.pool.get('ordem.servico')

        record_ids = context and context.get('active_ids', []) or []
        res = {}
        res['action'] = 'schedule'
        res['date'] = time.strftime('%Y-%m-%d %H:%M:%S')

        for ordem_servico_obj in ordem_servico_pool.browse(cr, uid, record_ids, context=context):
            if 'name' in fields:
                nome = u'OS nº ' + ordem_servico_obj.codigo
                res['name'] = nome

            if 'user_id' in fields:
                res['user_id'] = uid

            if 'partner_id' in fields:
                res['partner_id'] = ordem_servico_obj.partner_id and ordem_servico_obj.partner_id.id or False

            if 'phone' in fields:
                res['phone'] = ordem_servico_obj.partner_fone

        return res

    def action_schedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

        phonecall = self.pool.get('crm.phonecall')
        ordem_servico_ids = context and context.get('active_ids') or []
        ordem_servico_pool = self.pool.get('ordem.servico')
        agenda_obj = self.browse(cr, uid, ids, context=context)[0]

        ordem_servico_pool.agenda_ligacao(cr, uid, ordem_servico_ids, agenda_obj.date, agenda_obj.name, \
                agenda_obj.note, agenda_obj.phone, agenda_obj.user_id and agenda_obj.user_id.id or False, \
                acao=agenda_obj.action, context=context)

        return {'type': 'ir.actions.act_window_close'}


crm_ordem_servico2phonecall()