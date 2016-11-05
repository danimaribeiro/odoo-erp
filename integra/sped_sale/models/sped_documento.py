# -*- encoding: utf-8 -*-


from osv import osv, fields
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID


class sped_documento(osv.Model):
    _inherit = 'sped.documento'
    _name = 'sped.documento'

    _columns = {
        'sale_order_ids': fields.many2many('sale.order', 'sale_order_sped_documento', 'sped_documento_id', 'sale_order_id', string=u'Orçamentos'),
    }

    def depois_cancelar(self, cr, uid, ids, dados={}, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            cr.execute('delete from sale_order_sped_documento where sped_documento_id = {id}'.format(id=doc_obj.id))

        return


sped_documento()
