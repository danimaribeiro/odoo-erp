# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_partner_category(osv.Model):
    _name = 'res.partner.category'
    _inherit = 'res.partner.category'
    #_parent_store = True
    #_parent_order = 'name'
    #_order = 'parent_left'
    _rec_name = 'complete_name'

    #def name_get(self, cr, uid, ids, context=None):
        #"""Return the categories' display name, including their direct
           #parent by default.

        #:param dict context: the ``partner_category_display`` key can be
                             #used to select the short version of the
                             #category name (without the direct parent),
                             #when set to ``'short'``. The default is
                             #the long version."""
        #if context is None:
            #context = {}
        #if context.get('partner_category_display') == 'short':
            #return super(res_partner_category, self).name_get(cr, uid, ids, context=context)
        #reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        #res = []
        #for record in reads:
            #name = record['name']
            #if record['parent_id']:
                #name = record['parent_id'][1]+' / '+name
            #res.append((record['id'], name))
        #return res

    #def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=100):
        #if name:
            ## Be sure name_search is symetric to name_get
            #name = name.split(' / ')[-1]
            #ids = self.search(cr, uid, ['|', ('name', operator, name), ('complete_name', operator, name)] + args, limit=limit, context=context)
        #else:
            #ids = self.search(cr, uid, args, limit=limit, context=context)

        #return self.name_get(cr, uid, ids, context)

    #def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        #res = self.name_get(cr, uid, ids, context=context)
        #return dict(res)

    _columns = {
        #'name': fields.char(u'Nome da categoria', required=True, size=64, translate=False, select=True),
        #'parent_id': fields.many2one('res.partner.category', 'Parent Category', select=True, ondelete='cascade'),
        #'complete_name': fields.function(_name_get_fnc, type='char', size=256, string=u'Nome da categoria', store=True, select=True),
        #'child_ids': fields.one2many('res.partner.category', 'parent_id', 'Child Categories'),
        #'active' : fields.boolean('Active', help="The active field allows you to hide the category without removing it."),
        #'parent_left' : fields.integer('Left parent', select=True),
        #'parent_right' : fields.integer('Right parent', select=True),
        #'partner_ids': fields.many2many('res.partner', 'res_partner_category_rel', 'category_id', 'partner_id', 'Partners'),
    }
    #_constraints = [
        #(osv.osv._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    #]
    #_defaults = {
        #'active' : lambda *a: 1,
    #}


res_partner_category()
