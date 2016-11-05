# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
import random
from pybrasil.inscricao import limpa_formatacao


RANDOM_PASS_CHARACTERS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def generate_random_pass():
    return ''.join(random.sample(RANDOM_PASS_CHARACTERS,10))


class res_users(osv.Model):
    _inherit = 'res.users'
    
    def _pega_senha(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        
        for usuario_obj in self.browse(cr, 1, ids):
            res[usuario_obj.id] = usuario_obj.password
            
        return res
    
    _columns = {
        'cpf': fields.char(u'CPF', size=14, select=True),
        'senha': fields.function(_pega_senha, type='char', string=u'Senha'),
    }

    def cria_usuario_compartilhamento_holerite(self, cr, uid, holerite_obj):
        usuario_pool = self.pool.get('res.users')
        grupo_pool = self.pool.get('res.groups')
        action_pool = self.pool.get('ir.actions.actions')
        model_pool = self.pool.get('ir.model')

        model_ids = model_pool.search(cr, 1, [('model', '=', 'hr.payslip.portal')])

        if not len(model_ids):
            return

        model_id = model_ids[0]

        cpf = limpa_formatacao(holerite_obj.contract_id.employee_id.cpf)
        nome = holerite_obj.contract_id.employee_id.nome.strip().upper()
        company_id = holerite_obj.contract_id.company_id.id

        usuario_ids = usuario_pool.search(cr, 1, [('login', '=', cpf)])
        grupo_ids = grupo_pool.search(cr, 1, [('name', '=', u'RH - Portal do funcionário')])

        if not usuario_ids:
            action_id = action_pool.search(cr, 1, [('name', '=', u'Meus holerites')])
            dados = {
                'name': nome,
                'login': cpf,
                'cpf': holerite_obj.contract_id.employee_id.cpf,
                'company_id': company_id,
                'company_ids': [[6, False, [company_id]]],
                'password': generate_random_pass(),
                'groups_id': [[6, False, grupo_ids]],
                'action_id': action_id[0] if action_id else False
            }
            usuario_id = usuario_pool.create(cr, 1, dados)


res_users()
