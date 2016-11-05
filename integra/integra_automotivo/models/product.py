# -*- coding: utf-8 -*-


from osv import osv, fields


class product_product(osv.osv):
    _name = 'product.product'
    _description = 'Product'
    _inherit = 'product.product'

    _columns = {
        'fabricante_id': fields.many2one('res.partner', u'Fabricante'),
        'codigo_fabricante': fields.char(u'Código fabricante', size=30),
        'codigo_montadora': fields.char(u'Código montadora', size=30),
        'validade_km_urbano': fields.float(u'Validade em km urbano'),
        'validade_km_rodoviario': fields.float(u'Validade em km rodoviário'),
        'validade_km_rural': fields.float(u'Validade em km rural'),
        'validade_km_misto': fields.float(u'Validade em km misto'),
        'validade_meses': fields.float(u'Validade em meses'),
        #
        # Para serviçoss
        #
        'tempo_execucao': fields.float(u'Tempo de execução'),
        'terceirizado': fields.boolean(u'Terceirizado?'),

        'similar_ids': fields.many2many('product.product', 'product_similar', 'product_id', 'similar_id', 'Similares'),
    }


product_product()