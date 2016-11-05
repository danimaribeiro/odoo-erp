# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class product_category(orm.Model):
    _inherit = "product.category"

    def _busca_conta_propriedade(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for pc_obj in self.browse(cr, uid, ids):
            res[pc_obj.id] = False

            if nome_campo == 'account_receita_id' and pc_obj.property_account_income_categ:
                res[pc_obj.id] = pc_obj.property_account_income_categ.id
            elif nome_campo == 'account_despesa_id' and pc_obj.property_account_expense_categ:
                res[pc_obj.id] = pc_obj.property_account_expense_categ.id

        return res

    _columns = {
        #'account_receita_id': fields.function(_busca_conta_propriedade, type='many2one', relation='account.account', string=u'Conta de receita', method=True, store=True, select=True),
        #'account_despesa_id': fields.function(_busca_conta_propriedade, type='many2one', relation='account.account', string=u'Conta de despesa', method=True, store=True, select=True),
        'account_receita_id': fields.many2one('account.account', string=u'Conta de receita'),
        'account_despesa_id': fields.many2one('account.account', string=u'Conta de despesa'),

        'conta_receita_id': fields.many2one('finan.conta', string=u'Conta de receita'),
        'conta_despesa_id': fields.many2one('finan.conta', string=u'Conta de despesa'),
}


product_category()


class product_template(orm.Model):
    _inherit = "product.template"

    def _busca_conta_propriedade(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for pc_obj in self.browse(cr, uid, ids):
            res[pc_obj.id] = False

            if nome_campo == 'account_receita_id' and pc_obj.property_account_income:
                res[pc_obj.id] = pc_obj.property_account_income.id
            elif nome_campo == 'account_despesa_id' and pc_obj.property_account_expense:
                res[pc_obj.id] = pc_obj.property_account_expense.id

        return res

    _columns = {
        #'account_receita_id': fields.function(_busca_conta_propriedade, type='many2one', relation='account.account', string=u'Conta de receita', method=True, store=True, select=True),
        #'account_despesa_id': fields.function(_busca_conta_propriedade, type='many2one', relation='account.account', string=u'Conta de despesa', method=True, store=True, select=True),
        'account_receita_id': fields.many2one('account.account', string=u'Conta de receita'),
        'account_despesa_id': fields.many2one('account.account', string=u'Conta de despesa'),

        'conta_receita_id': fields.many2one('finan.conta', string=u'Conta de receita'),
        'conta_despesa_id': fields.many2one('finan.conta', string=u'Conta de despesa'),
    }


product_template()
