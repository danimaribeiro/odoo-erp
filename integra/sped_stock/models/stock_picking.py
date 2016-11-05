# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from tools.translate import _
import netsvc
import tools
from tools import float_compare
import decimal_precision as dp
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby


class stock_picking(osv.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        #'name': fields.char('Reference', size=64, select=True),
        #'origin': fields.char('Origin', size=64, help="Reference of the document that produced this picking.", select=True),
        #'backorder_id': fields.many2one('stock.picking', 'Back Order of', help="If this picking was split this field links to the picking that contains the other part that has been processed already.", select=True),
        #'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        #'note': fields.text('Notes'),
        #'stock_journal_id': fields.many2one('stock.journal','Stock Journal', select=True),
        #'location_id': fields.many2one('stock.location', 'Location', help="Keep empty if you produce at the location where the finished products are needed." \
                #"Set a location if you produce at a fixed location. This can be a partner location " \
                #"if you subcontract the manufacturing operations.", select=True),
        #'location_dest_id': fields.many2one('stock.location', 'Dest. Location',help="Location where the system will stock the finished products.", select=True),
        #'move_type': fields.selection([('direct', 'Partial Delivery'), ('one', 'All at once')], 'Delivery Method', required=True, help="It specifies goods to be delivered all at once or by direct delivery"),
        #'state': fields.selection([
            #('draft', 'New'),
            #('auto', 'Waiting Another Operation'),
            #('confirmed', 'Waiting Availability'),
            #('assigned', 'Ready to Process'),
            #('done', 'Done'),
            #('cancel', 'Cancelled'),
            #], 'State', readonly=True, select=True,
            #help="* Draft: not confirmed yet and will not be scheduled until confirmed\n"\
                 #"* Confirmed: still waiting for the availability of products\n"\
                 #"* Available: products reserved, simply waiting for confirmation.\n"\
                 #"* Waiting: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n"\
                 #"* Done: has been processed, can't be modified or cancelled anymore\n"\
                 #"* Cancelled: has been cancelled, can't be confirmed anymore"),
        #'min_date': fields.function(get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                 #store=True, type='datetime', string='Expected Date', select=1, help="Expected date for the picking to be processed"),
        #'date': fields.datetime('Order Date', help="Date of Order", select=True),
        'date': fields.date('Order Date', help="Date of Order", select=True),
        #'date_done': fields.datetime('Date Done', help="Date of Completion"),
        #'max_date': fields.function(get_min_max_date, fnct_inv=_set_maximum_date, multi="min_max_date",
                 #store=True, type='datetime', string='Max. Expected Date', select=2),
        #'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        #'auto_picking': fields.boolean('Auto-Picking'),
        #'address_id': fields.many2one('res.partner.address', 'Address', help="Address of partner"),
        #'partner_id': fields.related('address_id','partner_id',type='many2one',relation='res.partner',string='Partner',store=True),
        #'invoice_state': fields.selection([
            #("invoiced", "Invoiced"),
            #("2binvoiced", "To Be Invoiced"),
            #("none", "Not Applicable")], "Invoice Control",
            #select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        #'company_id': fields.many2one('res.company', 'Company', required=True, select=True),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato do cliente'),
    }

    _defaults = {
        #'name': lambda self, cr, uid, context: '/',
        #'state': 'draft',
        #'move_type': 'direct',
        #'type': 'in',
        #'invoice_state': 'none',
        #'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        #'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=c)
    }


stock_picking()
