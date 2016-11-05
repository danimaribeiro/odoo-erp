# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_tipo_dia(osv.Model):
    _name = 'hr.tipo.dia'
    _description = u'Cadastro de tipos de dias'
    _rec_name = 'codigo'
    _order = 'descricao'


    _columns = {
        'codigo': fields.char(u'Código', size=2),
        'descricao': fields.char(u'Descrição', size=30),
    }


hr_tipo_dia()
