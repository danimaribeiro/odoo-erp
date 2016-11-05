# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import fields, osv, orm


class hr_fecha_holerites(osv.osv_memory):
    _description = u'Fecha cálculo de holerites de funcionários'
    _name = 'hr.fecha.holerites'
    _inherit = 'ir.wizard.screen'
   

    _columns = {

    }

    _defaults = {

    }

    def fecha_holerites(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        holerite_ids = context['active_ids']
        #holerites_ids = tuple(holerites_ids)

        if not holerite_ids:
            return {'type': 'ir.actions.act_window_close'}

        self.pool.get('hr.payslip').fecha_holerite(cr, uid, holerite_ids, context=context)
            
        return

    def reabre_holerites(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        holerite_ids = context['active_ids']
        #holerites_ids = tuple(holerites_ids)

        if not holerite_ids:
            return {'type': 'ir.actions.act_window_close'}

        self.pool.get('hr.payslip').abre_holerite(cr, uid, holerite_ids, context=context)
            
        return
       

hr_fecha_holerites()
