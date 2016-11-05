# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D


class crm_lead(orm.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    _columns = {
        'qtd_cameras': fields.integer(u'Quantidade de câmeras'),
        'vr_unitario_camera': fields.float(u'Valor por câmera'),
        'qtd_adesoes': fields.integer(u'Quantidade de adesões'),
        'vr_unitario_adesao': fields.float(u'Valor por adesão'),
        'vr_total_adesao': fields.float(u'Valor de adesões'),
        'hr_department_id': fields.many2one('hr.department', u'NAL'),
    }

    def onchange_receita(self, cr, uid, ids, qtd_cameras=0, vr_unitario_camera=0, context={}):
        valores = {}
        res = {'value': valores}

        valores['planned_revenue'] = D(qtd_cameras or 0) * D(vr_unitario_camera or 0)

        return res

    def onchange_adesao(self, cr, uid, ids, qtd_adesoes=0, vr_unitario_adesao=0, context={}):
        valores = {}
        res = {'value': valores}

        valores['vr_total_adesao'] = D(qtd_adesoes or 0) * D(vr_unitario_adesao or 0)

        return res


crm_lead()


class crm_make_sale(osv.osv_memory):
    _name = 'crm.make.sale'
    _inherit = 'crm.make.sale'

    def makeOrder(self, cr, uid, ids, context={}):
        res = super(crm_make_sale, self).makeOrder(cr, uid, ids, context=context)
        crm_pool = self.pool.get('crm.lead')
        crm_id = context.get('active_id', False)
        sale_pool = self.pool.get('sale.order')

        if 'res_id' in res:
            sale_id = res['res_id']
            crm_obj = crm_pool.browse(cr, uid, crm_id)

            if crm_obj.hr_department_id:
                sale_pool.write(cr, uid, sale_id, {'hr_department_id': crm_obj.hr_department_id.id})

        return res


crm_make_sale()

