# -*- encoding: utf-8 -*-


from osv import osv, fields


class crm_lead(osv.Model):
    _inherit = 'crm.lead'

    def _anuidade(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        for registro in self.browse(cursor, user_id, ids):
            if registro.receita_locacao:
                txt = registro.receita_locacao * 12
            else:
                txt = 0

            retorno[registro.id] = txt

        return retorno

    _columns = {
        'receita_venda': fields.float(u'Implantação'),
        'receita_locacao': fields.float(u'Mensalidade'),
        'anuidade': fields.function(_anuidade, string=u'× 12', method=True, type='float', store=False),
    }

    def onchange_receita(self, cr, uid, ids, receita_venda=0, receita_locacao=0, context={}):
        valores = {}
        res = {'value': valores}

        valores['planned_revenue'] = receita_venda + (receita_locacao * 12)
        valores['anuidade'] = receita_locacao * 12

        return res


crm_lead()
