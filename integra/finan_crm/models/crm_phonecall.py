# -*- coding: utf-8 -*-

from osv import fields, osv

class crm_phonecall(osv.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    _columns = {
        'finan_lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro')
    }


crm_phonecall()
