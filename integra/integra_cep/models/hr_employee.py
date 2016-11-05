# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm
from consulta_cep import consulta_cep


class hr_employee(orm.Model):
    _inherit = 'hr.employee'
    _name = 'hr.employee'

    def consulta_cep(self, cr, uid, ids, context=None):
        pool_municipio = self.pool.get('sped.municipio')

        for employee_obj in self.browse(cr, uid, ids):
            if not employee_obj.cep:
                continue

            dados = consulta_cep(employee_obj.cep, cr, uid, pool_municipio)

            dados_a_gravar = {}
            for chave in dados:
                if dados[chave] and unicode(dados[chave]).strip():
                    dados_a_gravar[chave] = dados[chave]

            print(dados)
            print(dados_a_gravar)

            return self.write(cr, uid, ids, dados_a_gravar, context=context)


hr_employee()

