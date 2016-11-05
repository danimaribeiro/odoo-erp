# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import fields, osv, orm


class hr_recalcula(osv.osv_memory):
    _description = u'Recalcula Holerites de funcionários'
    _name = 'hr.recalcula'
    _inherit = 'ir.wizard.screen'
   

    _columns = {

    }

    _defaults = {

    }

    def recalcula_holerites(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        holerite_ids = context['active_ids']
        #holerites_ids = tuple(holerites_ids)

        if not holerite_ids:
            return {'type': 'ir.actions.act_window_close'}

        holerite_objs = self.pool.get('hr.payslip').browse(cr, uid, holerite_ids)
        
        print(holerite_objs)
        for holerite_obj in holerite_objs:
            holerite_obj.compute_sheet()
            
        return
       

hr_recalcula()
