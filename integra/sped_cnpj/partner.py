# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.inscricao import limpa_formatacao
from openerp import SUPERUSER_ID
from consulta_cnpj import cookie_receita


class res_partner(orm.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    _columns = {
        'cnae_ids': fields.many2many('sped.cnae', 'res_partner_cnae', 'partner_id', 'cnae_id', 'CNAEs adicionais'),
    }

    def action_consultar_cnpj(self, cursor, user_id, ids, context=None):
        partner_obj = self.browse(cursor, user_id, ids, context)[0]

        dados = cookie_receita()
        dados['texto_captcha'] = ''

        if partner_obj.cnpj_cpf:
            dados['cnpj'] = limpa_formatacao(partner_obj.cnpj_cpf)
        else:
            dados['cnpj'] = ''

        dados['partner_id'] = partner_obj.id
        dados['imagem'] = dados['imagem']

        consulta_cnpj_pool = self.pool.get('sped.consulta_cnpj')
        consulta_cnpj_id = consulta_cnpj_pool.create(cursor, user_id, dados)

        return {
            'name': 'Consulta CNPJ na Receita Federal',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'sped.consulta_cnpj',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': consulta_cnpj_id or False,
        }

res_partner()
