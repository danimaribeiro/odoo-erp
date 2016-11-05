# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields

class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if name:
            name = name.replace(' ', '%')

        res = super(product_product, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)

        return res

    def _custo_ultima_compra_asp(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #
        # O custo da última compra é contextual para o CNPJ da empresa
        # ativa do usuário no momento
        # O custo da última compra também pode vir de uma atualização de tabela
        # do fornecedor
        #
        user_obj = self.pool.get('res.users').browse(cr, 1, uid)
        company_obj = user_obj.company_id
        cnpj = company_obj.partner_id.cnpj_cpf
        cfops = str(CFOPS_COMPRA_CUSTO_VENDA).replace('[', '(').replace(']', ')').replace("u'", "'")


        #
        # Na ASP, o custo deve vir da última compra, independente da empresa que está
        # trabalhando
        #
        for product_id in ids:
            sql = '''
select
coalesce(di.vr_unitario_custo, 0), d.id, prod.currency_id, d.data_emissao_brasilia, d.modelo

from
sped_documentoitem di
join sped_documento d on d.id = di.documento_id
join res_company c on c.id = d.company_id
join res_partner p on p.id = c.partner_id
join res_partner pp on pp.id = d.partner_id
join sped_cfop cf on cf.id = di.cfop_id
join product_product prod on prod.id = di.produto_id

where
-- p.cnpj_cpf = '{cnpj}' and
d.modelo in ('01', '55', 'TF')
and d.data_emissao_brasilia <= current_date
and d.emissao = '1' and d.entrada_saida = '0'
and d.situacao in ('00', '01', '08')
and di.produto_id = {product_id}
and p.cnpj_cpf != pp.cnpj_cpf
and cf.codigo in {cfops}

order by
d.data_emissao_brasilia desc

limit 1;'''

            #sql = sql.format(product_id=product_id, cnpj=cnpj, cfops=cfops)
            sql = sql.format(product_id=product_id, cfops=cfops)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # O custo padrão, de toda forma, é o informado manualmente
            #
            res[product_id] = self.pool.get('product.product').read(cr, 1, product_id, 'standard_price')['standard_price']

            if len(dados):
                print('dados')
                print(dados)
                custo, doc_id, moeda_id, data_emissao, modelo = dados[0]
                custo = custo or 0

                if modelo != 'TF' and moeda_id and moeda_id != 6:
                    currency_pool = self.pool.get('res.currency')
                    custo = currency_pool.compute(cr, uid, moeda_id, 6, custo or 0, context={'date': data_emissao})

                res[product_id] = custo

        return res

    _columns = {
        'custo_ultima_compra_asp': fields.function(_custo_ultima_compra_asp, string=u'Custo da última compra/atualização de tabela', type='float'),
    }


product_product()
