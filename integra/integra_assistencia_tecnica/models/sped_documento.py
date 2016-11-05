# -*- coding: utf-8 -*-


from osv import orm, fields, osv



class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
    }

 
sped_documento()
