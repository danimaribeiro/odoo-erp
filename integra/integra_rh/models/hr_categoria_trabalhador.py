# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_categoria_trabalhador(osv.Model):
    _name = 'hr.categoria.trabalhador'
    _description = u'Categoria Trabalhador'
    _order = 'codigo'
    _rec_name = 'descricao'

    
    _columns = {
        'codigo': fields.char(u'Código', 6, select=True),
        'descricao': fields.text(u'Descrição', select=True),       
      
    }   
    
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)',
            u'O Código não pode se repetir!'),
    ]


