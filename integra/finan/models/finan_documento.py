# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields


POSTERGACAO_EXATA = 'EXATA'
POSTERGACAO_POSTERGA = 'POSTERGA'
POSTERGACAO_ANTECIPA = 'ANTECIPA'

TIPO_POSTERGACAO = (
    (POSTERGACAO_EXATA, 'Data Exata'),
    (POSTERGACAO_POSTERGA, 'Postergar'),
    (POSTERGACAO_ANTECIPA, 'Antecipar'),
)


class finan_documento(orm.Model):
    _description = u'Tipos de Documento'
    _name = 'finan.documento'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Descrição', size=30, required=True),
        'postergacao': fields.selection(TIPO_POSTERGACAO, u'Postergação', required=True),
    }

    _sql_constraints = [
        ('nome_unique', 'unique(nome)',
            u'A descrição não pode se repetir!'),
    ]

    _defaults = {
        'postergacao': POSTERGACAO_EXATA,
        }

    def _cria_id_novo(self, cr, uid, nome):
        folha_ids = self.search(cr, uid, [('nome', 'in', [nome.upper(), nome.lower()])])

        if folha_ids:
            return folha_ids[0]

        dados = {
            'nome': nome.upper(),
            'postergacao': 'POSTERGA',
        }
        folha_id = self.create(cr, uid, dados)
        return folha_id


finan_documento()
