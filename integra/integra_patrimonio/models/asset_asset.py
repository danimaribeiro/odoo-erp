# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import hoje


class asset_asset(osv.Model):
    _name = 'account.asset.asset'
    _inherit = 'account.asset.asset'
    _rec_name = 'descricao'

    def _get_descricao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for p_obj in self.browse(cr, uid, ids):
            t = u''

            if p_obj.code:
                t = u'[' + p_obj.code + u'] '

            t += p_obj.name or u''

            res[p_obj.id] = t

        return res

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|', ('name', 'ilike', texto),
            ('code', 'ilike', texto),
        ]

        return procura

    _columns = {
        'name': fields.char(u'Descrição', size=120, select=True),
        'code': fields.char(u'Plaqueta', size=32, readonly=True, states={'draft':[('readonly',False)]}),
        'descricao': fields.function(_get_descricao, method=True, type='char', size=120, string=u'Patrimônio', store=True, select=True, fnct_search=_procura_descricao),
        'product_id': fields.many2one('product.product', u'Produto'),
        'sped_documentoitem_ids': fields.many2many('sped.documentoitem', 'sped_documentoitem_patrimonio', 'asset_id', 'sped_documentoitem_id', u'Itens das Notas'),
        #'sped_documentoitem_saida_id': fields.one2many('sped.documentoitem', 'asset_id', u'Item da NF-e de venda'),
        'currency_id': fields.many2one('res.currency','Currency',required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'valor_mercado': fields.float(u'Valor de mercado'),
        'data_mercado': fields.date(u'Data do valor de mercado'),
        'cnpj_cpf': fields.char(u'CNPJ do fornecedor (importado)', size=18, readonly=True),
        'numero_nf_compra': fields.integer(u'NF compra (importado)', readonly=True),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro Custo', ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'data_baixa': fields.date(u'Data Baixa'),
        'nf_venda_id': fields.many2one('sped.documento', u'NF de Venda', ondelete='restrict'),
    }

    _defaults = {
        #'currency_id': lambda self, cr, uid, context: self.pool.get('res.currency').search(cr, 1, [('name', '=', 'BRL')])[0]
        'currency_id': 6,
    }

    def onchange_product_id(self, cr, uid, product_id, name, context={}):
        res = {}

        if (not product_id) or name:
            return res

        valores = {}
        res['value'] = valores

        produto_obj = self.pool.get('product.product').browe(cr, uid, product_id)
        valores['name'] = produto_obj.name

        return res

    def onchange_valor_mercado(self, cr, uid, ids, valor_mercado, context={}):
        if not valor_mercado:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        valores['data_mercado'] = str(hoje())

        return res

    def calcula_todos(self, cr, uid, ids, context={}):
        asset_pool = self.pool.get('account.asset.asset')

        asset_ids = asset_pool.search(cr, uid, [('state', '=', 'open')])

        for asset_obj in asset_pool.browse(cr, uid, asset_ids):
            asset_obj.compute_depreciation_board()

        return True


asset_asset()
