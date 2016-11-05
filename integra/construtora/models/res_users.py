# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_users(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    def _partner_corretor_id(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for user_obj in self.browse(cr, uid, ids):
            res[user_obj.id] = False

            sql = """
            select
                p.id
            from
                res_partner p
            where
                p.corretor_usuario_id = {user_id}
            limit 1;
            """
            sql = sql.format(user_id=user_obj.id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                res[user_obj.id] = dados[0][0]

        return res

    _columns = {
        'partner_corretor_id': fields.function(_partner_corretor_id, type='many2one', relation='res.partner', string=u'Corretor'),
        'imovel_ids': fields.many2many('const.imovel', 'res_user_imovel', 'user_id', 'imovel_id', u'Imóveis selecionados'),
        #'context_department_id': fields.many2one('hr.department', 'Departments'),
    }


res_users()


#class ir_action_window(osv.osv):
    #_name = 'ir.actions.act_window'
    #_inherit = 'ir.actions.act_window'

    #def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        #if context is None:
            #context = {}

        #select = ids

        #if isinstance(ids, (int, long)):
            #select = [ids]

        #res = super(ir_action_window, self).read(cr, uid, select, fields=fields, context=context, load=load)

        #for r in res:
            #if "'minha_selecao_imovel_ids()'" in (r.get('domain', '') or ''):
                #imovel_ids = []

                #for imovel_obj in self.pool.get('res.users').browse(cr, uid, uid).context_imovel_ids:
                    #imovel_ids.append(imovel_obj.id)

                #r['domain'] = r['domain'].replace("'minha_selecao_imovel_ids()'", str(imovel_ids))

        #if isinstance(ids, (int, long)):
            #if res:
                #return res[0]
            #else:
                #return False

        #return res


#ir_action_window()
