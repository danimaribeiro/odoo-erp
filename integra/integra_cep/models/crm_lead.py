# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm
from consulta_cep import consulta_cep


class crm_lead(orm.Model):
    _description = "Lead/Opportunity"
    _name = "crm.lead"
    _inherit = "crm.lead"

    def consulta_cep(self, cr, uid, ids, context=None):
        enderecos = self.browse(cr, uid, ids)
        pool_municipio = self.pool.get('sped.municipio')

        for endereco in enderecos:
            dados = consulta_cep(endereco.cep, cr, uid, pool_municipio)
            return self.write(cr, uid, ids, dados, context=context)


crm_lead()
