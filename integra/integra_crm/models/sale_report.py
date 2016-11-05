# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import tools
from osv import fields, osv

class sale_report(osv.osv):
    _name = "sale.report"
    _description = "Sales Orders Statistics"
    _auto = False
    _rec_name = 'date'
    _columns = {
        'date': fields.date('Date Order', readonly=True),
        'date_confirm': fields.date('Date Confirm', readonly=True),
        #'shipped': fields.boolean('Shipped', readonly=True),
        #'shipped_qty_1': fields.integer('Shipped', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        #'product_id': fields.many2one('product.product', 'Product', readonly=True),
        #'product_uom': fields.many2one('product.uom', 'UoM', readonly=True),
        #'product_uom_qty': fields.float('# of Qty', readonly=True),

        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        #'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesman', readonly=True),
        'price_total': fields.float('Total Price', readonly=True),
        'delay': fields.float('Commitment Delay', digits=(16,2), readonly=True),
        'categ_id': fields.many2one('product.category','Category of Product', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'state': fields.selection([
            ('draft', u'Orçamento'),
            ('waiting_date', u'Aguardando agendamento'),
            ('manual', u'Para faturar'),
            ('progress', u'Em andamento'),
            ('shipping_except', u'Exceção de entrega'),
            ('invoice_except', u'Exceção de faturamento'),
            ('done', u'Concluído'),
            ('cancel', u'Cancelado')
            ], 'Order State', readonly=True),
        #'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True),
        #'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
        'prospeccao': fields.integer(u'Prospecção'),
        'base_clientes': fields.integer(u'Base clientes'),
        'origem': fields.char(u'Origem', size=15),
    }
    _order = 'date desc'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report')
        cr.execute("""
            drop view if exists sale_report;
            create or replace view sale_report as (
                select
                    s.id,
                    1 as nbr,
                    s.date_order as date,
                    s.date_confirm as date_confirm,
                    to_char(s.date_order, 'YYYY') as year,
                    to_char(s.date_order, 'MM') as month,
                    to_char(s.date_order, 'YYYY-MM-DD') as day,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.vr_total_margem_desconto as price_total,
                    s.company_id as company_id,
                    extract(epoch from date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date))/(24*60*60)::decimal(16,2) as delay,
                    s.state,
                    case when s.crm_lead_id is null then 0 else 1 end as prospeccao,
                    case when s.crm_lead_id is not null then 0 else 1 end as base_clientes,
                    case when s.crm_lead_id is null then 'Base clientes' else 'Prospecção' end as origem
                from
                    sale_order s
            );
        """)


sale_report()
