# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
import random


class res_groups(osv.Model):
    _inherit = 'res.groups'

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Fornecedor', select=True, ondelete='restrict'),
        'model_id': fields.many2one('ir.model', u'Tabela', select=True, ondelete='restrict'),
    }

    def cria_grupo_compartilhamento(self, cr, uid, partner_id, tabela='product.supplierinfo'):
        grupo_pool = self.pool.get('res.groups')
        model_pool = self.pool.get('ir.model')
        partner_pool = self.pool.get('res.partner')
        menu_pool = self.pool.get('ir.model.data')
        modelaccess_pool = self.pool.get('ir.model.access')
        regra_pool = self.pool.get('ir.rule')

        model_ids = model_pool.search(cr, 1, [('model', '=', tabela)])

        if not len(model_ids):
            return

        model_id = model_ids[0]

        grupo_ids = grupo_pool.search(cr, 1, [('model_id', '=', model_id), ('partner_id', '=', partner_id)])

        if len(grupo_ids):
            return grupo_ids[0]

        partner_obj = partner_pool.browse(cr, 1, partner_id)

        dados = {
            'name': u'Compartihamento de cotações - ' + partner_obj.name,
            'partner_id': partner_id,
            'model_id': model_id,
        }
        grupo_id = grupo_pool.create(cr, 1, dados)

        dados = {
            'model_id': model_id,
            'name': tabela,
            'perm_read': True,
            'perm_write': True,
            'group_id': grupo_id,
        }
        modelaccess_pool.create(cr, 1, dados)

        modelos_leitura = (
            'product.uom',
            'product.template',
            'product.product',
            'res.company',
            'res.partner',
            'purchase.cotacao'
        )
        for modelo in modelos_leitura:
            modelo_id = model_pool.search(cr, 1, [('model', '=', modelo)])

            dados = {
                'model_id': modelo_id[0],
                'name': modelo,
                'perm_read': True,
                'group_id': grupo_id,
            }
            modelaccess_pool.create(cr, 1, dados)

        menus = (
            ('base', 'menu_purchase_root'),
            ('construtora', 'menu_purchase_cotacao'),
            ('construtora', 'menu_cotacao_supplier_info'),
        )
        menus_permitidos_ids = []
        for modulo, menu in menus:
            menu_ids = menu_pool.search(cr, 1, [('model', '=', 'ir.ui.menu'), ('module', '=', modulo), ('name', '=', menu)])
            menu_obj = menu_pool.browse(cr, 1, menu_ids[0])
            menu_id = menu_obj.res_id
            menus_permitidos_ids.append(menu_id)

        grupo_pool.write(cr, uid, grupo_id, {'menu_access': [[6, False, menus_permitidos_ids]]})

        regra_id = regra_pool.cria_regra_compartilhamento(cr, uid, partner_id, model_id)

        grupo_pool.write(cr, uid, grupo_id, {'rule_groups': [[6, False, [regra_id]]]})

        return grupo_id


res_groups()


class ir_rule(osv.Model):
    _inherit = 'ir.rule'

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Fornecedor', select=True, ondelete='restrict'),
    }

    def cria_regra_compartilhamento(self, cr, uid, partner_id, model_id):
        regra_pool = self.pool.get('ir.rule')
        partner_pool = self.pool.get('res.partner')

        regra_ids = regra_pool.search(cr, 1, [('model_id', '=', model_id), ('partner_id', '=', partner_id)])

        if len(regra_ids):
            return regra_ids[0]

        partner_obj = partner_pool.browse(cr, 1, partner_id)

        dados = {
            'name': u'Compartihamento de cotações - ' + partner_obj.name,
            'perm_read': True,
            'perm_create': True,
            'perm_write': True,
            'perm_unlink': True,
            'domain_force': "[('name', '=', %d)]" % partner_id,
            'partner_id': partner_id,
            'model_id': model_id,
        }

        regra_id = regra_pool.create(cr, 1, dados)

        return regra_id


ir_rule()


RANDOM_PASS_CHARACTERS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def generate_random_pass():
    return ''.join(random.sample(RANDOM_PASS_CHARACTERS,10))


class res_users(osv.Model):
    _inherit = 'res.users'

    def cria_usuario_compartilhamento(self, cr, uid, email, grupo_id):
        usuario_pool = self.pool.get('res.users')
        grupo_pool = self.pool.get('res.groups')
        action_pool = self.pool.get('ir.actions.actions')

        email = email.strip().lower()

        usuario_ids = usuario_pool.search(cr, 1, [('login', '=', email)])

        if usuario_ids:
            usuario_id = usuario_ids[0]
            grupo_pool.write(cr, 1, [grupo_id], {'users': [[4, usuario_id]]})

        else:
            action_id = action_pool.search(cr, 1, [('name', '=', u'Cotação - fornecedores')])
            dados = {
                'name': email.strip().lower(),
                'login': email.strip().lower(),
                'company_ids': [[6, False, self.pool.get('res.company').search(cr, 1, [])]],
                'password': generate_random_pass(),
                'groups_id': [[6, False, [grupo_id]]],
                'action_id': action_id[0] if action_id else False
            }
            usuario_id = usuario_pool.create(cr, 1, dados)
            usuario_id = usuario_id

        return usuario_id


res_users()
