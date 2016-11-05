# -*- coding: utf-8 -*-

from osv import fields, osv

class crm_phonecall(osv.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    _columns = {
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro')
    }


crm_phonecall()


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'crm_phonecall_ids': fields.one2many('crm.phonecall', 'lancamento_id', u'Ligações telefônicas'),
    }


finan_lancamento()
