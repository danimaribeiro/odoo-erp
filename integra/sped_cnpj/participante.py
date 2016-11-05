# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from openerp import SUPERUSER_ID
from osv import orm
from consulta_cnpj import cookie_receita


class Participante(orm.Model):
    _inherit = 'sped.participante'

    _columns = {}

    def action_consultar_cnpj(self, cursor, user_id, ids, context=None):
        participante = self.browse(cursor, user_id, ids, context)[0]

        dados = cookie_receita()
        dados['texto_captcha'] = ''

        if participante.cnpj_cpf:
            dados['cnpj'] = participante.cnpj_cpf.replace('.', '').replace('/', '').replace('-', '').strip()
        else:
            dados['cnpj'] = ''

        dados['partner_id'] = participante.partner_id.id
        dados['participante_id'] = participante.id
        dados['imagem'] = dados['imagem']

        consulta_cnpj_pool = self.pool.get('sped.consulta_cnpj')
        consulta_cnpj_id = consulta_cnpj_pool.create(cursor, user_id, dados)

        #act_window_pool = self.pool.get('ir.actions.act_window')
        #janela_consulta_cnpj = act_window_pool.for_xml_id(cursor, SUPERUSER_ID, 'sped_cnpj', 'janela_consulta_cnpj', context)['id']
        ##print(janela_consulta_cnpj)

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

Participante()
