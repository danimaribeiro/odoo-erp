# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D



class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def _field_readonly(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        nome_campo = nome_campo.replace('_readonly', '')

        for obj in self.browse(cr, uid, ids, context=context):
            if nome_campo[-3:] == '_id':
                campo = getattr(obj, nome_campo, False)

                if campo:
                    res[obj.id] = campo.id
                else:
                    res[obj.id] = False

            else:
                res[obj.id] = getattr(obj, nome_campo, False)

            if getattr(obj, nome_campo, False):
                print('foto', getattr(obj, nome_campo, False))

        return res

    _columns = {
        'quantidade_pontos': fields.integer(u'Quantidade de pontos'),
        'calcula_pontos_venda': fields.boolean(u'Calcula pontos?'),
        'agrupamento_id': fields.many2one('sale.agrupamento', u'Agrupamento'),
        'product_image_readonly': fields.function(_field_readonly, type='text', string=u'Foto', store=False),
        'nome_generico': fields.char(u'Nome genérico', size=60, select=True),
    }


product_product()
