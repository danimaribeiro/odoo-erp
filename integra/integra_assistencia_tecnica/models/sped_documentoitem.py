# -*- coding: utf-8 -*-


from osv import orm, fields, osv



class sped_documentoitem(osv.Model):
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    _columns = {
        'os_id': fields.many2one('ordem.servico', u'Ordem de Serviço'),
        
    }

 
sped_documentoitem()

