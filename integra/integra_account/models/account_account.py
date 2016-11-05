# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class account_account(osv.Model):
    _name = 'account.account'
    _inherit = 'account.account'
    _description = u'Conta contábil'

    def _get_company_currency(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        currency_pool = self.pool.get('res.currency')
        reais_id = currency_pool.search(cr, 1, [('name', '=', 'BRL')])[0]
        reais_obj = currency_pool.browse(cr, 1, reais_id)

        for rec in self.browse(cr, uid, ids, context=context):
            if rec.company_id:
                result[rec.id] = (rec.company_id.currency_id.id,rec.company_id.currency_id.symbol)
            else:
                result[rec.id] = (reais_obj.id, reais_obj.symbol)

        return result

    #_columns = {
        #'company_id': fields.many2one('res.company', 'Company', required=False),
    #}

    def recalcula_ordem_parent_left_parent_right(self, cr, uid, ids, context):
        for obj in self.browse(cr, uid, self.search(cr, uid, [], order='id')):
            self.write(cr, uid, obj.id, {'name': obj.name + ' '})

        for obj in self.browse(cr, uid, self.search(cr, uid, [], order='id')):
            self.write(cr, uid, obj.id, {'name': obj.name.strip()})


account_account()
