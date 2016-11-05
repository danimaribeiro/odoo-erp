# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_aviso_previo_proporcional(osv.Model):
    _name = 'hr.aviso_previo_proporcional'
    _description = u'Aviso prévio proporcional'
    _rec_name = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=30),
        'company_ids': fields.many2many('res.company', 'hr_aviso_previo_proporcional_company', 'avisoprevioproporcional_id', 'company_id', string=u'Empresas'),
        'avisoprevioproporcional_item_ids': fields.one2many('hr.aviso_previo_proporcional_item', 'avisoprevioproporcional_id', u'Itens'),
    }


hr_aviso_previo_proporcional()



class hr_aviso_previo_proporcional_item(osv.Model):
    _name = 'hr.aviso_previo_proporcional_item'
    _description = u'Item do aviso prévio proporcional'
    _rec_name = 'descricao'
    _order = 'anos, dias'

    _columns = {
        'avisoprevioproporcional_id': fields.many2one('hr.aviso_previo_proporcional', u'Tabela'),
        'anos': fields.integer(u'Anos trabalhados'),
        'dias': fields.integer(u'Dias de aviso'),
    }


hr_aviso_previo_proporcional_item()
