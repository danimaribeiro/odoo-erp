# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_motivo_alteracao_contratual(osv.Model):
    _name = 'hr.motivo.alteracao.contratual'
    _description = u'Motivos de alteração contratual'
    _rec_name = 'descricao'
    _order = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=30),
    }

    _sql_constraints = [
        ('descricao_unique', 'unique(descricao)',
            u'O motivo não pode se repetir!'),
    ]


hr_motivo_alteracao_contratual()
