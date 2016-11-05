# -*- encoding: utf-8 -*-


from osv import osv, fields

class midia_leilao(osv.osv):
    _name = 'midia.leilao'
    _description = 'midia.leilao'
    _rec_name = 'midia' 

    
    _columns = {
        'midia': fields.char(u'midia', size=30 ),
        'order_ids': fields.one2many('sale.order','midia_id', u'Midia'),
      }

    _defaults = {
        
    }        
    
midia_leilao()