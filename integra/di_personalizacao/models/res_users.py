# -*- coding: utf-8 -*-

from osv import fields, osv
from pybrasil.valor.decimal import Decimal as D


class res_users(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    _columns = {
        'imagem_assinatura': fields.binary(u'Assinatura de propostas'),
        'imagem_assinatura_text': fields.text(u'Assinatura de propostas'),
    }

    def write(self, cr, uid, ids, dados, context={}):
        if 'imagem_assinatura' in dados:
            dados['imagem_assinatura_text'] = dados['imagem_assinatura']

        return super(res_users, self).write(cr, uid, ids, dados, context=context)


res_users()
