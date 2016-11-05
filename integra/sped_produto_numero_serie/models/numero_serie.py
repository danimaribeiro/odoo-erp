# -*- encoding: utf-8 -*-


from datetime import datetime
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from openerp import SUPERUSER_ID


class product_numero_serie(osv.Model):
    _name = 'product.numero.serie'
    _description = u'Número de série do produto'
    _rec_name = 'numero_serie'
    _order = 'product_id, numero_serie'

    _columns = {
        'product_id': fields.many2one('product.product', u'Produto', ondelete='cascade'),
        'numero_serie': fields.char(u'Número de série', size=64, select=True),
        'sped_documento_garantia_id': fields.many2one('sped.documento', u'NF início garantia'),
        'data_inicial_garantia': fields.date(u'Data início garantia'),
        'data_final_garantia': fields.date(u'Data final garantia'),
        'partner_id': fields.related('sped_documento_garantia_id', 'partner_id', type='many2one', relation='res.partner', string='Cliente', store=True, select=True),
        'stock_move_ids': fields.many2many('stock.move', 'stock_move_numero_serie', 'numero_serie_id', 'move_id', u'Movimentação de estoque'),
        'sped_documentoitem_ids': fields.many2many('sped.documentoitem', 'sped_documentoitem_numero_serie', 'numero_serie_id', 'item_id', u'Itens de notas fiscais'),
    }

    _sql_constraints = [
        ('product_numero_serie_unique', 'unique (product_id, numero_serie)', u'O número de série não pode se repetir para esse produto!'),
    ]

    def create(self, cr, uid, dados, context={}):
        res = super(product_numero_serie, self).create(cr, uid, dados, context=context)

        self.gera_varios(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(product_numero_serie, self).write(cr, uid, ids, dados, context=context)

        self.gera_varios(cr, uid, ids)

        return res

    def gera_varios(self, cr, uid, ids):
        ns_pool = self.pool.get('product.numero.serie')

        for ns_obj in self.browse(cr, uid, ids):
            if '..' in ns_obj.numero_serie:
                comeco, fim = ns_obj.numero_serie.split('..')
                comeco = int(comeco) + 1
                fim = int(fim) + 1
                tamanho = len(str(fim))

                dados = {
                    'product_id': ns_obj.product_id.id,
                    'stock_move_ids': [],
                    'sped_documentoitem_ids': [],
                }

                for stock_move in ns_obj.stock_move_ids:
                    dados['stock_move_ids'].append([0, False, stock_move.id])

                for nf_item in ns_obj.sped_documentoitem_ids:
                    dados['sped_documentoitem_ids'].append([0, False, nf_item.id])

                for i in range(comeco, fim):
                    dados['numero_serie'] = str(i).zfill(tamanho)
                    novo_id = ns_pool.create(cr, uid, dados)

                sql = "update product_numero_serie set numero_serie = '{ns}' where id = {id};"
                sql = sql.format(ns=str(comeco-1).zfill(tamanho), id=ns_obj.id)
                cr.execute(sql)


product_numero_serie()
