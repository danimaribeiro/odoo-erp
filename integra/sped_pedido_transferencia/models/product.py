# -*- encoding: utf-8 -*-

from osv import osv, fields
import base64
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def _custo_ultima_compra(self, cr, uid, ids, nome_campo, args=None, context={}):
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

        for product_id in ids:
            sql = '''
select
coalesce(di.vr_unitario_custo, 0)

from
sped_documentoitem di
join sped_documento d on d.id = di.documento_id
join res_company c on c.id = d.company_id
join res_partner p on p.id = c.partner_id
join res_partner pp on pp.id = d.partner_id

where
p.cnpj_cpf = '{cnpj}'
and d.modelo in ('01', '55', 'TF')
and d.data_emissao_brasilia <= current_date
and d.emissao = '1' and d.entrada_saida = '0'
and d.situacao in ('00', '01', '08')
and di.produto_id = {product_id}
and p.cnpj_cpf != pp.cnpj_cpf

order by
d.data_emissao_brasilia desc

limit 1;'''

            sql = sql.format(product_id=product_id, cnpj=cnpj)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # O custo padrão, de toda forma, é o informado manualmente
            #
            res[product_id] = self.pool.get('product.product').read(cr, 1, product_id, 'standard_price')['standard_price']

            if len(dados):
                res[product_id] = D(dados[0][0])

        return res

    _columns = {
        'custo_ultima_compra': fields.function(_custo_ultima_compra, string=u'Custo da última compra/atualização de tabela', method=True, type='float'),
    }


product_product()
