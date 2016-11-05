# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *


##class Produto(orm.Model):
    ##_description = u'Produtos'
    ##_name = 'sped.produto'
    ##def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        ##retorno = {}
        ##txt = u''
        ##print("descricao")
        ##for registro in self.browse(cursor, user_id, ids):
            ##retorno[registro.id] = registro.product_id.name_template

        ##return retorno

    ##def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        ##texto = args[0][2]

        ##procura = [
            ##('product_id.name_template', 'ilike', texto),
            ##]

        ##return procura

    ##_columns = {
        ##'product_id': fields.many2one('product.product'),
        ##'descricao': fields.function(_descricao, string='Descrição', method=True, type='char', fnct_search=_procura_descricao),
        ##'tipo': fields.selection(TIPO_PRODUTO_SERVICO, u'Tipo'),
        ##'ncm_id': fields.many2one('sped.ncm', u'NCM'),
        ##'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária do ICMS'),
        ##'al_ipi_id': fields.many2one('sped.aliquotaipi', 'Alíquota do IPI'),
        ##'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', 'Alíquota do PIS-COFINS'),
        ##}

    ###_sql_constraints = [
        ###('product_id_unique', 'unique (product_id)',
        ###u'Só é permitido vincular a um product_product!'),
        ###]

    ##_defaults = {
        ##'tipo': TIPO_PRODUTO_SERVICO_MERCADORIA_PARA_REVENDA,
        ##}

    ##_rec_name = 'descricao'
    ###_order = 'descricao'

##Produto()


class product_product(orm.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Product'

    _columns = {
        #'produto_id': fields.one2many('sped.produto', 'product_id', u'SPED'),
        'tipo': fields.selection(TIPO_PRODUTO_SERVICO, u'Tipo'),
        'ncm_id': fields.many2one('sped.ncm', u'NCM'),
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família tributária do ICMS'),
        'al_ipi_id': fields.many2one('sped.aliquotaipi', u'Alíquota do IPI'),
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota do PIS-COFINS'),
        'servico_id': fields.many2one('sped.servico', u'Código do serviço'),
        'org_icms': fields.selection(ORIGEM_MERCADORIA, u'Origem da mercadoria', select=True),
        'cest_id': fields.many2one('sped.cest', u'CEST'),
        }

    _defaults = {
        #'org_icms': ORIGEM_MERCADORIA_NACIONAL,
    }

product_product()
