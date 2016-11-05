# -*- coding: utf-8 -*-

from osv import fields, osv

class crm_phonecall(osv.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    
    _columns = {
        'ordem_servico_id': fields.many2one('ordem.servico', u'Ordem de serviço')
    }


crm_phonecall()
