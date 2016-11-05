# -*- encoding: utf-8 -*-

from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D


class sale_order(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'representante_id': fields.many2one('res.users', u'Representante'),
        'revenda_id': fields.many2one('res.partner', u'Revenda'),
        #'vendedor_id': fields.many2one('res.users', u'Vendendor'),
        'comissao_vendedor': fields.float(u'Comissão vendedor'),
        'comissao_representante': fields.float(u'Comissão representante'),
        'comissao_revenda': fields.float(u'Comissão revenda'),
        'comissao_total': fields.float(u'Comissão total'),
    }

    def onchange_partner_id(self, cr, uid, ids, part):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)

        if not part:
            return res

        res['value']['representante_id'] = res['value']['user_id']
        res['value']['user_id'] = uid

        partner_obj = self.pool.get('res.partner').browse(cr, uid, part)

        if partner_obj.parent_id:
            res['value']['revenda_id'] = partner_obj.parent_id.id

        return res

    def create(self, cr, uid, dados, context={}):
        if 'representante_id' not in dados:
            res_repr = self.onchange_partner_id(cr, uid, [], dados['partner_id'])

            dados['representante_id'] = res_repr['value']['representante_id']

        res = super(sale_order, self).create(cr, uid, dados, context=context)
        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)

        #
        # Calcula a comissão
        #
        equipe_pool = self.pool.get('crm.case.section')

        for order_obj in self.browse(cr, uid, ids):
            if order_obj.state != 'done':
                if order_obj.section_id:
                    equipe_obj = order_obj.section_id
                else:
                    equipe_ids = equipe_pool.search(cr, uid, [], order='id')
                    equipe_obj = equipe_pool.browse(cr, uid, equipe_ids[0])


                comissao_vendedor = D(0)
                comissao_representante = D(0)
                comissao_revenda = D(0)
                valor_pedido = D(order_obj.amount_total or 0)

                if equipe_obj.comissao_vendedor:
                    comissao_vendedor = valor_pedido * D(equipe_obj.comissao_vendedor) / D(100)
                    comissao_vendedor = comissao_vendedor.quantize(D('0.01'))

                if equipe_obj.comissao_representante:
                    comissao_representante = valor_pedido * D(equipe_obj.comissao_representante) / D(100)
                    comissao_representante = comissao_representante.quantize(D('0.01'))

                if equipe_obj.comissao_revenda:
                    comissao_revenda = valor_pedido * D(equipe_obj.comissao_revenda) / D(100)
                    comissao_revenda = comissao_revenda.quantize(D('0.01'))

                comissao_total = comissao_vendedor + comissao_representante + comissao_revenda

                dados_comissao = {
                    'comissao_vendedor': comissao_vendedor,
                    'comissao_representante': comissao_representante,
                    'comissao_revenda': comissao_revenda,
                    'comissao_total': comissao_total,
                    'id': order_obj.id,
                }

                cr.execute('''
                    update sale_order set
                        comissao_vendedor = {comissao_vendedor},
                        comissao_representante = {comissao_representante},
                        comissao_revenda = {comissao_revenda},
                        comissao_total = {comissao_total}
                    where
                        id = {id};
                '''.format(**dados_comissao))

        return res


sale_order()
