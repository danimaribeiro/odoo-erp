# -*- encoding: utf-8 -*-


from osv import osv, fields


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'categoria_comissao_ids': fields.one2many('orcamento.categoria_comissao', 'partner_id', u'Comissões para venda'),
        'categoria_comissao_servico_ids': fields.one2many('orcamento.categoria_comissao_servico', 'partner_id', u'Comissões para serviço'),
    }


res_partner()
