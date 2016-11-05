# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm
from consulta_cep import consulta_cep


class res_partner(orm.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'

    def consulta_cep(self, cr, uid, ids, context=None):
        pool_municipio = self.pool.get('sped.municipio')

        for partner_obj in self.browse(cr, uid, ids):
            dados = consulta_cep(partner_obj.cep, cr, uid, pool_municipio)
            return self.write(cr, uid, ids, dados, context=context)


res_partner()


class res_partner_address(orm.Model):
    _description = 'Partner Addresses'
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    def consulta_cep(self, cr, uid, ids, context=None):
        enderecos = self.browse(cr, uid, ids)
        pool_municipio = self.pool.get('sped.municipio')

        for endereco in enderecos:
            dados = consulta_cep(endereco.cep, cr, uid, pool_municipio)
            return self.write(cr, uid, ids, dados, context=context)


res_partner_address()
