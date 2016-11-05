# -*- encoding: utf-8 -*-


from osv import osv, fields


class crm_lead(osv.Model):
    _inherit = 'crm.lead'

    _columns = {
        'receita_venda': fields.float(u'Receita de vendas'),
        'receita_locacao': fields.float(u'Receita de locação'),
    }

    def onchange_receita(self, cr, uid, ids, receita_venda=0, receita_locacao=0, context={}):
        valores = {}
        res = {'value': valores}

        valores['planned_revenue'] = receita_venda + receita_locacao

        return res


crm_lead()
