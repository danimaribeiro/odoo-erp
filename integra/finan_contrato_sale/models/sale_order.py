# -*- encoding: utf-8 -*-

from osv import osv, fields


class sale_order(osv.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    _columns = {
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelete='restrict'),
        'res_partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),
    }

    _defaults = {
        
    }


sale_order()

