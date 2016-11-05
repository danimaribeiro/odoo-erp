# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv



class sale_order_line(orm.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    _order = 'order_id, tipo_item, agrupamento_id, sequence, id'

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

        return res

    _columns = {
        'tipo_os_id': fields.related('order_id', 'tipo_os_id', type='many2one', relation='sale.tipo.os', string=u'Tipo da OS'),
        'tipo_os_tipo': fields.related('order_id', 'tipo_os_tipo', type='char', string=u'Tipo da OS (venda, locação, OS)'),
        'agrupamento_id': fields.many2one('sale.agrupamento', u'Agrupamento'),
        #'product_image': fields.related('product_id', 'product_image', type='binary', string=u'Foto', store=False),
        #'product_image_readonly': fields.function(_field_readonly, type='binary', string=u'Foto', store=False),
        'sequence': fields.integer(u'Sequência no agrupamento'),
        'parent_id': fields.many2one('sale.order.line', u'Acessório de', ondelete='cascade'),
        'cobrar': fields.boolean(u'Cobrar?'),
    }

    _defaults = {
        'sequence': 100,
        'cobrar': True,
    }

    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context={}):
        #print('context antes', context)
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        #print('context depois', context)

        if not product_id:
            return res

        produto_pool = self.pool.get('product.product')
        produto_obj = produto_pool.browse(cr, uid, product_id)

        if 'agrupamento_id' not in context or not context['agrupamento_id']:
            if produto_obj.agrupamento_id:
                res['value']['agrupamento_id'] = produto_obj.agrupamento_id.id

            else:
                res['value']['agrupamento_id'] = False

        if getattr(produto_obj, 'nome_generico', False):
            res['value']['name'] = u'[' + produto_obj.default_code
            res['value']['name'] += u'] ' + produto_obj.nome_generico

        if 'acessorio_selecao_ids' in context and getattr(produto_obj, 'acessorio_obrigatorio_ids', False):
            acessorio_selecao_ids = context['acessorio_selecao_ids']

            for acessorio_obj in produto_obj.acessorio_obrigatorio_ids:
                if acessorio_obj.acessorio_id.id not in acessorio_selecao_ids[0][2]:
                    acessorio_selecao_ids[0][2].append(acessorio_obj.acessorio_id.id)

            res['value']['acessorio_selecao_ids'] = acessorio_selecao_ids

        #if produto_obj.product_image:
            #print('foto')
            #print(produto_obj.product_image)
            #res['value']['product_image_readonly'] = produto_obj.product_image

        return res


sale_order_line()
