# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm
from consulta_cep import consulta_cep


class const_imovel(orm.Model):    
    _inherit = 'const.imovel'

    def consulta_cep(self, cr, uid, ids, context=None):
        pool_municipio = self.pool.get('sped.municipio')

        for imovel_obj in self.browse(cr, uid, ids):
            if not imovel_obj.cep:
                continue

            dados = consulta_cep(imovel_obj.cep, cr, uid, pool_municipio)

            dados_a_gravar = {}
            for chave in dados:
                if dados[chave] and unicode(dados[chave]).strip():
                    dados_a_gravar[chave] = dados[chave]
                    
            print(dados)
            print(dados_a_gravar)

            return self.write(cr, uid, ids, dados_a_gravar, context=context)


const_imovel()

