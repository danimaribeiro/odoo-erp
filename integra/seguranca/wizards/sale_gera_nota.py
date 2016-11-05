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

        sql = '''
        select distinct
            so.id

        from
            sale_order so
            join product_pricelist lp on lp.id = so.pricelist_id
            left join sale_order_sped_documento sosd on sosd.sale_order_id = so.id
            left join sped_documento d on d.id = sosd.sped_documento_id

        where
            (coalesce(lp.meses_retorno_locacao, 0) = 0)
            and so.libera_faturamento_contrato = True
            and (sosd.sale_order_id is null or d.situacao not in ('00', '01'))
        '''
        #(coalesce(lp.meses_retorno_locacao, 0) = 0 or coalesce(so.vr_total_servicos, 0) > 0)

        if pedido_id:
            sql += '''
            and so.id = {pedido_id}
            '''.format(pedido_id=pedido_id)

        else:
            sql += '''
            and so.date_order between '{data_inicial}' and '{data_final}'
            '''.format(data_inicial=data_inicial, data_final=data_final)

        if company_id:
            sql += '''
            and so.company_id = {company_id}
            '''.format(company_id=company_id)

        if partner_id:
            sql += '''
            and so.partner_id = {partner_id}
            '''.format(partner_id=partner_id)

        pedido_pool = self.pool.get('sale.order')

        cr.execute(sql)
        dados = cr.fetchall()
        pedido_ids = []
        for pedido_id, in dados:
            pedido_ids.append(pedido_id)

        res = {}
        if ids:
            for id in ids:
                res[id] = pedido_ids
        else:
            res = pedido_ids

        return res

    _columns = {
        'pedido_ids': fields.function(_get_pedido_ids, method=True, type='one2many', string=u'Pedidos', relation='sale.order'),
    }

    def gera_notas(self, cr, uid, ids, context={}):
        pedidos = context['pedido_ids']
        pedido_ids = []

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
            for pedido_obj in pedidos_cliente[cnpj]:
                #
                # Verificamos se vai gerar somente NF de serviço, no caso de locação
                #
                if pedido_obj.pricelist_id.meses_retorno_locacao:
                    context['soh_servicos'] = True
                else:
                    context['soh_servicos'] = False

                pedido_obj.gera_notas(context=context)


finan_gera_nota()
