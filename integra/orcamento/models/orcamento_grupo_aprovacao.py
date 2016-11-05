# -*- coding: utf-8 -*-


from osv import osv, fields


class orcamento_grupo_aprovacao(osv.Model):
    _name = 'orcamento.grupo.aprovacao'
    _order = 'nivel desc, name'

    _columns = {
        'name': fields.char(u'Grupo de aprovação comercial', size=64, select=True),
        'nivel': fields.integer(u'Nível', help_text=u'Nível mais alto tem mais permissão', select=True),
        'usuario_ids': fields.many2many('res.users', 'orcamento_grupo_aprovacao_usuario', 'grupo_id', 'usuario_id', u'Usuários no grupo'),
    }

    def ajusta_permissao(self, cr, uid):
        cr.execute('update res_users set nivel_aprovacao_comercial = 0;')
        cr.execute("""
            update res_users u
            set nivel_aprovacao_comercial = (
                select
                    max(g.nivel)
                from
                    orcamento_grupo_aprovacao_usuario gu
                    join orcamento_grupo_aprovacao g on g.id = gu.grupo_id
                where
                    gu.usuario_id = u.id
                )
        """)

    def create(self, cr, uid, dados, context={}):
        res = super(orcamento_grupo_aprovacao, self).create(cr, uid, dados, context=context)

        self.ajusta_permissao(cr, uid)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(orcamento_grupo_aprovacao, self).write(cr, uid, ids, dados, context=context)

        self.ajusta_permissao(cr, uid)

        return res

    def unlink(self, cr, uid, ids, context={}):
        res = super(orcamento_grupo_aprovacao, self).unlink(cr, uid, ids, context=context)

        self.ajusta_permissao(cr, uid)

        return res


orcamento_grupo_aprovacao()


class orcamento_grupo_aprovacao_usuario(osv.Model):
    _name = 'orcamento.grupo.aprovacao.usuario'
    _description = u'Usuários do grupo de aprovação'
    _order = 'grupo_id, user_id'

    _columns = {
        'grupo_id': fields.many2one('orcamento.grupo.aprovacao', u'Grupo de aprovação', ondelete='cascade'),
        'usuario_id': fields.many2one('res.users', u'Usuário'),
    }


orcamento_grupo_aprovacao_usuario()


class res_users(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    _columns = {
        'nivel_aprovacao_comercial': fields.integer(u'Nível de aprovação comercial', select=True),
    }

res_users()
