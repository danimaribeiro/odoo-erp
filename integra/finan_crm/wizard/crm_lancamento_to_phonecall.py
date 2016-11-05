# -*- coding: utf-8 -*-

from osv import osv, fields
import time


class crm_lancamento2phonecall(osv.osv_memory):
    _name = 'crm.lancamento2phonecall'
    _inherit = 'crm.phonecall2phonecall'
    _description = u'Lançamento para ligação telefônica'

    _columns = {
        'action': fields.selection([('schedule','Agendar uma ligação'), ('log','Registrar uma ligação')], 'Action', required=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        lancamento_pool = self.pool.get('finan.lancamento')

        record_ids = context and context.get('active_ids', []) or []
        res = {}
        res['action'] = 'schedule'
        res['date'] = time.strftime('%Y-%m-%d %H:%M:%S')

        for lancamento_obj in lancamento_pool.browse(cr, uid, record_ids, context=context):
            if 'name' in fields:
                if lancamento_obj.tipo == 'R':
                    nome = u'Conta a receber nº ' + lancamento_obj.numero_documento
                else:
                    nome = u'Conta a pagar nº ' + lancamento_obj.numero_documento

                res['name'] = nome

            if 'user_id' in fields:
                res['user_id'] = uid

            if 'partner_id' in fields:
                res['partner_id'] = lancamento_obj.partner_id and lancamento_obj.partner_id.id or False

            if 'phone' in fields:
                res['phone'] = lancamento_obj.partner_fone or (lancamento_obj.res_partner_address_id and lancamento_obj.res_partner_address_id.phone or False)

        return res

    def action_schedule(self, cr, uid, ids, context=None):
        value = {}
        if context is None:
            context = {}

        phonecall = self.pool.get('crm.phonecall')
        lancamento_ids = context and context.get('active_ids') or []
        lancamento_pool = self.pool.get('finan.lancamento')
        agenda_obj = self.browse(cr, uid, ids, context=context)[0]

        lancamento_pool.agenda_ligacao(cr, uid, lancamento_ids, agenda_obj.date, agenda_obj.name, \
                agenda_obj.note, agenda_obj.phone, agenda_obj.user_id and agenda_obj.user_id.id or False, \
                acao=agenda_obj.action, context=context)

        return {'type': 'ir.actions.act_window_close'}


crm_lancamento2phonecall()