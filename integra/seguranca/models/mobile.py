# -*- encoding: utf-8 -*-


from openerp.osv import osv, fields


class integra_mobile(osv.osv_memory):
    _name = 'integra.mobile'
    _description = u'Controle de aplicações Mobile'

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', size=18, string=u'CNPJ/CPF', select=True, store=True),
        'endereco': fields.char(u'Endereço web', size=255),
        'banco_dados': fields.char(u'Banco de Dados', size=255),
    }


integra_mobile()
