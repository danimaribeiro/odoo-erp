# -*- coding: utf-8 -*-

from osv import fields, osv
from integra_rh.models.hr_payslip_input import mes_atual, primeiro_ultimo_dia_mes


class finan_gera_nota(osv.osv_memory):
    _name = 'sale.gera_nota'
    _inherit = 'sale.gera_nota'

    def _get_pedido_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        if ids:
            gera_nota_obj = self.browse(cr, uid, ids[0])
            data_inicial = gera_nota_obj.data_inicial
            data_final = gera_nota_obj.data_final

            if gera_nota_obj.company_id:
                company_id = gera_nota_obj.company_id.id
            else:
                company_id = False

            if gera_nota_obj.partner_id:
                partner_id = gera_nota_obj.partner_id.id
            else:
                partner_id = False

            if gera_nota_obj.pedido_id:
                pedido_id = gera_nota_obj.pedido_id.id
            else:
                pedido_id = False

        else:
            if 'data_inicial' not in context or 'data_final' not in context:
                return {}

            data_inicial = context['data_inicial']
            data_final = context['data_final']

            if not data_inicial or not data_final:
                raise osv.except_osv(u'Atenção', u'É preciso escolher um período!')

            company_id = context.get('company_id', False)
            pedido_id = context.get('pedido_id', False)

        if pedido_id:
            busca = [
                ('id', '=', pedido_id),
                ('state', 'in', ['manual', 'done']),
                ('sped_documento_ids', '=', False),
            ]

        else:
            busca = [
                ('date_order', '>=', data_inicial),
                ('date_order', '<=', data_final),
                ('state', 'in', ['manual', 'done']),
                ('sped_documento_ids', '=', False),
            ]

        if company_id:
            busca += [('company_id', '=', company_id)]

        if partner_id:
            busca += [('partner_id', '=', partner_id)]

        pedido_ids = self.pool.get('sale.order').search(cr, uid, busca)

        res = {}
        if ids:
            for id in ids:
                res[id] = pedido_ids
        else:
            res = pedido_ids

        return res
    
    _columns = {
        'stock_picking_id': fields.many2one('stock.picking', u'Lista de separação'),
    }

    def gera_notas(self, cr, uid, ids, context=None):
        pedidos = context['pedido_ids']
        pedido_ids = []
        gera_nota_obj = self.browse(cr, uid, ids[0])

        for operacao, pedido_id, valores in pedidos:
            pedido_ids += [pedido_id]

        #
        # Agrupa os pedidos por cliente
        #
        pedidos_cliente = {}
        for pedido_obj in self.pool.get('sale.order').browse(cr, uid, pedido_ids):
            cnpj = pedido_obj.partner_id.cnpj_cpf
            if cnpj not in pedidos_cliente:
                pedidos_cliente[cnpj] = [pedido_obj]
            else:
                pedidos_cliente[cnpj].append(pedido_obj)

        #
        # Agora, gera as notas propriamente ditas
        #
        for cnpj in pedidos_cliente:
            if len(pedidos_cliente[cnpj]) == 1:
                pedido_obj = pedidos_cliente[cnpj][0]
                print('cnpj', cnpj)

                if gera_nota_obj.stock_picking_id:
                    pedido_obj.gera_notas(context={'stock_picking_id': gera_nota_obj.stock_picking_id.id})
                else:
                    pedido_obj.gera_notas()

            else:
                pass


finan_gera_nota()
