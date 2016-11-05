# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_cbo(orm.Model):
    _name = 'hr.cbo'
    _description = u'Classificação Brasileira de Ocupações'
    _rec_name = 'descricao'
    _order = 'ocupacao'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''
        for registro in self.browse(cursor, user_id, ids):
            txt = registro.codigo or ''
            txt += ' - ' 
            txt += registro.ocupacao or ''
            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',('codigo', 'like', texto), ('ocupacao', 'like', texto)
            ]
        return procura


    _columns = {
        'codigo': fields.char(u'Código', 6, select=True),
        'ocupacao': fields.char(u'Ocupação', 140, select=True),
        'descricao': fields.function(_descricao, string=u'CBO', method=True, type='char', fnct_search=_procura_descricao),

    }


hr_cbo()
