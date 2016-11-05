# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_rubrica_rescisao(orm.Model):
    _name = 'hr.rubrica.rescisao'
    _description = u'Rubrica para rescisão'
    _rec_name = 'nome'
    _order = 'codigo'

    #_name_search = 'codigo'

    def _get_nome_funcao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            texto = u'[' + obj.codigo + '] '
            texto += obj.descricao

            res[obj.id] = texto

        return res

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('codigo', 'ilike', texto),
            ('descricao', 'ilike', texto),
        ]

        return procura

    def _get_sinal_funcao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.codigo < 100:
                sinal = '+'
            else:
                sinal = '-'

            res[obj.id] = sinal

        return res

    _columns = {
        'codigo': fields.char(u'Código', 7, select=True),
        'descricao': fields.text (u'Descrição'),
        'nome': fields.function(_get_nome_funcao, type='char', size=256, string=u'Nome', store=False, fnct_search=_procura_nome),
        'sinal': fields.function(_get_sinal_funcao, type='char', size=1, string=u'Sinal', store=True),
    }

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)',
            u'O Código não pode se repetir!'),
    ]


hr_rubrica_rescisao()
