# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)




class res_users(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'
    _description = 'Users Fone'


    _columns = {
        'fone': fields.char(u'Fone', size=18),
        'mobile': fields.char(u'Celular', size=18),
        'signature': fields.text(u'Assinatura de email'),
        'porta': fields.char(u'Porta', size=6),
    }

    def onchange_fone_celular(self, cr, uid, ids, fone, mobile, context={}):
        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            return {'value': {'fone': fone}}

        if mobile is not None and mobile:
            if not valida_fone_internacional(mobile) and not valida_fone_celular(mobile):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            mobile = formata_fone(mobile)
            return {'value': {'mobile': mobile}}


res_users()
